#!/usr/bin/python
# -*- coding: utf-8 -*-
from time import time
from os import environ
from traceback import format_exc
from random import randint, choice, shuffle

from s3_bucket import save_dict, load_dict
from twitch_socket import get_stream_list
from pastebin import make_paste
from weapon import get_weapon
from counter import Counter, counters
from hybrid_bot import bot
import simple_tools
import gw2_tools
import value_set
import roulette
import re

value_set.custom_commands = load_dict('custom_commands')

cooldowns = {}


def log_err(func):
    """Abort command and print log to console on error"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            print(f"Error in {func.__name__}:\n{format_exc()}")

    return wrapper


def mod_only(func):
    """Ensure message author is mod"""
    def wrapper(msg):
        if msg.is_mod:
            return func(msg)
        else:
            return "Sorry, that's a mod-only command!"
    return wrapper


def cooldown(duration=2):
    """Ensure command cooldown period has passed"""
    def decorator(func):
        def wrapper(msg):
            now = int(time())
            name = func.__name__
            on_cooldown = False
            if name in cooldowns:
                on_cooldown = cooldowns.get(name) + duration > now
            if not on_cooldown:
                cooldowns[name] = now
                return func(msg)
            else:
                return None
        return wrapper
    return decorator


@log_err
def command_exists(command_token):
    """Test command availability"""
    if command_token in simple_tools.simple_commands:
        return True
    if command_token in value_set.advanced_commands:
        return True
    if command_token in value_set.custom_commands:
        return True
    return False


@log_err
def load_ctr_commands():
    """Load stored counters"""
    if counters:
        for ctr in counters:
            if command_exists(ctr):
                print(f"!! Failed to load Counter: {ctr}. Command or counter already exists.")
            else:
                value_set.advanced_commands[ctr] = exec_counter


# ADD COMMAND
@log_err
@mod_only
def exec_add(msg):
    """Add a custom command"""
    if msg.args:
        if len(msg.args) > 1:
            command_token = msg.args[0].lower()
            command_output = ' '.join(msg.args[1:])
            if command_exists(command_token):
                return "Command or counter already exists: {}".format(command_token)
            value_set.custom_commands[command_token] = command_output
            save_dict(value_set.custom_commands, 'custom_commands')
            return "Added command: {}".format(command_token)
        else:
            return "The format is: !add {command_name} {command_content}"


# REMOVE COMMAND
@log_err
@mod_only
def exec_remove(msg):
    """Remove a custom command by token"""
    if msg.args:
        command_token = msg.args[0].lower()
        if command_token in value_set.custom_commands:
            value_set.custom_commands.pop(command_token)
            save_dict(value_set.custom_commands, 'custom_commands')
            return "Removed command: {}".format(command_token)
        if command_token in counters:
            counters.pop(command_token)
            value_set.advanced_commands.pop(command_token)
            counter_data = [{'token': c, 'count': counters[c].count, 'admins': counters[c].admins} for c in counters]
            save_dict(counter_data, 'counters')
            return "Counter was removed: {}".format(command_token)
        return "Command could not be removed: {}".format(command_token)


# UPDATE COMMAND
@log_err
@mod_only
def exec_update(msg):
    """Edit a custom command by token"""
    if msg.args and len(msg.args) > 1:
        command_token = msg.args[0].lower()
        command_output = ' '.join(msg.args[1:])
        if command_token in value_set.custom_commands:
            value_set.custom_commands.pop(command_token)
            value_set.custom_commands[command_token] = command_output
            save_dict(value_set.custom_commands, 'custom_commands')
            return f"{command_token} updated!"
        return f"{command_token} wasn't found in custom commands!"


# CUSTOM COMMAND
@log_err
def exec_custom(msg):
    """Get a list of custom commands"""
    if msg.args and len(msg.args) >= 2:
        new_msg = msg
        arg_cmd = new_msg.args.pop(0)
        if arg_cmd == 'add':
            return exec_add(new_msg)
        elif arg_cmd == 'remove':
            return exec_remove(new_msg)
    custom_command_list = ', '.join(value_set.custom_commands) if value_set.custom_commands else "None yet!"
    if len(custom_command_list) <= 480:
        return "Custom commands: {}".format(custom_command_list)
    else:
        kv_sort = list(f"{k} => {value_set.custom_commands[k]}" for k in value_set.custom_commands.keys())
        content = '[' + ']\n['.join(kv_sort) + ']'
        return "Custom commands: " + make_paste('custom_commands', content)


# FOLLOWAGE
@log_err
@cooldown(duration=5)
def exec_howlong(msg):
    """Get invoking user's follow time"""
    content = simple_tools.api_fetch('followage', msg.user)
    return "{0} has been following for: {1}".format(msg.display_name, content)


