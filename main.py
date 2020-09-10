#!/usr/bin/python
# -*- coding: utf-8 -*-
from os import environ

from hybrid_bot import bot
from twitch_commands import load_ctr_commands

if __name__ == "__main__":
    load_ctr_commands()
    bot.run(environ['DISCORD_TOKEN'])
