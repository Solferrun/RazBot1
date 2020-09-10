#!/usr/bin/python
# -*- coding: utf-8 -*-
from urllib.error import HTTPError, URLError
from urllib.request import urlopen, Request
from urllib.parse import urlencode
from unicodedata import normalize
from random import choice
from os import environ
import contextlib
import urlfetch
import re

simple_commands = {
    'command': f"Command list: {environ['COMMANDS_URL']}",
    'commands': f"Command list: {environ['COMMANDS_URL']}",
    'help': f"Command list: {environ['COMMANDS_URL']}",
    'stats': f"https://stats.streamelements.com/c/{environ['STREAMER_NAME']}"
    }


def get_pets_data(url, limit=30):
    """Parse post data from url"""
    attempts = 0
    while attempts < limit:
        try:
            print('getpets')
            hdr = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.3',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
                'Accept-Encoding': 'none',
                'Accept-Language': 'en-US,en;q=0.8',
                'Connection': 'keep-alive'}
            request = Request(url=url, headers=hdr)
            response = urlopen(request).read()
            response_parsed = str(response.decode('utf-8'))
            print(response_parsed)
            post_shortcode = re.search('"shortcode":"(.*)","dimensions"', response_parsed, re.MULTILINE).group(1)
            print(post_shortcode)
            post_image = re.search('"display_url":"(.*)","display_resources"', response_parsed, re.MULTILINE).group(1).replace(r'\u0026', '&')
            print(post_image)
            post_timestamp = int(re.search(r'"taken_at_timestamp":(\d*),', response_parsed, re.MULTILINE).group(1))
            print(post_timestamp)
            post_description = re.search('"text":"(.*)"}}]},', response_parsed, re.MULTILINE).group(1).replace(r"\n", '\n')
            print(repr(post_description))
            return {'url': url,
                    'timestamp': post_timestamp,
                    'shortcode': post_shortcode,
                    'image_url': post_image,
                    'description': post_description}
        except (AttributeError, MemoryError, HTTPError, URLError) as e:
            attempts += 1
            print(f'Error: {e}')
            continue


def tiny_url(url):
    """Make url tiny"""
    request_url = ('http://tinyurl.com/api-create.php?' +
                   urlencode({'url': url}))
    with contextlib.closing(urlopen(request_url)) as response:
        return response.read().decode('utf-8')


fortune_responses = [
    'It is certain.', 'It is decidedly so.', 'Without a doubt.', 'Yes - definitely.', 'You may rely on it.',
    'As I see it, yes.', 'Most likely.', 'Outlook good.', 'Yes.', 'Signs point to yes.', 'Reply hazy, try again.',
    'Ask again later.', 'Better not to tell you now.', 'Cannot predict now.', 'Concentrate and ask again.',
    'Don\'t count on it.', 'My reply is no.', 'My sources say no.', 'Outlook not so good.', 'Very doubtful.']


# 8BALL
def get_fortune(args=None):
    """Get random fortune"""
    if args:
        return choice(fortune_responses)
    else:
        return "You gotta ask a question if you wanna get an answer! razWink"


# PICK
def get_pick(args):
    """Pick from string of options"""
    options = re.sub('(,)?( ,)? or ( ,)?', ', ', args)
    chosen = choice(options.split(','))
    if chosen:
        return 'I choose {}!'.format(chosen.strip())
    else:
        return 'I choose for you to stop trying to break me!'


# ICECREAM
def get_icecream(target):
    """Get random ice cream"""
    flavors = ["Chocolate", "Vanilla", "Strawberry", "Chocolate Chip", "Mint Chocolate Chip", "Caramel", "Coffee",
               "Butter Pecan", "Rocky Road", "Cherry Garcia", "Avocado", "Pistachio", "Taco-Flavored", "Flavorless"]
    containers = ["on a Cone", "in a Bowl", "on a Stick", "in a Bucket", "Over Rice"]
    return "{0} is handed a {1} Ice Cream {2}!".format(target, choice(flavors), choice(containers))