# GAME
@log_err
@cooldown(duration=5)
def exec_game(msg):
    """Get the current game from Twitch"""
    content = simple_tools.api_fetch('game')
    return "{0} is currently playing: {1}".format(environ['TWITCH_CHANNEL'], content)


# UPTIME
@log_err
@cooldown(duration=5)
def exec_uptime(msg):
    """Get stream uptime from Twitch"""
    content = simple_tools.api_fetch('uptime')
    if 'offline' not in content:
        return f"{environ['TWITCH_CHANNEL']} has been live for: {content}"
    else:
        return f"{environ['TWITCH_CHANNEL']} is not live razBot"


# MULTI
@log_err
@cooldown(duration=5)
def exec_multi(msg):
    """Generate a multitwitch link featuring the streamer and all provided usernames"""
    if msg.args:
        users = [x.replace('@', '') for x in msg.args]
        return simple_tools.get_multi(users)
    else:
        return "The format is: !multi {user} {user} ..."


@log_err
@cooldown(duration=5)
def exec_title(msg):
    """Get the current stream title from Twitch"""
    return "The stream title is: {}".format(simple_tools.api_fetch('title'))


# CHOOSE
@log_err
@cooldown(duration=2)
def exec_choose(msg):
    """Choose between provided options"""
    return simple_tools.get_pick(msg.args_string)


# ICECREAM
@log_err
@cooldown(duration=2)
def exec_icecream(msg):
    """Give random ice cream to invoking user"""
    target = msg.mentions[0] if msg.mentions else msg.display_name
    return simple_tools.get_icecream(target)


# 8BALL
@log_err
@cooldown(duration=2)
def exec_8ball(msg):
    """Give random fortune to invoking user"""
    return simple_tools.get_fortune(msg.args_string)


# CAST
@log_err
@cooldown(duration=2)
def exec_cast(msg):
    """Make the invoking user cast a random or custom spell"""
    spell = simple_tools.get_spellname()
    try:
        target = msg.mentions[0]
        return "{0} casts {1} on {2}!".format(msg.display_name, spell, target)
    except IndexError:
        return "{0} casts {1} on themselves!".format(msg.display_name, spell)


# RANDOM
@log_err
@cooldown(duration=2)
def exec_random(msg):
    """Generate a random number between args 1 and 2 for invoking user"""
    try:
        a = int(msg.args[0])
        b = int(msg.args[1])
        return str(randint(min(a, b), max(a, b)))
    except (IndexError, TypeError):
        return "The format is: !random {number} {number}"


# SHOUTOUT
@log_err
@cooldown(duration=5)
def exec_shoutout(msg):
    """Do a shoutout for the provided user"""
    if msg.mentions:
        last_played = simple_tools.api_fetch('game', msg.mentions[0])
        return f"Check out {msg.mentions[0]}'s channel, and give them a follow! They were last seen " \
            f"playing {last_played} at https://www.twitch.tv/{msg.mentions[0]}"
    elif msg.args:
        last_played = simple_tools.api_fetch('game', msg.args[0])
        return f"Check out {msg.args[0]}'s channel, and give them a follow! They were last seen " \
            f"playing {last_played} at https://www.twitch.tv/{msg.args[0]}"
    return f'I didn\'t see any mentions, so I\'ll just shoutout myself! @{environ["BOT_NAME"]} razCool'


# GETSTREAM
@log_err
@mod_only
@cooldown(duration=5)
def exec_getstream(msg):
    """Get a random stream based on the provided game title"""
    game_name = 'Guild%20Wars%202'
    if msg.args_string:
        game_name = msg.args_string.replace(' ', '%20')
    streams = get_stream_list(f'limit=100&game={game_name}&language=en&stream_type=live')
    if streams:
        for stream in streams.values():
            print(f'[{stream.streamer_id}] {stream.info}')
        candidates = list(filter(
            lambda s: (s.stream_viewers > 5) and (s.stream_viewers < 50),
            streams.values()))
        if any(candidates):
            sel = choice(candidates)
            return sel.info
    return f'No streams found for game: "{game_name.replace("%20", " ")}"'


