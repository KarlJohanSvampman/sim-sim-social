import asyncio
from services.llm_service import maybe_run_decision_llm
from services.state import get_world, get_world_snapshot
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


def nearest_other(c):
    best = None
    best_d = 1e9
    for o in TAGGED_CHARACTERS.values():
        if o is c:
            continue
        dx = o.position["x"] - c.position["x"]
        dy = o.position["y"] - c.position["y"]
        d = dx*dx + dy*dy
        if d < best_d:
            best_d = d
            best = o
    return best


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

        # expire speech bubbles
        for c in TAGGED_CHARACTERS.values():
            if getattr(c.state, "speech_expires_tick", 0) and world["tick"] >= c.state.speech_expires_tick:
                c.state.spoken_text = ""
                c.state.speech_expires_tick = 0

        face_each_other()

        for c in TAGGED_CHARACTERS.values():
            # continue existing movement without re-calling LLM
            pending = c.state.pending_action or {}
            if pending.get("name") == "move":
                tgt = pending.get("target_tile") or {}
                tx, ty = tgt.get("x", c.position["x"]), tgt.get("y", c.position["y"])
                if (c.position["x"], c.position["y"]) != (tx, ty):
                    step_toward(c, tx, ty)
                    c.state.current_action_name = "move"
                    continue
                else:
                    c.state.pending_action = None

            res = await maybe_run_decision_llm(c.model_dump(), world)
            if not res:
                continue

            act = res.get("action", {})
            name = act.get("name", "wait")

            # prevent walking during conversation unless leaving
            if c.state.conversation_partner_id and name == "move":
                name = "wait"

            # auto-pick a target for social actions
            if name in ["speak", "yell", "gesture"] and not act.get("target_character_id"):
                other = nearest_other(c)
                if other:
                    act["target_character_id"] = other.profile.id

            # movement persists until target reached
            if name == "move":
                tgt = act.get("target_tile") or {"x": c.position["x"], "y": c.position["y"]}
                c.state.pending_action = {"name": "move", "target_tile": tgt}
                step_toward(c, tgt.get("x", 0), tgt.get("y", 0))

            # speaking
            if name in ["speak", "yell"]:
                utt = (act.get("utterance") or "").strip()
                if utt:
                    c.state.spoken_text = utt
                    c.state.speech_expires_tick = world["tick"] + 6  # ~6 ticks visible
                    c.state.conversation_turns_remaining = max(c.state.conversation_turns_remaining, 3)
                else:
                    name = "wait"

            # set conversation partner
            tgt_id = act.get("target_character_id") or ""
            if tgt_id and tgt_id in TAGGED_CHARACTERS:
                c.state.conversation_partner_id = tgt_id
                # make it mutual for better back-and-forth
                TAGGED_CHARACTERS[tgt_id].state.conversation_partner_id = c.profile.id

            # countdown conversation
            if c.state.conversation_turns_remaining > 0:
                c.state.conversation_turns_remaining -= 1
                if c.state.conversation_turns_remaining == 0:
                    c.state.conversation_partner_id = ""

            c.state.current_action_name = name

        world["tagged_characters"] = {cid: c.model_dump() for cid, c in TAGGED_CHARACTERS.items()}

        # broadcast a clean snapshot to ensure frontend updates (tick, etc.)
        await manager.broadcast(get_world_snapshot())
        await asyncio.sleep(world.get("config", {}).get("tick_rate", 1.0))
