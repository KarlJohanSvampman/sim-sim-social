import asyncio

from services.llm_service import maybe_run_decision_llm
from services.state import get_world
from services.tagged_profile_store import TAGGED_CHARACTERS
from services.tagged_runtime import seed_default_tagged_characters
from services.ws import manager


def step_toward(c, tx, ty):
    cx, cy = c.position["x"], c.position["y"]
    if cx < tx: cx += 1
    elif cx > tx: cx -= 1
    elif cy < ty: cy += 1
    elif cy > ty: cy -= 1
    c.position["x"], c.position["y"] = cx, cy


def face_each_other():
    for c in TAGGED_CHARACTERS.values():
        pid = c.state.conversation_partner_id
        if not pid or pid not in TAGGED_CHARACTERS:
            continue
        other = TAGGED_CHARACTERS[pid]
        dx = other.position["x"] - c.position["x"]
        dy = other.position["y"] - c.position["y"]
        c.state.facing = {"x": dx, "y": dy}


async def tagged_sim_loop():
    seed_default_tagged_characters()
    world = get_world()

    while True:
        world["tick"] += 1

        face_each_other()

        for c in TAGGED_CHARACTERS.values():
            res = await maybe_run_decision_llm(c.model_dump(), world)
            if not res:
                continue

            act = res.get("action", {})
            name = act.get("name", "wait")

            if c.state.conversation_partner_id and name == "move":
                name = "wait"

            if name == "move":
                tgt = act.get("target_tile") or {"x": c.position["x"], "y": c.position["y"]}
                step_toward(c, tgt.get("x",0), tgt.get("y",0))

            if name in ["speak","yell"]:
                c.state.spoken_text = act.get("utterance", "...")
                c.state.conversation_turns_remaining = max(c.state.conversation_turns_remaining, 3)

            if act.get("target_character_id"):
                c.state.conversation_partner_id = act["target_character_id"]

            if c.state.conversation_turns_remaining > 0:
                c.state.conversation_turns_remaining -= 1
                if c.state.conversation_turns_remaining == 0:
                    c.state.conversation_partner_id = ""

            c.state.current_action_name = name

        world["tagged_characters"] = {cid: c.model_dump() for cid, c in TAGGED_CHARACTERS.items()}

        await manager.broadcast(world)
        await asyncio.sleep(world.get("config", {}).get("tick_rate", 1.0))