# OWO
@log_err
@cooldown(duration=5)
def exec_owo(msg):
    """Genewate a owo bewsion ob da pwobided stwing"""
    message = msg.args_string.lower()
    subs = {
        "who'd": "who would", "what'd": "what did", "where'd": "where did", "when'd": "when did", "why'd": "why did",
        "ain't": "isn't", "isn't": "innint", "weren't": "wuwwent", "wasn't": "wunnent", "wouldn't": "woonent",
        "how'd": "how did", "can't": "can not", "au": "awu", "oy": "owoy", "r": "w", "l": "w", "kn": "n", "sch": "skw",
        "ove": "uv", "?": "?? ʘwʘ", "!": "! ✧w✧", "<3": "♥w♥", "oo": "oow", "you": "yoo", "have": "hab", "with": "wif",
        "who": "hoo", "what": "wat", "where": "wheow", "when": "wen", "why": "wy", "would": "woowd", "'ve": " have",
        "n't": ' not', "this": "dis", "ck": "c", "shit": "pewps", "hell": "hec", "damn": "pewpin", "penis": "pp"}
    for s in subs:
        message = message.replace(s, subs[s])
    message = re.sub('(?<=o)([aei])', r'w\1', message)
    message = re.sub('(?<=u)([aeiou])', r'w\1', message)
    message = re.sub('(?<= )the ', r'da ', message)
    message = re.sub('(.)th([aeu ].)', r'\1d\2', message)
    message = re.sub('(.)th([^aeu ].)', r'\1t\2', message)
    message = re.sub('(.)o([^o])', r'\1ow\2', message)
    message = re.sub(r"(\w)'we", r'\1 awe', message)
    message = re.sub(r"(\w)'d", r'\1 woowd', message)
    message = message.replace('iw', 'iow')
    message = message.replace('v', 'b')
    message = message.replace('owu', 'ow')
    return message


# PIRATE SPEAK
@log_err
@cooldown(duration=5)
def exec_pirate(msg):
    """It do be spittin' back yer babble in the way of a pirate"""
    message = msg.args_string.lower()
    subs = {
        'will be': 'be', 'doing': 'be doin\'', 'am': 'do be', 'is': 'do be', 'are': 'be', 'you': 'ye', 'my': 'me',
        'buddy': 'bucko', 'hello': 'ahoy there', 'hi': 'ahoy', 'hey': 'ahoy', 'yo': 'yo-ho', 'sup': 'yo-ho',
        'howdy': 'ahoy', 'friend': 'matey', 'pal': 'matey', 'amigo': 'matey', 'and': 'an\'',
        'vice versa': 'the reverse', 'talk': 'blabber', 'semi': 'half', 'wait': 'avast', 'hold on': 'avast',
        'stop': 'avast', 'the back': 'the aft', 'of': '\'o', 'guys': 'hearties', 'friends': 'hearties',
        'damn': 'blimey', 'treasure': 'booty', 'loot': 'booty', 'gold': 'booty', 'money': 'booty', 'sword': 'cutlass',
        'toilet': 'head', 'bathroom': 'head', 'noob': 'landlubber', 'person': 'seadog', 'people': 'seadogs',
        'wow': 'Shiver me timbers!', 'omg': 'Shiver me timbers!', 'die': 'walk the plank',
        'dead': 'sleepin\' in Davy Jones\' locker', 'yes': 'aye', 'yeah': 'aye', 'yep': 'aye', 'ok': 'aye aye',
        'whoa': 'blow me down', 'woah': 'blow me down', 'chest': 'coffer', 'dollars': 'doubloons', 'steal': 'plunder',
        'see': 'spy', 'think': 'reckon', 'world': 'seven seas', 'hey': 'oy', 'god': 'ferryman'
    }

    for s in subs:
        message = re.sub(r"(^|\W)({})($|\W)".format(s), r"\1{}\3".format(subs[s]), message)

    message = re.sub(r"(ing)($|\W)", r"in'\2", message)

    return message