# MULTI
def get_multi(args):
    """Generate multi Twitch link"""
    return "http://multistre.am/{0}/{1}/layout3/".format(environ["TWITCH_CHANNEL"], '/'.join(args))


spell_choices = [
    "Starfire Charge", "Unholy Missiles", "Frost Frenzy", "Mirage", "Recharge", "Blessing of Darkness",
    "Orb of Pursuit", "Perversion Aura", "Assimilation Bolt", "Disruption of Sight", "Wind Tempest",
    "Electric Fury", "Sunlight Burn", "Wipe Out", "Lullaby", "Spell-shield of Revival", "Bolt of Clarity",
    "Duplicity Surge", "Interruption of Senses", "Entangling of Ancestors", "Mind Arrow", "Void Hail",
    "Static Typhoon", "Tranquility", "Bless", "Aura of Devouring", "Hex of the Void", "Sticks and Stones",
    "Disturbance of Shadows", "Decadence Hymn", "Demolition Spell-shield", "North Becomes South-West" 
    "Arms for Legs and Legs for Arms", "Unmaking by Ancestral Erasure", "Inside-Down, Upside-Out",
    "Reverse Amnesia, Where You Remember Things That Never Happened", "Wingardium Levi-OHHH-sa",
    "One-Year Aging", "Summon Centipodal Stalker"
]


def get_num_suffix(number):
    """Get appropriate suffix for number"""
    try:
        if int(number) in [11, 12, 13]:
            return 'th'
        n = str(number)[-1]
        if n == '1':
            return 'st'
        elif n == '2':
            return 'nd'
        elif n == '3':
            return 'rd'
        else:
            return 'th'
    except ValueError:
        print("!! non-number object passed to SimpleTools::get_num_suffix")
        return 'th'


# CAST
def get_spellname():
    """Get random spell name"""
    return choice(spell_choices)


# CASELESS EQUAL
def normalize_caseless(text):
    """Normalize characters for comparison"""
    return normalize("NFKD", text.casefold())


def caseless_equal(left, right):
    """Compare strings, ignore case difference"""
    return normalize_caseless(left) == normalize_caseless(right)


# API FETCH
def api_fetch(api, channel=environ['TWITCH_CHANNEL'], user=None):
    """Fetch certain Twitch API functions"""
    url = f"https://beta.decapi.me/twitch/{api}/{channel}/"
    if user:
        url += user
    #f"https://beta.decapi.me/twitch/{api}?channel={channel}&user={user}"
    response = urlfetch.get(url)
    content = response.content.decode('utf-8')
    return content


class MessageObject:
    """Organized message from Twitch"""
    def __init__(self, message, args, args_string, user, mentions, is_mod, is_subscribed, display_name):
        self.message = message
        self.args = args
        self.args_string = args_string
        self.user = user
        self.mentions = mentions
        self.is_mod = is_mod
        self.is_subscribed = is_subscribed
        self.display_name = display_name


curse_choices = [
    "your headphone cords snag on every door handle",
    "anything you buy goes on sale the next day",
    "all the chocolate chips in cookies you eat turn out to be raisins",
    "chairs always make a farting sound, except when you try to demonstrate that \'it was the chair!\'",
    "your phone always turns out to have been slightly unplugged from its charger cable overnight",
    "every open parking space you think you've spotted turns out to be occupied by a motorcycle",
    "every film you watch with your parents present is packed with sex scenes",
    "you can never follow through with an oncoming sneeze",
    "delivery guys always forget your drink",
    "you always wake up fifteen minutes before your alarm goes off",
    "you always burn your tongue on the first sip of a hot beverage",
    "your line at the grocery store always moves slower than the others",
    "every public toilet you use already has a massive dump in it",
    "people in front of you always walk slower than you, but just fast enough that you can't pass them casually",
    "toilet paper roll always turns out to have 2 sheets left",
    "all of your YouTube recommendations are random \"10 things you probably didn't know about...\" videos"
]


def curse(user, target):
    """Inflict random curse on target user"""
    return f"{user} casts the \"{choice(curse_choices)}\" curse on {target}!"