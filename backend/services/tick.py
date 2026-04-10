import asyncio
from services.state import get_world, init_world
from services.db import upsert_character, log_event
from services.ws import manager
from services.institutions import tick_institutions

async def simulation_loop():
    world = get_world()
    init_world()
    while True:
        world["tick"] += 1
        for cid, c in world["characters"].items():
            c["thoughts"] = f"Tick {world['tick']}."
            upsert_character(cid, c)
        tick_institutions(world)
        log_event(world["tick"], "tick", None, None, {"character_count": len(world["characters"])})
        await manager.broadcast(world)
        await asyncio.sleep(1.0)