# ROULETTE MANAGEMENT
@log_err
@mod_only
def exec_roulette(msg):
    """Manage an volitional entry roulette"""
    if not msg.args:
        # EDGE CASES
        if roulette.round_obj:
            return f"There is a roulette running! Simply type \"{roulette.round_obj.entry_phrase}\" in chat to enter!"
        else:
            return "There is currently no roulette running. The format is: !roulette {entry phrase} | !roulette end"
    else:
        first_word = msg.args[0].strip()
        # END ROULETTE
        if first_word == 'end':
            if roulette.round_obj:
                print("Roulette ended.")
                if roulette.round_obj.users:
                    result = roulette.round_obj.result()
                    roulette.round_obj = None
                    return result
                else:
                    roulette.round_obj = None
                    return "The roulette is over! No one entered, so I guess I win! razCool"
            else:
                return "There is currently no roulette running."
        # GET ENTRANTS
        elif first_word == 'entrants' or first_word == 'who':
            if roulette.round_obj:
                entrants = ', '.join(roulette.round_obj.users)
                return f"Current roulette entrants: {entrants}"
            else:
                return "There is currently no roulette running."
        # CREATE ROULETTE
        else:
            if roulette.round_obj:
                return f"@{msg.display_name} There's already a roulette running! The entry phrase " \
                    f"is \"{roulette.round_obj.entry_phrase}\". To end the roulette, please use: !roulette end"
            else:
                roulette.round_obj = roulette.Roulette(msg.args_string.strip())
                print(f"Roulette created with entry phrase: {roulette.round_obj.entry_phrase}")
                return f"A new roulette round has been started! " \
                       f"Simply type \"{roulette.round_obj.entry_phrase}\" in chat to enter!"


# COUNTERS
@log_err
def exec_make_counter(msg):
    """Create a new counter by name"""
    if msg.args and msg.is_mod:
        counter_name = msg.args[0].lower()
        if not command_exists(counter_name) and msg.is_mod:
            value_set.advanced_commands[counter_name] = exec_counter
            admins = msg.mentions if msg.mentions else None
            count = int(msg.args[1]) if len(msg.args) > 1 and msg.args[1].isdigit() else 0

            # Create counter
            counters[counter_name] = Counter(count=count, admins=admins)
            result = f"Counter created: {counter_name} ({count})"
            result += f" // Permissions for: {', '.join(['moderators', *msg.mentions])}"

            # Save counter list
            counter_data = [{'token': c, 'count': counters[c].count, 'admins': counters[c].admins} for c in counters]
            save_dict(counter_data, 'counters')
            return result
        else:
            if msg.mentions:
                new_admins = list(filter(lambda m: m not in counters[counter_name].admins, msg.mentions))
                counters[counter_name].admins += new_admins
                if new_admins:
                    return "Edit permissions for {} counter granted to: {}".format(counter_name, ', '.join(new_admins))
                else:
                    return "Permissions already granted for: {}".format(', '.join(msg.mentions))
            return "Command or counter already exists: {}".format(counter_name)
    current_counters = [f"{c} ({counters[c].count})" for c in counters]
    return "Use \"!\" followed by the counter name to view a counter's state (e.g. !deaths). " \
           "Current counters: {}".format(', '.join(current_counters) if current_counters else None)


@log_err
def exec_counter(msg):
    """Control or create counters"""
    if msg.message:
        counter_name = msg.message.split()[0][1:]
        if msg.args:
            command_name = msg.args[0]
            counter = counters[counter_name]
            has_edit_privileges = msg.is_mod or msg.user in counter.admins
            instructions = "Usage examples: !{0} +1 // !{0} -3 // !{0} =24 // " \
                           "!{0} remove // !{0} users".format(counter_name)
            if counter and has_edit_privileges:
                if command_name.startswith('='):
                    try:
                        amount = int(msg.args_string.replace('=', ''))
                        counter.set_to(amount)
                    except ValueError:
                        return instructions
                elif command_name in ['permissions', 'users', 'edit', 'admins']:
                    if counter.admins:
                        return "Users who may edit {0} counter: {1}".format(counter_name, ', '.join(counter.admins))
                    else:
                        return "Users who may edit {0} counter: {1}".format(counter_name, "Mods only")
                elif command_name in ['remove', 'delete']:
                    value_set.advanced_commands.pop(counter_name)
                    counters.pop(counter_name)
                    counter_data = {{'token': c, 'count': counters[c].count, 'admins': counters[c].admins} for c in
                                    counters}
                    save_dict(counter_data, 'counters')
                    return "Counter was removed: {}".format(counter_name)
                else:
                    try:
                        operators = ['+', '-', '*', '/', '(', ')', '[', ']', ' ']
                        for c in msg.args_string:
                            if not c.isdigit() and c not in operators:
                                raise SyntaxError
                        if not counter.set_to(eval("{} {}".format(counters[counter_name].count, msg.args_string))):
                            return None
                    except SyntaxError:
                        return instructions
                counter_data = [{'token': c, 'count': counters[c].count, 'admins': counters[c].admins} for c in
                                counters]
                save_dict(counter_data, 'counters')
                return "The {0} counter is now at {1}.".format(counter_name, counter.count)
        return "{0}: {1}".format(counter_name.capitalize(), counters[counter_name].count)


