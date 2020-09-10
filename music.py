from os import environ
from random import shuffle

from discord.ext import commands

from s3_bucket import save_dict, load_dict
from simple_tools import tiny_url
from ytdl import YTDLSource
import value_set


class Music(commands.Cog):
    def __init__(self, bot_in):
        self.bot = bot_in

    @commands.command()
    async def play(self, ctx):
        """Have the bot come play in your voice channel (while stream is offline)"""
        if not value_set.BOT_OPTIONS.get('stream_online'):
            try:
                song_name = ctx.message.content.split('play', 1)[1].strip()
                if song_name:
                    ctx.message.content = 'sr ' + song_name
                    await self.sr(ctx)
                elif not value_set.BOT_OPTIONS.get('player_enabled'):
                    summon_success = await self.summon(ctx)
                    if summon_success:
                        value_set.BOT_OPTIONS['player_enabled'] = True
                        await ctx.send(f"**_Now playing in {self.bot.voice_channel}!_**")
                else:
                    await ctx.send(f"*Already playing in {self.bot.voice_channel}!*")
            except AttributeError as e:
                await ctx.send('*Please do that while connected to a voice channel!*')
        else:
            await ctx.send('*Stream is live! Music bot reserved.*')

    @commands.command()
    @commands.has_role("~Moderator~")
    async def summon(self, ctx):
        """Summon bot to your current voice channel"""
        try:
            channel_int = ctx.author.voice.channel.id
            value_set.BOT_OPTIONS['discord_voice_channel'] = channel_int
            save_dict(value_set.BOT_OPTIONS, 'bot_options')
            self.bot.voice_channel = self.bot.get_channel(channel_int)
            await self.bot.channel_connect()
            print(f">> Voice connected to {self.bot.voice_channel}")
            return True
        except AttributeError as e:
            await ctx.send('*Please do that while connected to a voice channel!*')
            return False

    @commands.command()
    @commands.has_role("~Moderator~")
    async def player(self, ctx, cmd=None):
        """Turn the player on/off, or get its status"""
        if cmd == 'off' or cmd == 'disable' and value_set.BOT_OPTIONS.get('player_enabled'):
            value_set.BOT_OPTIONS['player_enabled'] = False
            save_dict(value_set.BOT_OPTIONS, 'bot_options')
            await ctx.send("*Player disabled.*")
            await self.bot.clear_files()
            value_set.BOT_OPTIONS['discord_voice_channel'] = environ['DISCORD_VOICE_CHANNEL']

        elif cmd == 'on' or cmd == 'enable' and not value_set.BOT_OPTIONS.get('player_enabled'):
            value_set.BOT_OPTIONS['player_enabled'] = True
            save_dict(value_set.BOT_OPTIONS, 'bot_options')
            await ctx.send("*Player enabled.*")

        elif cmd == 'add':
            await self.add(ctx)

        elif cmd == 'remove':
            await self.remove(ctx)

        else:
            player_status = 'enabled' if value_set.BOT_OPTIONS.get('player_enabled') else 'disabled'
            response = f"*Player is {player_status}.* "
            if value_set.CURRENT_PLAYER:
                response += f"*The current/last played audio is:* `{value_set.CURRENT_PLAYER.title}`"
            await ctx.send(response)

    @commands.command()
    @commands.has_role("~Moderator~")
    async def pause(self, ctx):
        """Pause the discord player"""
        vc = self.bot.get_voice()
        if vc:
            paused = vc.is_paused()
            if paused:
                vc.resume()
            else:
                vc.pause()
            await ctx.send("Player {}.".format('unpaused' if paused else 'paused'))

    @commands.command()
    async def skip(self, ctx):
        """Tell the Discord player to skip the current song"""
        is_mod = '~Moderator~' in list(role.name for role in ctx.author.roles)
        if is_mod or not value_set.BOT_OPTIONS.get('stream_online'):
            if self.bot.get_voice():
                await ctx.send(f"*Song skipped by {ctx.author.name}!*")
                self.bot.get_voice().stop()
                value_set.MUSIC_QUEUE = load_dict('music_queue')

    @commands.command()
    @commands.has_role("~Moderator~")
    async def volume(self, ctx, value):
        """Adjust the Discord player's volume by %"""
        if self.bot.get_voice():
            if value.isdigit():
                target_volume = max(min(int(value), 100), 0)
                self.bot.get_voice().source.volume = target_volume / 100
                await ctx.send(f"Player volume set to {target_volume}%")
            else:
                current_volume = int(self.bot.get_voice().source.volume * 100)
                await ctx.send(f"Current volume: {current_volume}. Use !volume [0-100] to adjust it.")

    @commands.command()
    async def playlist(self, ctx):
        """Show the default playlist"""
        playlist = value_set.MUSIC_QUEUE['default'].copy()
        if playlist:
            line = f"{playlist.pop(0)}"
            while playlist:
                next_song = playlist.pop(0)
                if len(f"{line}\n{next_song}") > 2000:
                    await ctx.send(line)
                    line = f"{next_song}"
                else:
                    line += f"\n{next_song}"
            await ctx.send(line)
        else:
            await ctx.send("The playlist is empty!")

    @commands.command()
    @commands.has_role("~Moderator~")
    async def add(self, ctx):
        """Add song to default playlist"""
        song_name = ctx.message.content.split('add', 1)[1].strip()
        value_set.MUSIC_QUEUE['default'].append(song_name)
        save_dict(value_set.MUSIC_QUEUE, 'music_queue')
        await ctx.send(f"*Added {song_name} to the default playlist!*")

    @commands.command()
    @commands.has_role("~Moderator~")
    async def remove(self, ctx):
        """Remove song from default playlist"""
        song_name = ctx.message.content.split('remove', 1)[1].strip()
        if song_name:
            try:
                value_set.MUSIC_QUEUE['default'].remove(song_name)
                save_dict(value_set.MUSIC_QUEUE, 'music_queue')
                await ctx.send(f"*Removed \"{song_name}\" from the default playlist!*")
            except ValueError:
                await ctx.send(f"*\"{song_name}\" wasn't found in the default playlist! Use: \"!playlist\" "
                               f"to view the contents of the default playlist.*")
        else:
            if value_set.MUSIC_QUEUE['default']:
                target = value_set.MUSIC_QUEUE['default'][-1]
                output = f"*Removed \"{target}\" from the default playlist!*"
                value_set.MUSIC_QUEUE['default'].remove(target)
                save_dict(value_set.MUSIC_QUEUE, 'music_queue')
                return output
            else:
                await ctx.send("Nothing to remove!")

    @commands.command()
    @commands.has_role("~Moderator~")
    async def shuffle(self, ctx):
        """Shuffle songs in default playlist"""
        shuffle(value_set.MUSIC_QUEUE['default'])
        save_dict(value_set.MUSIC_QUEUE, 'music_queue')
        await ctx.send(f"*Default playlist shuffled!*")

    @commands.command()
    async def requests(self, ctx):
        """Show the request list"""
        request_list = value_set.MUSIC_QUEUE['request'].copy()
        if request_list:
            line = f"[1]: {request_list.pop(0)}"
            for idx, song in enumerate(request_list):
                next_song = request_list.pop(0)
                if len(f"{line}\n{idx+2}: {next_song}") > 2000:
                    await ctx.send(line)
                    line = f"[{idx+2}]: {next_song}"
                else:
                    line += f"\n[{idx+2}]: {next_song}"
            await ctx.send(line)
        else:
            await ctx.send("*The request list is empty!*")

    @commands.command()
    @commands.has_role("~Moderator~")
    async def sr(self, ctx):
        """Request a song for the Discord player, or get the request list"""
        song_name = ctx.message.content.split('sr', 1)[1].strip()
        if song_name:
            req_info = await YTDLSource.get_info(song_name)
            if req_info and req_info['duration'] <= 600:
                value_set.MUSIC_QUEUE['request'].append(song_name)
                save_dict(value_set.MUSIC_QUEUE, 'music_queue')
                req_count = len(value_set.MUSIC_QUEUE['request'])
                await ctx.send(f"*Added {ctx.message.author.name}'s request:*\n[{req_count}] {song_name}")
            else:
                await ctx.send(f"*Couldn't add that request! Either there were no results, or it was over 10 mins.*")
        else:
            await self.requests(ctx)

    @commands.command()
    @commands.has_role("~Moderator~")
    async def cancel(self, ctx, value):
        """Remove a song by index from the request queue"""
        if value.isdigit():
            idx = int(value) - 1
            if idx < len(value_set.MUSIC_QUEUE['request']):
                value_set.MUSIC_QUEUE['request'].pop(idx)
                save_dict(value_set.MUSIC_QUEUE, 'music_queue')
                await ctx.send(f"*Request removed from the queue.*")
            else:
                await ctx.send("*There's no song in the request queue with that index!*")
        elif value == 'all':
            value_set.MUSIC_QUEUE['request'] = []
            save_dict(value_set.MUSIC_QUEUE, 'music_queue')
            await ctx.send(f"*All requests removed from the queue.*")

    @commands.command()
    @commands.has_role("~Moderator~")
    async def announce(self, ctx):
        """Have RazBot relay a message to music channel"""
        announcement = ctx.message.content.split('announce', 1)[1].strip()
        await ctx.send(f"{announcement}")

    @commands.command()
    async def song(self, ctx):
        """Return the current song from the Discord player"""
        if value_set.CURRENT_PLAYER:
            await ctx.send(f'*Currently playing:* `{value_set.CURRENT_PLAYER.title}`')

    @commands.command()
    async def link(self, ctx):
        """Return a link to the audio file of the current song"""
        if value_set.CURRENT_PLAYER:
            await ctx.send(tiny_url(value_set.CURRENT_PLAYER.url))

    @commands.command()
    @commands.has_role("~Moderator~")
    async def channel(self, ctx, channel):
        """Move the bot to the provided voice channel"""
        try:
            if channel and channel.isdigit():
                channel_int = int(channel)
                value_set.BOT_OPTIONS['discord_voice_channel'] = channel_int
                save_dict(value_set.BOT_OPTIONS, 'bot_options')

                self.bot.voice_channel = self.bot.get_channel(channel_int)
                await self.bot.disconnect_all_voice()
                await self.bot.channel_connect()
                await ctx.send(f"*Connected to {self.bot.voice_channel}!*")
            else:
                await ctx.send("*Please provide a voice channel ID!\n"
                               "\n"
                               "No idea what that is?\n"
                               "Go to User Settings > Appearance  and turn \"Developer Mode\" on.\n"
                               "Then right click the voice channel you want the bot to use, and select \"Copy ID\"*")
        except AttributeError as e:
            await ctx.send("*Provided channel must be a voice channel!*")
            print(repr(e))

    @commands.command()
    @commands.has_role("~Moderator~")
    async def refmt(self, ctx):
        """Reformat current song's dictionary key to match its YouTube title"""
        old = value_set.MUSIC_QUEUE['default'][-1]
        new = value_set.CURRENT_PLAYER.title
        value_set.MUSIC_QUEUE['default'].remove(old)
        value_set.MUSIC_QUEUE['default'].append(new)
        save_dict(value_set.MUSIC_QUEUE, 'music_queue')
        await ctx.send(f"{old} => {new}")

    @commands.command()
    @commands.has_role("~Moderator~")
    async def clear(self, ctx):
        """
        Attempt to clear up to 200 message from the source chat
        """
        messages = await ctx.history(limit=200).flatten()
        for m in messages:
            if m.author == self.bot.user:
                await m.delete()
        print(">> Discord message deletion complete")

    # @commands.command()
    # @commands.has_role("~Moderator~")
    # async def test1(self, ctx):
    #     await self.bot.announce_stream_start()
    #
    # @commands.command()
    # @commands.has_role("~Moderator~")
    # async def test2(self, ctx):
    #     await self.bot.update_stream_message()

    @commands.command()
    @commands.has_role("~Moderator~")
    async def set_welcome(self, ctx):
        """Set the welcome message for new users in Discord"""
        self.bot.welcome_message = ctx.message.content.split('set_welcome')[1].strip()
        value_set.BOT_OPTIONS['welcome_message'] = self.bot.welcome_message
        save_dict(value_set.BOT_OPTIONS, 'bot_options')
        await ctx.send("*Message set.*")