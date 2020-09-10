#!/usr/bin/python
# -*- coding: utf-8 -*-
from os import environ
from re import search


def get_msg_parts(line):
    """Parse message from Twitch into usable object"""
    if 'PRIVMSG' in line:
        try:
            message_data = dict()
            message_data['display_name'] = search('display-name=(.*?);', line).group(1)
            message_data['user'] = message_data['display_name'].lower()
            message_data['is_subscribed'] = True if search('subscriber=(.*?);', line).group(1) == '1' else False
            message_data['is_mod'] = True if search('mod=(.*?);', line).group(1) == '1' or 'broadcaster' in line else False
            message_data['yt_redeem'] = True if 'custom-reward-id=5dde5a13-4bec-4faf-ac80-da8e7ec8dc5e' in line else False
            message_data['message'] = search(f"PRIVMSG #{environ['TWITCH_CHANNEL']} :(.*)", line).group(1).replace('\r', '')
            return message_data
        except ValueError as e:
            print(e)
    else:
        return {'user': '', 'message': line, 'yt_redeem': False, 'is_mod': False, 'is_subscribed': False, 'display_name': ''}


def get_clip_id(msg):
    """Extract post code from line, and return proper link"""
    m = search(r'.*(clip|tv)/(\w*)', msg)
    if m:
        return f'https://clips.twitch.tv/{m.group(2)}'
    else:
        return '<delete me>'


def log_message(line):
    """Log messages to Console"""
    if not line.startswith('{}: /color'.format(environ["BOT_NAME"])):
        print(line)