@log_err
@cooldown(duration=5)
def exec_dice(msg):
    """Custom dice-rolling game"""
    dice = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣']
    result = ""
    point = 0
    while True:
        roll = [randint(0, 5), randint(0, 5)]
        rsum = roll[0] + roll[1] + 2
        result += f"{dice[roll[0]]}{dice[roll[1]]}({rsum}) > "
        if rsum == point or rsum == 11:
            return result + "WINNER! razCool"
        elif not point and (rsum == 7 or rsum == 11):
            return result + "WINNER! razCool"
        elif rsum == 7:
            return result + "LOSER! razHands"
        elif any(x == rsum for x in [2, 3]):
            return result + "LOSER! razHands"
        elif point == 0:
            point = rsum


# ATTACK
@log_err
@cooldown(duration=5)
def exec_attack(msg):
    """Invoking user attacks the mentioned user"""
    if msg.mentions:
        target = msg.mentions[0]
        weapon = get_weapon()
        damage_amount = weapon.roll_attack_power()
        damage_verb = weapon.damage_type.verb
        damage_noun = weapon.damage_type.noun
        return f"{msg.display_name} {damage_verb} {target} for {damage_amount} {damage_noun} damage!"


# CURSE
@cooldown(duration=5)
def exec_curse(msg):
    """Inflicts a random curse on mentioned user"""
    if msg.mentions:
        return simple_tools.curse(msg.display_name, msg.mentions[0])


# WIELD
@log_err
@cooldown(duration=5)
def exec_wield(msg):
    """Wield a random weapon for invoking user"""
    return f"{msg.display_name} wields their [{get_weapon().name}]!"


@log_err
def exec_raz(msg):
    """Return a random raz pet from stored history"""
    if msg.args and msg.is_mod:
        cmd = msg.args[0].lower()
        cmd_arg = None
        if len(msg.args) > 1:
            cmd_arg = msg.args[1]
        if cmd == 'ls':
            for k, v in value_set.RAZ_PETS.items():
                print(f"{k}: {v}")
            return None
        elif cmd == 'rm' and cmd_arg and cmd_arg in value_set.RAZ_PETS:
            value_set.RAZ_PETS.pop(cmd_arg)
            save_dict(value_set.RAZ_PETS, 'raz_pets')
            return f"Removed: {cmd_arg}"
        elif cmd == 'add' and cmd_arg:
            value_set.RAZ_PETS[cmd_arg] = f'https://www.instagram.com/p/{cmd_arg}'
            save_dict(value_set.RAZ_PETS, 'raz_pets')
            return f"Added: {value_set.RAZ_PETS[cmd_arg]}"
    if value_set.RAZ_PETS:
        url = choice(list(value_set.RAZ_PETS.values()))
        return f"Random Raz pets! {url}"


