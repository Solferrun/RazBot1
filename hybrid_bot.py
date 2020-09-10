#!/usr/bin/python
# -*- coding: utf-8 -*-
import asyncio
from random import shuffle
from itertools import cycle
from traceback import format_exc
from urllib.error import HTTPError
from datetime import datetime as dt
from codecs import open as enc_open
from os import environ, path, remove, listdir
import requests

import discord
from discord.ext import commands
from youtube_dl.utils import DownloadError

import twitch_socket
import value_set
import roulette
from music import Music
from instagram import get_posts
from twitch_initialize import join_room
from gw2_tools import set_gw2_dyno_state
from s3_bucket import save_dict, load_dict
from ytdl import YTDLSource, DurationError
from twitch_read import get_msg_parts, get_clip_id
from simple_tools import MessageObject, api_fetch, simple_commands, get_num_suffix


def log_err(func):
    """Abort command and print log to console on error"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception:
            print(f"Error in {func.__name__}:\n{format_exc()}")
    return wrapper


class Bot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        load_dict('item_data')
        self.read_buffer = ""
        self.chat_color = cycle(["Blue", "BlueViolet", "CadetBlue", "Chocolate", "Coral", "DodgerBlue", "Firebrick", "GoldenRod", 
                                 "Green", "HotPink", "OrangeRed", "Red", "SeaGreen", "SpringGreen", "YellowGreen"])
        self.name = environ["BOT_NAME"]
        self.current_song = None
        self.default_voice_channel = int(environ.get('DISCORD_VOICE_CHANNEL'))
        custom_voice_channel = value_set.BOT_OPTIONS.get('discord_voice_channel')
        voice_channel = int(custom_voice_channel if custom_voice_channel else self.default_voice_channel)
        self.voice_channel = self.get_channel(voice_channel)
        self.last_promote = dt.now().strftime("%D:%H:%M")
        self.welcome_message = value_set.BOT_OPTIONS.get('welcome_message')
        self.splash_url_start = "https://i.imgur.com/rigtgGR.png"
        self.splash_url_over = "https://i.imgur.com/EFfWimV.png"

    @log_err
    async def disconnect_all_voice(self):
        """Disconnect from all voice channels"""
        if self.voice_clients:
            for v in self.voice_clients:
                await v.disconnect()
        self.dump_to_file('song.html', '')

    @log_err
    async def twitch_send(self, message):
        """Send message to Twitch chat"""
        twitch_socket.send_message(f"/me ~ {message}")
        print(f"{environ['BOT_NAME']}: {message}")

    # CHECK FOR RAZ PETS
    @log_err
    async def check_instagram(self, attempt_limit=30):
        """Check IG for new Raz pets"""
        posts = get_posts()
        if posts:
            for p in posts:
                if p['post_code'] not in value_set.RAZ_PETS:
                    await self.add_pets(p)

    @log_err
    async def add_pets(self, post):
        """Add Raz Pets entry to database and share to Discord"""
        post_url = f"https://www.instagram.com/p/{post['post_code']}"
        channel = self.get_channel(int(environ['DISCORD_PETS_CHANNEL']))
        embed = discord.Embed(title='**Raz pets!**',
                              description=post['caption'],
                              color=0x463aff)
        embed.set_image(url=post['media_url'])
        embed.add_field(name='Instagram', value=post_url)
        value_set.RAZ_PETS[post['post_code']] = post_url
        save_dict(value_set.RAZ_PETS, 'raz_pets')
        # embed.set_footer(text='')
        await channel.send(embed=embed)
        await self.twitch_send(f'Raz pets! {post_url}')

    @log_err
    async def promote_channel(self, now):
        """Promote the twitch channel"""
        if value_set.BOT_OPTIONS.get('stream_online'):
            current_minute = int(now.strftime("%M"))
            if current_minute == 0:
                load_dict('item_data')
                await self.twitch_send("Hey! Have Twitch Prime? It gives you a free Sub to use every month! Please "
                                       "consider using it here on MaericTV and help grow the channel! <3")
            elif current_minute == 30:
                await self.twitch_send(f"Come join our awesome community on Discord! "
                                       f"-> {environ['DISCORD_INVITE_URL']}")

    @log_err
    def stream_is_online(self):
        """Checks whether the stream is online"""
        uptime_report = api_fetch('uptime')
        return "minutes" in uptime_report or "seconds" in uptime_report

    # PERIODIC STUFF
    @log_err
    async def every_minute(self):
        """Events to perform every minute"""
        try:
            await self.check_instagram(attempt_limit=30)
            await self.check_voice()
        except Exception:
            print(f"!! HybridBot::every_minute: {format_exc()}")

        # Promote channel
        now = dt.now()
        current_datetime = now.strftime("%D:%H:%M")
        if current_datetime != self.last_promote:
            self.last_promote = now.strftime("%D:%H:%M")
            await self.promote_channel(now)

        # Ping twitch
        try:
            twitch_socket.current_socket.send("PING :tmi.twitch.tv\r\n".encode('UTF-8'))
        except BrokenPipeError:
            print(f"!! Twitch response failed: {format_exc()}\nReconnecting...")
            while not join_room(twitch_socket.current_socket):
                ">> Twitch room join failed. Retrying..."
            print("--Connected to Twitch--")

        # Check stream state
        is_online = self.stream_is_online()
        if is_online and not value_set.BOT_OPTIONS.get('stream_online'):
            print(">> Stream went online")
            set_gw2_dyno_state(set_active=True)
            await self.announce_stream_start()

        elif not is_online and value_set.BOT_OPTIONS.get('stream_online'):
            print(">> Stream went offline")
            set_gw2_dyno_state(set_active=False)
            await self.announce_stream_end()
        await asyncio.sleep(1)

    @log_err
    async def announce_stream_start(self):
        """Announce stream to Discord"""
        try:
            game_name = api_fetch('game')
            stream_title = api_fetch('title')
            embed = discord.Embed(title=f"**MaericTV just went live with {game_name}!**",
                                  url="https://www.twitch.tv/maerictv",
                                  description=stream_title,
                                  color=0x463aff)
            embed.add_field(name='Come join us!', value="https://www.twitch.tv/maerictv")
            embed.set_image(url=self.splash_url_start)
            stream_channel = self.get_channel(int(environ['DISCORD_STREAMING_CHANNEL']))
            stream_message = await stream_channel.send(content="@here", embed=embed)
            value_set.BOT_OPTIONS['stream_message'] = stream_message.id
        except Exception:
            print(f"!! hybrid_bot::announce_stream_start: {format_exc()}")
        finally:
            value_set.BOT_OPTIONS['stream_online'] = True
            save_dict(value_set.BOT_OPTIONS, 'bot_options')

    @log_err
    async def update_stream_message(self, stream_message, stream_title):
        stream_message_embed = stream_message.embeds[0]
        stream_message_embed.description = stream_title
        await stream_message.edit(embed=stream_message_embed)

    @log_err
    async def announce_stream_end(self):
        """Edit stream announcement in Discord"""
        try:
            game_name = api_fetch('game')
            stream_title = api_fetch('title')
            vod_url = api_fetch('vod_replay', channel='maerictv').split('?')[0]
            embed = discord.Embed(title=f"**MaericTV's {game_name} stream has ended!**",
                                  url=vod_url,
                                  description=stream_title,
                                  color=0x463aff)
            embed.add_field(name="But there's always the vod:", value=vod_url)
            embed.set_image(url=self.splash_url_over)
            stream_channel = self.get_channel(int(environ['DISCORD_STREAMING_CHANNEL']))
            messages = await stream_channel.history(limit=20).flatten()
            old_message = discord.utils.get(messages, id=value_set.BOT_OPTIONS.get('stream_message'))
            await old_message.edit(embed=embed)
        except Exception:
            print(f"!! hybrid_bot::announce_stream_end: {format_exc()}")
        finally:
            if value_set.BOT_OPTIONS['player_enabled']:
                # Stop player
                value_set.BOT_OPTIONS['discord_voice_channel'] = environ['DISCORD_VOICE_CHANNEL']
                value_set.BOT_OPTIONS['player_enabled'] = False
                await self.disconnect_all_voice()
                await self.dj_send("_Stream went offline. Player auto-disabled!_")
            value_set.BOT_OPTIONS['stream_message'] = None
            value_set.BOT_OPTIONS['stream_online'] = False
            save_dict(value_set.BOT_OPTIONS, 'bot_options')

    # MESSAGE HANDLING
    @log_err
    async def parse_messages(self):
        """Read and parse received Twitch messages"""
        try:
            recieved = twitch_socket.current_socket.recv(2056)
            if recieved:
                self.read_buffer = self.read_buffer + recieved.decode('UTF-8')
                temp = self.read_buffer.split("\n")
                self.read_buffer = temp.pop()

                # PARSE LINES
                for line in temp:
                    message_parts = get_msg_parts(line)
                    message = message_parts['message']
                    user = message_parts['user']
                    is_mod = message_parts['is_mod']
                    is_subscribed = message_parts['is_subscribed']
                    display_name = message_parts['display_name']

                    # PING/LOG
                    if "PING :tmi.twitch.tv" in line:
                        twitch_socket.current_socket.send("PONG :tmi.twitch.tv\r\n".encode("utf-8"))
                        break
                    elif "PONG tmi.twitch.tv" not in line and user:
                        print(f"{display_name}: {message}")

                    # CLIP FORWARDING
                    if "clips.twitch.tv/" in line or "twitch.tv/maerictv/clip/" in line:
                        print(">> Forwarding clip to discord...")
                        clip_channel = self.get_channel(int(environ['DISCORD_CLIPS_CHANNEL']))
                        await clip_channel.send(f"**Clip shared to Twitch chat by {display_name}!**\n {get_clip_id(message)}")

                    # ROULETTE ENTER PHRASE HANDLING
                    if roulette.round_obj and message.strip() == roulette.round_obj.entry_phrase:
                        if display_name not in roulette.round_obj.users:
                            roulette.round_obj.add(display_name)
                            await self.twitch_send(f"{display_name} has entered the roulette!")

                    # SONG REQUEST HANDLING
                    elif message_parts['yt_redeem']:
                        print(f">> YT redeem detected: {message}")
                        req_info = await YTDLSource.get_info(message)
                        try:
                            if req_info:
                                if req_info['duration'] <= 600:
                                    value_set.MUSIC_QUEUE['request'].append(req_info['webpage_url'])
                                    save_dict(value_set.MUSIC_QUEUE, 'music_queue')
                                    req_count = len(value_set.MUSIC_QUEUE['request'])
                                    req_wait = f"{req_count}{get_num_suffix(req_count)}" if req_count > 1 else "next"
                                    await self.dj_send(f"[{req_count}] Yarn request from `{display_name}`: {req_info['webpage_url']}")
                                    await self.twitch_send(f"@{display_name} Your request is {req_wait} in the song queue! razCool")
                                else:
                                    await self.twitch_send(f"@{display_name} Your request was over 10 minutes, so I ate it! razHands")
                            else:
                                await self.twitch_send(f"Sorry, @{display_name}, your request yielded no results! razCool")
                        except DownloadError:
                            #self.reboot_app()
                            print(format_exc())
                            value_set.BOT_OPTIONS['player_enabled'] = False
                            await self.dj_send("_YouTube is denying requests! Disabling player. :(_")

                    # COMMAND HANDLING
                    elif message.startswith('!'):
                        msg_split = message.split(' ', 1)

                        # GET ARGUMENTS
                        args = None
                        args_string = None
                        if len(msg_split) > 1:
                            args_string = msg_split[1].strip()
                            args = [word for word in args_string.split() if not word.startswith('@') or word == '@']


                        # GET MENTIONS
                        mentions = []
                        if '@' in message:
                            mentions = [word[1:].replace(',', '') for word in message.split()
                                        if word.startswith('@') and word != '@']
                            if mentions:
                                print('Mentions: {0}'.format(mentions))

                        # GET TOKEN
                        token = None
                        if msg_split:
                            token = msg_split[0][1:].strip().lower()
                        if not token:
                            break

                        # EXECUTE COMMAND
                        response = None
                        if token in simple_commands:
                            response = simple_commands[token]
                        elif token in value_set.advanced_commands:
                            response = value_set.advanced_commands[token](
                                MessageObject(message, args, args_string, user, mentions, is_mod, is_subscribed,
                                              display_name))
                        elif token in value_set.custom_commands:
                            response = value_set.custom_commands[token].replace('{user}', display_name)

                        if response:
                            await self.twitch_send(response)
        except BlockingIOError:
            return
        return

    @log_err
    def get_voice(self):
        """Get first voice client"""
        return self.voice_clients[0] if self.voice_clients else None

    @log_err
    async def dj_send(self, message):
        """Send message to Discord DJ channel"""
        dj_channel = self.get_channel(int(environ['DISCORD_DJ_CHANNEL']))
        await dj_channel.send(message)

    @log_err
    async def check_voice(self):
        """Check voice state, disconnect from empty channels"""
        vc = self.get_voice()
        if vc and len(vc.channel.members) <= 1:
            await self.dj_send(f"*It's too lonely in here! Disconnecting from {self.voice_channel}.*")
            await vc.disconnect()
            value_set.BOT_OPTIONS['player_enabled'] = False
            value_set.BOT_OPTIONS['discord_voice_channel'] = environ['DISCORD_VOICE_CHANNEL']
            save_dict(value_set.BOT_OPTIONS, 'bot_options')
            await self.clear_files()

    @log_err
    async def background_tasks(self):
        """Run looping tasks"""
        await self.wait_until_ready()
        while not self.is_closed():
            try:
                if value_set.BOT_OPTIONS.get('player_enabled'):
                    if not self.get_voice():
                        await self.channel_connect()

                    if not (self.get_voice().is_playing() or self.get_voice().is_paused()):
                        # Play new song
                        await self.clear_files()
                        await self.play_next_song()
                else:
                    await self.disconnect_all_voice()

                await self.parse_messages()

                now = dt.now()
                # current_hour = int(now.strftime("%H"))
                # current_minute = int(now.strftime("%M"))
                current_second = int(now.strftime("%S"))
                if current_second == 0:
                    await self.every_minute()

            except discord.errors.ClientException as e:
                print(f"!! ClientException while attempting to play \"{self.current_song}\": {format_exc()}")

                if self.current_song in value_set.MUSIC_QUEUE['default']:
                    value_set.MUSIC_QUEUE['default'].append(value_set.MUSIC_QUEUE['default'].remove(self.current_song))
                elif self.current_song in value_set.MUSIC_QUEUE['request']:
                    value_set.MUSIC_QUEUE['request'].remove(self.current_song)

                if 'Already connected to a voice channel' in str(e):
                    await self.disconnect_all_voice()
            except ValueError:
                print(format_exc())
                self.dj_send("YouTube is currently refusing my HTTP requests! Player disabled for now.")
            except Exception:
                print(f"!! HybridBot::background_tasks: {format_exc()}")

            await asyncio.sleep(1)

    @log_err
    async def clear_files(self):
        """Clear downloaded audio files from root folder"""
        here = path.dirname(path.realpath(__file__))
        for file in [f for f in listdir(here) if f.endswith('.m4a') or f.endswith('.webm')]:
            try:
                remove(file)
            except PermissionError:
                continue

    async def channel_connect(self):
        """Connect to a voice channel"""
        voice_client = self.voice_clients[0] if self.voice_clients else None
        if voice_client:
            return await voice_client.move_to(self.voice_channel)

        custom_voice_channel = value_set.BOT_OPTIONS.get('discord_voice_channel')
        voice_channel = int(custom_voice_channel if custom_voice_channel else self.default_voice_channel)
        self.voice_channel = self.get_channel(voice_channel)
        await self.voice_channel.connect(timeout=3)
        print(f">> Voice connected to {self.voice_channel}")

    @log_err
    async def play_next_song(self):
        """Play song from playlist on VoiceClient"""
        try:
            msg = "**Playing"
            if value_set.MUSIC_QUEUE['request']:
                self.current_song = value_set.MUSIC_QUEUE['request'].pop(0)
                msg += " request"
            else:
                self.current_song = value_set.MUSIC_QUEUE['default'][0]
                value_set.MUSIC_QUEUE['default'].append(value_set.MUSIC_QUEUE['default'].pop(0))
            value_set.CURRENT_PLAYER = await YTDLSource.from_url(self.current_song, loop=self.loop)
            if not self.get_voice():
                await self.channel_connect()
            self.get_voice().play(value_set.CURRENT_PLAYER, after=lambda e: print(f"PlayError: {e}") if e else None)
            # self.get_voice().source.volume = 0.10
            save_dict(value_set.MUSIC_QUEUE, 'music_queue')
            await self.dj_send(f"{msg}:** `{value_set.CURRENT_PLAYER.title}`")
        except discord.errors.ClientException:
            print(f"!! HybridBot::play_next_song: {format_exc()}")
            self.get_voice().stop()
            await self.disconnect_all_voice()
            await self.channel_connect()
        except HTTPError:
            print(f"!! HybridBot::play_next_song: {format_exc()}")
            await self.twitch_send(f"YouTube is currently refusing my HTTP requests! Player disabled for now.")
            await self.dj_send("YouTube is currently refusing my HTTP requests! Player disabled for now.")
            value_set.BOT_OPTIONS['player_enabled'] = False
            save_dict(value_set.BOT_OPTIONS, 'bot_options')
            if self.get_voice():
                self.get_voice().stop()
                await self.disconnect_all_voice()
            await self.clear_files()
        except DurationError:
            print(f"!! HybridBot::play_next_song: {format_exc()}")
            await self.twitch_send(f"\"{self.current_song}\" was over 10 minutes long! So I skipped it. razBlank")
        except Exception:
            print(f"!! Error while playing {self.current_song} HybridBot::play_next_song: {format_exc()}")

    def dump_to_file(self, file_name, text):
        """Dump string to file"""
        here = path.dirname(path.realpath(__file__))
        template_path = here + f"/Templates/{file_name}"
        with enc_open(template_path, 'w', 'utf-8') as file:
            file.write(text)
            file.close()


bot = Bot(command_prefix=commands.when_mentioned_or("DJ "),
          description=f"{environ['STREAMER_NAME']}'s Music Bot")


@log_err
@bot.event
async def on_ready():
    await bot.disconnect_all_voice()
    value_set.MUSIC_QUEUE = load_dict('music_queue')
    print('--Connected to Discord--')
    twitch_socket.current_socket = twitch_socket.open_twitch_socket()
    while not join_room(twitch_socket.current_socket):
        continue
    print("--Connected to Twitch--")

    bot.background_task1 = bot.loop.create_task(bot.background_tasks())
    # bot.background_task2 = bot.loop.create_task(bot.update_gw2_character_data())


@log_err
@bot.event
async def on_disconnect():
    value_set.CURRENT_PLAYER = None
    await bot.disconnect_all_voice()
    await bot.clear_files()


@log_err
@bot.event
async def on_voice_state_update(member, before, after):
    """Report unintentional disconnects"""
    if member == bot.user and str(before.channel) != 'Streaming Now' and not after.channel:
        print(f">> Voice disconnected from {before.channel}")
        await bot.clear_files()
        await bot.disconnect_all_voice()

gif_list = ["https://media1.tenor.com/images/f71ccae28db3864915f76043bf547639/tenor.gif",
            "https://media1.tenor.com/images/4ece62cbde2383c165324005fc4e1d71/tenor.gif",
            "https://media.tenor.com/images/5602761e30bef913c4961b1b34d6fc17/tenor.gif",
            "https://media1.tenor.com/images/765f14717c4d5eab1bea8a2a299c1240/tenor.gif",
            "https://media1.tenor.com/images/d38871baf11459a3d09c7de110b1c541/tenor.gif",
            "https://media1.tenor.com/images/8a650dbffd5d35fcfa81816bcff1bbf9/tenor.gif",
            "https://media1.tenor.com/images/05b165e692cbf3aa21e6f9d4540a2642/tenor.gif",
            "https://media1.tenor.com/images/412839b4babb4a68f4f58f09e315623c/tenor.gif",
            "https://media1.tenor.com/images/6648e75609fc74c87c713e732fbff27d/tenor.gif",
            "https://media1.tenor.com/images/d1f26c4cc48446457e6d757093d8a680/tenor.gif",
            "https://media1.tenor.com/images/ed548295fd09888f370b3550d10009e5/tenor.gif",
            "https://media1.tenor.com/images/c15788506dda2372ef870cb25b8d4ad7/tenor.gif",
            "https://media1.tenor.com/images/50734893c5517adb8b683fe2f17889c4/tenor.gif",
            "https://media1.tenor.com/images/a709cc32d722b762156a2f5829a33dd3/tenor.gif",
            "https://media1.tenor.com/images/777f89d7196047ef3c3665382f1891f6/tenor.gif",
            "https://media1.tenor.com/images/1169d1ab96669e13062c1b23ce5b9b01/tenor.gif",
            "https://media1.tenor.com/images/ece3a04d7e19a6bdee41655fcddb2f2a/tenor.gif",
            "https://media1.tenor.com/images/4b61af267c84ebc16befebe8853744ac/tenor.gif",
            "https://media1.tenor.com/images/ad3c7510001752486d87d1e13e50354c/tenor.gif",
            "https://media1.tenor.com/images/3eeb85272c6e91e66cdfbaf7d3e5947e/tenor.gif",
            "https://media1.tenor.com/images/b11727bfdbcbddbf974f8d8bbc387a8a/tenor.gif",
            "https://media1.tenor.com/images/e1f829172edbcfcd9563a90a8ec67240/tenor.gif",
            "https://media1.tenor.com/images/861c48867905893b294ace460042ffe7/tenor.gif"]

shuffle(gif_list)
gif_cycle = cycle(gif_list)


@log_err
@bot.event
async def on_message(message):
    """
    On any Discord message visible to bot
    """
    if message.author != bot.user:
        try:
            user_roles = list(role.name for role in message.author.roles)
            is_mod = '~Moderator~' in user_roles
            is_bot = '~Bot~' in user_roles
            # Clear DJ Channel messages
            if message.channel.id == int(environ['DISCORD_DJ_CHANNEL']):
                await bot.process_commands(message)
                if message.author != bot.user:
                    await message.delete()
            elif is_mod:
                await bot.process_commands(message)

            # Restrict Live Stream channel while stream is live
            if message.channel.id == int(environ['DISCORD_STREAMING_CHANNEL']):
                if not (is_mod or is_bot or not value_set.BOT_OPTIONS['stream_online']):
                    print(f">> Blocked: {message.author.name}@{message.channel.name}: {message.content}")
                    await message.delete()
                    embed = discord.Embed(title='Sorry about that!',
                                          description='*General posting is disabled during live streams.*',
                                          color=0x463aff)
                    img_src = next(gif_cycle)
                    embed.set_image(url=img_src)
                    await message.channel.send(embed=embed)
        except AttributeError:
            print(f"{message.author.name}@{message.channel}: {message.content}")


@bot.event
async def on_member_join(member):
    """Welcome new members, and grant member role"""
    guild = member.guild
    member_role = discord.utils.get(guild.roles, name='~Member~')
    await member.add_roles(member_role)
    if guild.system_channel and bot.welcome_message:
        message = bot.welcome_message.replace('{user}', member.mention)
        await guild.system_channel.send(message)
    else:
        print("System channel or welcome message not found.")

bot.add_cog(Music(bot))
