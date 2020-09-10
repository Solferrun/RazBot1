import json
from os import path, environ
from requests import patch, get
# from urllib import request
# import asyncio

from s3_bucket import save_dict, load_dict
from simple_tools import api_fetch

obj_path = path.dirname(path.realpath(__file__)) + '/obj'


region_key = {
    'na': 'C2F5B4C3-8717-C84F-B96E-DF15917563847928F0D2-A25B-4ED2-A786-85AA1A981297',
    'eu': '7BEBEEB7-6B28-D94E-BF94-386393694939CEE078AE-CDB6-47EF-B1DA-B6851481D90F'
}


def set_gw2_dyno_state(set_active):
    state = 1 if set_active else 0
    app_id = environ["heroku_app_id"]
    proc_id = environ["heroku_proc_id"]
    url = f"https://api.heroku.com/apps/{app_id}/formation/{proc_id}"
    payload = {"quantity": state, "size": "Free", "type": "NightMaeric"}
    headers = {"Accept": "application/vnd.heroku+json; version=3",
               "Authorization": f"Bearer {environ["heroku_oauth"]}"}

    patch(url, data=json.dumps(payload), headers=headers).json()


def flatten(l):
    """Flatten a multi-dimensional list"""
    return [item for sublist in l for item in sublist]


def item_data_init():
    with open(f"{obj_path}/item_data.json", 'w') as f:
        print("  >> Retrieving item_data from S3")
        item_data = load_dict('item_data')
        json.dump(item_data, f)


def get_data(*args, region=None):
    """Fetch data from GW2 api"""
    if region is None:
        region = 'eu' if 'EU' in api_fetch('title') else 'na'
    token = region_key.get(region)
    url = f"https://api.guildwars2.com/v2/{'/'.join(args)}"
    headers = {"Authorization": f"Bearer {token}"}

    data = get(url, headers=headers).json()

    return data


def get_character():
    """Get the current/last played character"""
    characters = get_data('characters')
    last_character = characters[0]
    return last_character


def get_cauliflower_score(region='na'):
    cf_total = 0
    print(f">> Loading item data from {obj_path}/item_data.json")
    with open(f"{obj_path}/item_data.json", 'r') as f:
        character_item_data = json.loads(f.read())

        play_region = 'eu' if 'EU' in api_fetch('title') else 'na'
        if play_region == region:
            # Update current character
            this_character = get_character()
            char_name_enc = this_character.replace(' ', '%20')
            upper_inventory = get_data('characters', char_name_enc, 'inventory')
            bags = upper_inventory.get('bags')
            items = flatten(i.get('inventory') for i in bags if i)
            character_item_data[region][this_character] = items

        # Count Cauliflower from all characters
        for character in character_item_data[region]:
            items = character_item_data[region][character]
            cf_count = sum(i.get('count') for i in items if i and i.get('id') == 12532)
            cf_total += cf_count
    return cf_total


def get_inventory_usage():
    character = get_character()

    char_name_enc = character.replace(' ', '%20')
    upper_inventory = get_data('characters', char_name_enc, 'inventory')

    bags = upper_inventory['bags']
    inventory_slots = flatten(b['inventory'] for b in bags if b)
    inventory_size = sum(int(b['size']) for b in bags if b)

    empty_slots = inventory_slots.count(None)
    used_slots = inventory_size - empty_slots

    return f"{character}'s inventory is {used_slots}/{inventory_size} slots full."


def get_build():
    character = get_character()
    with open(f"{obj_path}/builds.json") as f:
        builds = json.loads(f.read())
        character_build = builds.get(character)
        if character_build:
            return f"{character}'s build: {character_build}"
        return f"Maeric still needs to share {character}'s build!"


# def get_world_boss_clears(region='na'):
#     world_bosses = [wb.replace('_', ' ').title() for wb in get_data('worldbosses', region=region)]
#     return ', '.join(world_bosses)


# def get_raid_boss_clears(region='na'):
#     raid_bosses = [rb.replace('_', ' ').title() for rb in get_data('raids', region=region)]
#     return ', '.join(raid_bosses)


