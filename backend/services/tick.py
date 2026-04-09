import asyncio
from services.state import get_world, init_world
from services.db import upsert_character, log_event
from services.cache import set_world_snapshot, push_recent_event
from services.ws import manager
from services.conversation import maybe_start_conversation, conversation_turn
from services.institutions import tick_institutions

async def simulation_loop():
    world = get_world()
    init_world()
    while True:
        world["tick"] += 1

        # simple autonomous conversation trigger
        if world["tick"] == 2:
            maybe_start_conversation(world, "npc_1", "npc_2")

        for cid, c in world["characters"].items():
            c["thoughts"] = f"Tick {world['tick']}."
            upsert_character(cid, c)

        # step active conversations
        for cid, c in list(world["characters"].items()):
            if c.get("conversation_id"):
                conversation_turn(world, cid)

        tick_institutions(world)

        event = {"tick": world["tick"], "kind": "tick", "payload": {"character_count": len(world["characters"])}}
        log_event(world["tick"], "tick", None, None, event["payload"])
        push_recent_event(event)
        set_world_snapshot(world)
        await manager.broadcast(world)
        await asyncio.sleep(1.0)
