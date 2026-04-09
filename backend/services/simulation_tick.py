
import asyncio
from services.physiology import update_needs
from services.homeostasis import generate_homeostasis_goals

characters = [
    {"id": "npc_1", "needs": {"hunger":10,"thirst":10,"fatigue":10,"bladder":10}}
]

async def simulation_loop():
    while True:
        for c in characters:
            update_needs(c)
            c["goal"] = generate_homeostasis_goals(c)
        await asyncio.sleep(1)