# PLAYLIST
@log_err
@mod_only
@cooldown(duration=5)
def exec_playlist(msg):
    """Control the Discord playlist"""
    if msg.args:
        cmd = msg.args[0]
        if len(msg.args) > 1:
            cmd_arg = ' '.join(msg.args[1:])

            if cmd == 'add':
                value_set.MUSIC_QUEUE['default'].append(cmd_arg)
                save_dict(value_set.MUSIC_QUEUE, 'music_queue')
                return f"Added \"{cmd_arg}\" to the default playlist! razBot"

            if cmd == 'remove':
                try:
                    value_set.MUSIC_QUEUE['default'].remove(cmd_arg)
                    save_dict(value_set.MUSIC_QUEUE, 'music_queue')
                    return f"Removed \"{msg.args_string}\" from the default playlist! razBot"
                except ValueError:
                    return f"\"{cmd_arg}\" wasn't found in the default playlist! razBlank Use \"!pl\" to " \
                        f"view the contents of the default playlist."
        elif cmd == 'add':
            if value_set.CURRENT_PLAYER.title not in value_set.MUSIC_QUEUE['default']:
                value_set.MUSIC_QUEUE['default'].append(value_set.CURRENT_PLAYER.title)
                save_dict(value_set.MUSIC_QUEUE, 'music_queue')
                return f"Added \"{value_set.CURRENT_PLAYER.title}\" to the default playlist!"
            else:
                return "It's already in razWink"
        elif cmd == 'remove':
            if value_set.CURRENT_PLAYER.title in value_set.MUSIC_QUEUE['default']:
                target = value_set.MUSIC_QUEUE['default'][-1]
                output = f"Removed \"{target}\" from the default playlist! razBot"
                value_set.MUSIC_QUEUE['default'].remove(target)
                save_dict(value_set.MUSIC_QUEUE, 'music_queue')
                exec_skip(msg)
                return output
            else:
                exec_skip(msg)

        elif cmd == 'shuffle' or cmd == 'mix':
            shuffle(value_set.MUSIC_QUEUE['default'])
            save_dict(value_set.MUSIC_QUEUE, 'music_queue')
            def_playlist = '\n'.join(value_set.MUSIC_QUEUE['default'])
            print(f"Default Playlist: {def_playlist}")
            return f"Default playlist shuffled! razBot"
    else:
        content = "\n".join(value_set.MUSIC_QUEUE['default'])
        return "Default Playlist: " + make_paste('default_playlist', content)


# SONG REQUEST
@log_err
@cooldown(duration=5)
def exec_songrequest(msg):
    """Manually request a song for the Discord player"""
    if msg.args and msg.is_mod:
        value_set.MUSIC_QUEUE['request'].append(msg.args_string)
        print(f"Request Queue: {value_set.MUSIC_QUEUE['request']}")
        save_dict(value_set.MUSIC_QUEUE, 'music_queue')
        request_count = len(value_set.MUSIC_QUEUE['request'])
        request_wait = f"{request_count}{simple_tools.get_num_suffix(request_count)}" if request_count > 1 else "next"
        return f"@{msg.display_name} Your request is {request_wait} in the song queue! razCool"
    elif not msg.is_mod:
        return "Use Yarn Balls to request a song from YouTube when the request player is active!"


# PAUSE
@log_err
@mod_only
@cooldown(duration=30)
def exec_pause(msg):
    """Pause the discord player"""
    if bot.get_voice():
        vc = bot.get_voice()
        paused = vc.is_paused()
        if paused:
            vc.resume()
        else:
            vc.pause()
        return "Player {}.".format('unpaused' if paused else 'paused')


# SKIP
@log_err
@mod_only
@cooldown(duration=5)
def exec_skip(msg):
    """Tell the Discord player to skip the current song"""
    if bot.get_voice():
        bot.get_voice().stop()
        value_set.MUSIC_QUEUE = load_dict('music_queue')


# VOLUME
@log_err
@mod_only
def exec_volume(msg):
    """Adjust the Discord player's volume by %"""
    if bot.get_voice():
        if msg.args and msg.args[0].isdigit():
            volume = max(min(int(msg.args[0]), 100), 0)
            bot.get_voice().source.volume = volume / 100
            return f"Player volume set to {volume}%"
        else:
            current_volume = int(bot.get_voice().source.volume * 100)
            return f"Current volume: {current_volume}. Use !volume [0-100] to adjust it."


# SONG
@log_err
@cooldown(duration=5)
def exec_song(msg):
    """Return the current song from the Discord player"""
    if bot.get_voice():
        return f'Currently playing: {value_set.CURRENT_PLAYER.title} razJAM'


# QUEUE
@log_err
@cooldown(duration=30)
def exec_queue(msg):
    """Return the request queue"""
    if value_set.MUSIC_QUEUE['request']:
        raw_list = 'Request Queue: [' + '], ['.join(value_set.MUSIC_QUEUE['request']) + ']'
        if len(raw_list) < 500:
            return raw_list
        else:
            content = "\n".join(value_set.MUSIC_QUEUE['request'])
            return "Request Queue: " + make_paste('request_playlist', content)
    else:
        return 'The request queue is empty!'


