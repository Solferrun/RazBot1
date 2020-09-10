#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
import re
import socket
from urllib import request


class Stream:
    def __init__(self, data):
        self.channel_id = re.match(r'.*"_id":(\d*),.*', data[0]).group(1)
        self.stream_game = re.match(r'.*"game":"([^"]*)",.*', data[0]).group(1)
        try:
            self.stream_title = re.match(r'.*"status":"(.*),"broadcaster_language".*', data[1].replace(r'\\', '')).group(1)
        except AttributeError:
            self.stream_title = "[FAILED TO PARSE TITLE]"
        self.stream_viewers = int(re.match(r'.*"viewers":(\d*),.*', data[0]).group(1))
        self.stream_resolution = re.match(r'.*"video_height":(\d*),.*', data[0]).group(1)
        self.stream_fps = re.match(r'.*"average_fps":(\d*),.*', data[0]).group(1)
        self.stream_url = re.match(r'.*"url":"([^"]*)",.*', data[1]).group(1)
        self.streamer_display_name = re.match(r'.*"display_name":"([^"]*)",.*', data[1]).group(1)
        self.streamer_name = re.match(r'.*"name":"([^"]*)",.*', data[1]).group(1)
        self.streamer_language = re.match(r'.*"broadcaster_language":"([^"]*)",.*', data[1]).group(1)
        self.streamer_id = re.match(r'.*"_id":(\d*),.*', data[1]).group(1)
        self.streamer_partnered = re.match(r'.*"partner":([^"]*),.*', data[1]).group(1)
        self.streamer_views = re.match(r'.*"views":(\d*),.*', data[1]).group(1)
        self.streamer_followers = re.match(r'.*"followers":(\d*),.*', data[1]).group(1)

        self.info = f'[@{self.streamer_display_name}] streaming {self.stream_game} for {self.stream_viewers} viewers, {self.stream_resolution}p @ {self.stream_fps}fps || {self.stream_title}'.encode("utf-8").decode("unicode_escape")


def clean_stream_list(sl):
    raw = sl.replace("b'{\"streams\":[", '')
    raw = raw.replace("]}'", '')
    raw_stream_data = map(lambda s: s.split('},'), raw.split('}},'))
    streams = {}
    for rsd in raw_stream_data:
        try:
            temp_s = Stream(rsd)
            streams[temp_s.streamer_name] = temp_s
        except AttributeError:
            print(f">> Failed to parse stream: {rsd}")
            continue
    return streams


def get_stream_list(query):
    url = f"https://api.twitch.tv/kraken/streams?{query}"
    r = request.Request(url)
    r.add_header("Accept", "application/vnd.twitchtv.v5+json")
    r.add_header("Client-ID", os.environ["TWITCH_CLIENT_ID"])
    r.add_header("Authorization", "OAuth " + os.environ["TWITCH_TOKEN"])
    raw_stream_list = request.urlopen(r).read().decode('utf-8')
    if raw_stream_list:
        streams = clean_stream_list(raw_stream_list)
        if streams:
            return streams


def get_metadata(channel_name):
    url = f"https://api.twitch.tv/helix/streams/metadata?user_login={channel_name}"
    r = request.Request(url)
    r.add_header("Accept", "application/vnd.twitchtv.v5+json")
    r.add_header("Client-ID", os.environ["TWITCH_CLIENT_ID"])
    r.add_header("Authorization", "OAuth " + os.environ["TWITCH_TOKEN"])
    raw_stream_list = request.urlopen(r).read().decode('utf-8')
    print(raw_stream_list)


def open_twitch_socket():
    s = socket.socket()

    s.connect(("irc.chat.twitch.tv", 6667))
    s.send("PASS {0}\r\n".format("oauth:" + os.environ["TWITCH_TOKEN"]).encode('UTF-8'))
    s.send('CAP LS 1\r\n'.encode('UTF-8'))
    s.send('CAP REQ :twitch.tv/tags twitch.tv/commands\r\n'.encode('UTF-8'))
    s.send('CAP END\r\n'.encode('UTF-8'))
    s.send("NICK {0}\r\n".format(os.environ["BOT_NAME"]).encode('UTF-8'))
    s.send("JOIN #{0}\r\n".format(os.environ["TWITCH_CHANNEL"]).encode('UTF-8'))
    s.setblocking(False)

    return s


current_socket = open_twitch_socket()


def send_message(message):
    message_temp = "PRIVMSG #{0} :{1}".format(os.environ["TWITCH_CHANNEL"], message)
    current_socket.send(bytes(message_temp + "\r\n", 'UTF-8'))


def send_whisper(user, message):
    message_temp = "PRIVMSG #{0} :.w {1} {2}.".format(os.environ["TWITCH_CHANNEL"], user, message)
    current_socket.send(bytes(message_temp + "\r\n", 'UTF-8'))


def ban_user(user):
    message_temp = "PRIVMSG #{0} :.ban {1}".format(os.environ["TWITCH_CHANNEL"], user)
    current_socket.send(bytes(message_temp + "\r\n", 'UTF-8'))


def timeout_user(user):
    message_temp = "PRIVMSG #{0} :.timeout {1}".format(os.environ["TWITCH_CHANNEL"], user)
    current_socket.send(bytes(message_temp + "\r\n", 'UTF-8'))


def purge_user(user):
    message_temp = "PRIVMSG #{0} :.timeout {1} 1".format(os.environ["TWITCH_CHANNEL"], user)
    current_socket.send(bytes(message_temp + "\r\n", 'UTF-8'))