def get_magnetite(region='na'):
    with open(f"{obj_path}/item_data.json") as f:
        character_item_data = json.loads(f.read())
        wallet = character_item_data[region]['Wallet']
        magnetite = next(currency for currency in wallet if currency['id'] == 28)
        return magnetite.get('value')
    # if region is None:
    #     region = 'eu' if 'EU' in api_fetch('title') else 'na'
    # wallet = get_data('account', 'wallet', region=region)
    # magnetite = next(currency for currency in wallet if currency['id'] == 28)
    # return f"[{region.upper()}] Magnetite Shards: {magnetite.get('value')}"


def get_gaeting(region='na'):
    with open(f"{obj_path}/item_data.json") as f:
        character_item_data = json.loads(f.read())
        wallet = character_item_data[region]['Wallet']
        gaeting = next(currency for currency in wallet if currency['id'] == 39)
        return gaeting.get('value')
    # if region is None:
    #     region = 'eu' if 'EU' in api_fetch('title') else 'na'
    # wallet = get_data('account', 'wallet', region=region)
    # gaeting = next(currency for currency in wallet if currency['id'] == 39)
    # return f"[{region.upper()}] Gaeting Crystals: {gaeting.get('value')}"


item_vals = {77302: 1, 77401: 1, 77449: 1, 91147: 1, 91160: 1, 91182: 1, 91184: 1, 91186: 1, 91187: 1, 91191: 1,
             91203: 1, 91215: 1, 91233: 1, 91252: 1, 91262: 1, 91267: 1, 88485: 1, 91138: 1, 91157: 1, 91166: 1,
             91172: 1, 91195: 1, 91200: 1, 91211: 1, 91220: 1, 91237: 1, 91241: 1, 91244: 1, 91260: 1, 80111: 25,
             80131: 25, 80145: 25, 80161: 25, 80190: 25, 80205: 25, 80248: 25, 80252: 25, 80254: 25, 80277: 25,
             80281: 25, 80296: 25, 80356: 25, 80384: 25, 80399: 25, 80435: 25, 80557: 25, 80578: 25}


def get_insight_count(region='na'):
    li_total = 0
    with open(f"{obj_path}/item_data.json", 'r') as f:
        character_item_data = json.loads(f.read())
        for character in character_item_data[region]:
            items = character_item_data[region][character]
            li_count = sum(i.get('count')*item_vals.get(i.get('id')) for i in items if i and i.get('id') in item_vals)
            li_total += li_count
    return li_total


def save_item_data():
    print(">> Retrieving GW2 item data from API")
    na_character_item_data = {}
    eu_character_item_data = {}

    # Fetch NA item data
    characters = get_data('characters', region='na')
    for character in characters:
        char_enc = character.replace(' ', '%20')
        upper_inventory = get_data('characters', char_enc, 'inventory', region='na')
        bags = upper_inventory.get('bags')
        bags.append({'inventory': get_data('characters', char_enc, 'equipment', region='na').get('equipment')})
        items = flatten(i.get('inventory') for i in bags if i)
        na_character_item_data[character] = items
        print(f"  >> [NA]{character}'s item data retrieved")

    na_character_item_data['Shared Bank'] = get_data('account', 'bank', region='na')
    na_character_item_data['Shared Inventory'] = get_data('account', 'inventory', region='na')
    na_character_item_data['Materials'] = get_data('account', 'materials', region='na')
    na_character_item_data['Wallet'] = get_data('account', 'wallet', region='na')

    # Fetch EU item data
    characters = get_data('characters', region='eu')
    for character in characters:
        char_enc = character.replace(' ', '%20')
        upper_inventory = get_data('characters', char_enc, 'inventory', region='eu')
        bags = upper_inventory.get('bags')
        bags.append({'inventory': get_data('characters', char_enc, 'equipment', region='eu').get('equipment')})
        items = flatten(i.get('inventory') for i in bags if i)
        eu_character_item_data[character] = items
        print(f"  >> [EU]{character}'s item data retrieved")

    eu_character_item_data['Shared Bank'] = get_data('account', 'bank', region='eu')
    eu_character_item_data['Shared Inventory'] = get_data('account', 'inventory', region='eu')
    eu_character_item_data['Materials'] = get_data('account', 'materials', region='eu')
    eu_character_item_data['Wallet'] = get_data('account', 'wallet', region='eu')

    print("  >> Creating item_data dict")
    item_data = {'na': na_character_item_data, 'eu': eu_character_item_data}
    print("  >> Saving item_data to S3")
    save_dict(item_data, 'item_data')

    print(">> GW2 item data retrieval done")