# PLAYER
@log_err
@mod_only
def exec_player(msg):
    """Control the Discord player"""
    if not msg.args:
        player_status = 'enabled' if value_set.BOT_OPTIONS.get('player_enabled') else 'disabled'
        response = f"Player is {player_status}. "
        if value_set.CURRENT_PLAYER:
            response += f'The current/last played audio is: {value_set.CURRENT_PLAYER.title}. '
        response += 'Mod Usage: !player [ on | off | skip | pause | volume | reset | queue ]'
        return response
    cmd = msg.args[0].lower()

    if cmd == 'off' or cmd == 'disable' and value_set.BOT_OPTIONS.get('player_enabled'):
        value_set.BOT_OPTIONS['player_enabled'] = False
        save_dict(value_set.BOT_OPTIONS, 'bot_options')
        return 'Player disabled.'

    elif cmd == 'on' or cmd == 'enable' and not value_set.BOT_OPTIONS.get('player_enabled'):
        value_set.BOT_OPTIONS['player_enabled'] = True
        save_dict(value_set.BOT_OPTIONS, 'bot_options')
        return 'Player enabled.'

    elif cmd == 'skip' or cmd == 'next' and bot.get_voice():
        return exec_skip(msg)

    elif cmd == 'pause' or cmd == 'stop' and bot.get_voice():
        return exec_pause(msg)

    elif cmd == 'volume' and bot.get_voice():
        new_msg = msg
        new_msg.args.pop(0)
        return exec_volume(new_msg)

    elif cmd == 'link' or cmd == 'source' and bot.get_voice():
        return f'/w {msg.user} {simple_tools.tiny_url(value_set.CURRENT_PLAYER.url)}'

    elif cmd == 'queue' or cmd == 'q':
        return exec_queue(msg)

    elif cmd == 'add' or cmd == 'remove':
        return exec_playlist(msg)


@log_err
@cooldown(duration=5)
def exec_pets(msg):
    """Manual Raz Pets management"""
    if msg.is_mod and msg.args:
        cmd = msg.args[0].lower()
        cmd_arg = None
        if len(msg.args) > 1 and msg.args[1] in value_set.RAZ_PETS:
            cmd_arg = msg.args[1]
        if cmd == 'ls':
            print(f"[{', '.join(value_set.RAZ_PETS.keys())}]")
        elif cmd == 'rm' and cmd_arg:
            value_set.RAZ_PETS.pop(cmd_arg)
            print(f"Removed: {value_set.RAZ_PETS[cmd_arg]}")
        elif cmd == 'add' and cmd_arg:
            value_set.RAZ_PETS[cmd_arg] = f'https://www.instagram.com/p/{cmd_arg}'
            print(f"Added: {value_set.RAZ_PETS[cmd_arg]}")


@log_err
@cooldown(duration=5)
def exec_discord(msg):
    """Broadcast the Discord server"""
    return f"Come join our awesome community on Discord! -> {environ['DISCORD_INVITE_URL']}"


@log_err
@cooldown(duration=5)
def exec_dpsloss(msg):
    """Knight's dpsloss idea"""
    dps_loss_messages = ["What? Did Maeric die again?", "It’s his fashion wars, isn’t it?",
                         "Oh no, did Raz shut the PC off again?", "Is Juni needing a spider killed?",
                         "Oh no, he left the aerodrome, didn’t he?"]
    return choice(dps_loss_messages)


@log_err
@cooldown(duration=10)
def exec_cauliflower(msg):
    region = 'na'
    if msg.args:
        region_arg = msg.args[0].lower()
        if region_arg == 'eu':
            region = region_arg
            print('eu region cf')
    cauliflower = gw2_tools.get_cauliflower_score(region)
    return f"[{region.upper()}] Maeric's Cauliflower Score: {cauliflower}"


@log_err
@cooldown(duration=10)
def exec_inventory(msg):
    return gw2_tools.get_inventory_usage()


@log_err
@cooldown(duration=2)
def exec_build(msg):
    return gw2_tools.get_build()


@log_err
@cooldown(duration=5)
def exec_gw2(msg):
    return "GW2 related commands: !build, !kp, !insights, !magnetite, !gaeting, !cauliflower, !inventory"


@log_err
@cooldown(duration=2)
def exec_magnetite(msg):
    region = 'na'
    if msg.args:
        region_arg = msg.args[0].lower()
        if region_arg == 'eu':
            region = region_arg
    magnetite = gw2_tools.get_magnetite(region)
    return f"[{region.upper()}] Magnetite Shards: {magnetite}"


