import asyncio

from services.llm_service import maybe_run_decision_llm
from services.state import get_world
from services.tagged_profile_store import TAGGED_CHARACTERS
from services.tagged_runtime import seed_default_tagged_characters
from services.ws import manager


async def tagged_sim_loop():
    seed_default_tagged_characters()
    world = get_world()

    while True:
        world["tick"] += 1

        for character in TAGGED_CHARACTERS.values():
            llm_result = await maybe_run_decision_llm(character.model_dump(), world)
            if llm_result:
                character.state.current_action_name = llm_result.get("action", {}).get("name", "wait")

        world["tagged_characters"] = {cid: c.model_dump() for cid, c in TAGGED_CHARACTERS.items()}

        await manager.broadcast(world)
        await asyncio.sleep(world.get("config", {}).get("tick_rate", 1.0))
