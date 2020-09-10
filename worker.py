from gw2_tools import save_item_data
from asyncio import sleep, run


async def update_gw2_character_data():
    """Fetch and save GW2 character inventory data"""
    while True:
        save_item_data()
        await sleep(3600)

run(update_gw2_character_data())