@log_err
@cooldown(duration=1)
def exec_gaeting(msg):
    region = 'na'
    if msg.args:
        region_arg = msg.args[0].lower()
        if region_arg == 'eu':
            region = region_arg
    gaeting = gw2_tools.get_gaeting(region)
    return f"[{region.upper()}] Gaeting Crystals: {gaeting}"


@log_err
@cooldown(duration=1)
def exec_insights(msg):
    region = 'na'
    if msg.args:
        region_arg = msg.args[0].lower()
        if region_arg == 'na' or region_arg == 'eu':
            region = region_arg
    insights = gw2_tools.get_insight_count(region)
    return f"[{region.upper()}] Legendary Insights/Divinations: {insights}"


@log_err
@cooldown(duration=1)
def exec_kp(msg):
    region = 'na'
    if msg.args:
        region_arg = msg.args[0].lower()
        if region_arg == 'na' or region_arg == 'eu':
            region = region_arg
    magnetite = gw2_tools.get_magnetite(region)
    gaeting = gw2_tools.get_gaeting(region)
    insights = gw2_tools.get_insight_count(region)
    return f"[{region.upper()}] MS: {magnetite} / GC: {gaeting} / LI: {insights}"


# @log_err
# @cooldown(duration=3)
# def exec_clears(msg):
#     region = 'na'
#     if msg.args:
#         arg1 = msg.args[0].lower()
#         if arg1 == 'world':
#             if len(msg.args) > 1:
#                 arg2 = msg.args[1].lower()
#                 region = arg2 if arg2 == 'eu' else 'na'
#             clears = gw2_tools.get_world_boss_clears(region)
#             f"[{region.upper()}] Daily World Boss Clears: {clears}"
#         elif arg1 == 'eu':
#             region = 'eu'
#     clears = gw2_tools.get_raid_boss_clears(region)
#     return f"[{region.upper()}] Weekly Raid Boss Clears: {clears}"


@log_err
@mod_only
@cooldown(duration=5)
def exec_test(msg):
    gw2_tools.save_item_data()
    return "Item data saved."
    #value_set.BOT_OPTIONS['stream_online'] = True


value_set.advanced_commands = {
    'test': exec_test,
    'howlong': exec_howlong,
    'followage': exec_howlong,
    'game': exec_game,
    'uptime': exec_uptime,
    'multi': exec_multi,
    'title': exec_title,
    'choose': exec_choose,
    'pick': exec_choose,
    'icecream': exec_icecream,
    '8ball': exec_8ball,
    'cast': exec_cast,
    'shoutout': exec_shoutout,
    'so': exec_shoutout,
    'count': exec_make_counter,
    'counter': exec_make_counter,
    'counters': exec_make_counter,
    'roulette': exec_roulette,
    'add': exec_add,
    'remove': exec_remove,
    'custom': exec_custom,
    'random': exec_random,
    'owo': exec_owo,
    'curse': exec_curse,
    'getstream': exec_getstream,
    'ps': exec_pirate,
    'pirate': exec_pirate,
    'raz': exec_raz,
    'sr': exec_songrequest,
    'songrequest': exec_songrequest,
    'song': exec_song,
    'player': exec_player,
    'p': exec_player,
    'pause': exec_pause,
    'skip': exec_skip,
    'volume': exec_volume,
    'playlist': exec_playlist,
    'pl': exec_playlist,
    'queue': exec_queue,
    'q': exec_queue,
    'requests': exec_queue,
    'attack': exec_attack,
    'fight': exec_attack,
    'wield': exec_wield,
    'weild': exec_wield,
    'equip': exec_wield,
    'weapon': exec_wield,
    'dice': exec_dice,
    'discord': exec_discord,
    'dpsloss': exec_dpsloss,
    'cauliflower': exec_cauliflower,
    'cf': exec_cauliflower,
    'inventory': exec_inventory,
    'magnetiteshards': exec_magnetite,
    'magnetite': exec_magnetite,
    'ms': exec_magnetite,
    'gaetingcrystals': exec_gaeting,
    'gaeting': exec_gaeting,
    'gc': exec_gaeting,
    'insights': exec_insights,
    'li': exec_insights,
    'kp': exec_kp,
    'build': exec_build,
    'gw2': exec_gw2,
    'update': exec_update,
    'edit': exec_update
}