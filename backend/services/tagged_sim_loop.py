import asyncio

from services.llm_service import maybe_run_decision_llm
from services.state import get_world
from services.tagged_profile_store import TAGGED_CHARACTERS
from services.tagged_runtime import seed_default_tagged_characters
from services.ws import manager


def tick_base_state(character):
    character.state.needs.hunger = min(100.0, character.state.needs.hunger + 0.12)
    character.state.needs.thirst = min(100.0, character.state.needs.thirst + 0.14)
    character.state.needs.bladder = min(100.0, character.state.needs.bladder + 0.10)
    character.state.needs.sleep = min(100.0, character.state.needs.sleep + 0.08)
    character.state.fatigue = min(100.0, character.state.fatigue + 0.04)


def sync_tagged_characters_into_world():
    world = get_world()
    world.setdefault("tagged_characters", {})
    world["tagged_characters"] = {}
    for char_id, character in TAGGED_CHARACTERS.items():
        world["tagged_characters"][char_id] = character.model_dump()


def maybe_set_speech(character, world_tick, text):
    if not text:
        return
    character.state.spoken_text = text
    character.state.speech_expires_tick = world_tick + 12


def clear_expired_speech(character, world_tick):
    if getattr(character.state, "speech_expires_tick", 0) and world_tick >= character.state.speech_expires_tick:
        character.state.spoken_text = ""
        character.state.speech_expires_tick = 0


def store_conversation(speaker, listener, text, world_tick):
    if not text:
        return
    entry = {"tick": world_tick, "from": speaker.profile.id, "to": listener.profile.id, "text": text}
    speaker.conversation_history.append(entry)
    listener.conversation_history.append(entry)
    speaker.conversation_history = speaker.conversation_history[-20:]
    listener.conversation_history = listener.conversation_history[-20:]


def secs_to_ticks(world, seconds: int) -> int:
    tick_rate = float(world.get("config", {}).get("tick_rate", 1.0))
    if tick_rate <= 0:
        tick_rate = 1.0
    return max(1, int(round(seconds / tick_rate)))


def occupied_positions(exclude_id=None):
    occ = {}
    for cid, c in TAGGED_CHARACTERS.items():
        if cid == exclude_id:
            continue
        occ[(c.position["x"], c.position["y"])] = cid
    return occ


def step_toward(character, target, exclude_id=None):
    if not target:
        return
    world = get_world()
    x, y = character.position["x"], character.position["y"]
    tx, ty = int(target.get("x", x)), int(target.get("y", y))
    candidates = []
    if tx > x:
        candidates.append((x + 1, y))
    elif tx < x:
        candidates.append((x - 1, y))
    if ty > y:
        candidates.append((x, y + 1))
    elif ty < y:
        candidates.append((x, y - 1))
    candidates += [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]

    occ = occupied_positions(exclude_id=exclude_id)
    for nx, ny in candidates:
        tile = world["grid"]["tiles"].get(f"{nx},{ny}")
        if not tile or tile.get("blocks_movement"):
            continue
        if (nx, ny) in occ:
            continue
        character.position["x"], character.position["y"] = nx, ny
        return


def face_target(character, target_character_id):
    target = TAGGED_CHARACTERS.get(target_character_id)
    if not target:
        return
    character.state.current_intention = f"facing:{target_character_id}"


def apply_llm_action(character, llm_result, world_tick):
    world = get_world()
    action = (llm_result or {}).get("action", {}) or {}
    name = action.get("name", "wait")
    intention = str(action.get("intention", "") or "")
    pre_delay = max(1, min(15, int(action.get("pre_action_delay", 2))))
    duration_seconds = max(1, min(60, int(action.get("duration_seconds", 4))))
    post_delay = max(1, min(15, int(action.get("post_action_delay", 2))))
    utterance = str(action.get("utterance", "") or "")
    target_character_id = str(action.get("target_character_id", "") or "")
    target_tile = action.get("target_tile") or {}

    character.state.current_action_name = name
    character.state.current_intention = intention
    character.state.action_phase = "pre"
    character.state.action_delay_ticks_remaining = secs_to_ticks(world, pre_delay)
    character.state.pending_action = {
        "name": name,
        "target_character_id": target_character_id,
        "target_tile": target_tile,
        "utterance": utterance,
        "duration_seconds": duration_seconds,
        "post_action_delay": post_delay,
    }

    if utterance:
        maybe_set_speech(character, world_tick, utterance)

    if name == "speak" and target_character_id:
        target = TAGGED_CHARACTERS.get(target_character_id)
        if target:
            store_conversation(character, target, utterance, world_tick)


def progress_action(character, world_tick):
    pending = getattr(character.state, "pending_action", None)
    if not pending:
        return False

    if character.state.action_delay_ticks_remaining > 0:
        character.state.action_delay_ticks_remaining -= 1
        return True

    if character.state.action_phase == "pre":
        character.state.action_phase = "active"
        character.state.action_delay_ticks_remaining = secs_to_ticks(get_world(), int(pending.get("duration_seconds", 4)))
        character.state.mood = f"doing:{pending.get('name', 'wait')}"

        name = pending.get("name")
        if name == "speak" and pending.get("target_character_id"):
            face_target(character, pending["target_character_id"])
            target = TAGGED_CHARACTERS.get(pending["target_character_id"])
            if target:
                target.state.current_action_name = "speak"
                target.state.current_intention = f"talking_with:{character.profile.id}"
                target.state.action_phase = "active"
                target.state.action_delay_ticks_remaining = max(
                    getattr(target.state, "action_delay_ticks_remaining", 0),
                    secs_to_ticks(get_world(), int(pending.get("duration_seconds", 4)))
                )
                maybe_set_speech(target, world_tick, f"(listening to {character.profile.name})")
        elif name == "move":
            step_toward(character, pending.get("target_tile") or {}, exclude_id=character.profile.id)
        return True

    if character.state.action_phase == "active":
        character.state.action_phase = "post"
        character.state.action_delay_ticks_remaining = secs_to_ticks(get_world(), int(pending.get("post_action_delay", 2)))
        return True

    if character.state.action_phase == "post":
        character.state.action_phase = "idle"
        character.state.current_action_name = ""
        character.state.current_intention = ""
        character.state.pending_action = None
        return False

    return False


async def tagged_sim_loop():
    seed_default_tagged_characters()
    world = get_world()
    while True:
        world["tick"] = world.get("tick", 0) + 1

        for char_id, character in TAGGED_CHARACTERS.items():
            tick_base_state(character)
            clear_expired_speech(character, world["tick"])

            if progress_action(character, world["tick"]):
                continue

            llm_result = maybe_run_decision_llm(character.model_dump(), world)
            if llm_result:
                character.memory.append({"tick": world["tick"], "llm_result": llm_result})
                character.memory = character.memory[-40:]
                apply_llm_action(character, llm_result, world["tick"])

        sync_tagged_characters_into_world()
        await manager.broadcast(world)
        await asyncio.sleep(world.get("config", {}).get("tick_rate", 1.0))
