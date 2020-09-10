from s3_bucket import load_dict

CURRENT_PLAYER = None
RAZ_PETS = load_dict('raz_pets')
MUSIC_QUEUE = load_dict('music_queue')
BOT_OPTIONS = load_dict('bot_options')

advanced_commands = {}
custom_commands = {}