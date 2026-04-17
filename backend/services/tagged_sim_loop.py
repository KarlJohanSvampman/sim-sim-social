import asyncio

from services.llm_service import maybe_run_decision_llm
from services.state import get_world
from services.tagged_profile_store import TAGGED_CHARACTERS
from services.tagged_runtime import seed_default_tagged_characters
from services.ws import manager


def clamp(v, lo, hi):
    return max(lo, min(hi, v))


def tick_base_state(character):
    character.state.needs.hunger = min(100.0, character.state.needs.hunger + 0.12)
    character.state.needs.thirst = min(100.0, character.state.needs.thirst + 0.14)
    character.state.needs.bladder = min(100.0, character.state.needs.bladder + 0.10)
    character.state.needs.sleep = min(100.0, character.state.needs.sleep + 0.08)
    character.state.fatigue = min(100.0, character.state.fatigue + 0.04)

    # emotional drift
    character.state.emotional_temperature = clamp(
        getattr(character.state, "emotional_temperature", 20.0) * 0.995,
        0,
        100,
    )


def update_emotions(character, action_name):
    temp = getattr(character.state, "emotional_temperature", 20.0)
    if action_name in ["yell", "smash"]:
        temp += 10
    elif action_name == "gesture":
        temp += 4
    elif action_name == "relax":
        temp -= 8

    character.state.emotional_temperature = clamp(temp, 0, 100)
    character.state.escalation_level = int(character.state.emotional_temperature // 25)


def maybe_interrupt(character):
    # simple interruption chance
    for other in TAGGED_CHARACTERS.values():
        if other.profile.id == character.profile.id:
            continue
        if abs(other.position["x"] - character.position["x"]) <= 1 and abs(other.position["y"] - character.position["y"]) <= 1:
            if character.state.escalation_level >= 2:
                character.state.awaiting_reply_from_id = other.profile.id


def apply_llm_action(character, llm_result, world_tick):
    world = get_world()
    action = (llm_result or {}).get("action", {}) or {}

    name = action.get("name", "wait")
    utterance = action.get("utterance", "")
    target_character_id = action.get("target_character_id", "")

    character.state.current_action_name = name
    character.state.pending_action = {"name": name}

    update_emotions(character, name)

    if utterance:
        character.state.spoken_text = utterance
        character.state.speech_expires_tick = world_tick + 20

    if target_character_id:
        character.state.conversation_partner_id = target_character_id
        character.state.awaiting_reply_from_id = target_character_id
        character.state.conversation_turns_remaining = 4


def progress_action(character, world_tick):
    pending = getattr(character.state, "pending_action", None)
    if not pending:
        return False

    # end instantly for now (AI drives pacing)
    character.state.pending_action = None
    return False


async def tagged_sim_loop():
    seed_default_tagged_characters()
    world = get_world()

    while True:
        world["tick"] += 1

        for character in TAGGED_CHARACTERS.values():
            tick_base_state(character)

            if getattr(character.state, "speech_expires_tick", 0) and world["tick"] >= character.state.speech_expires_tick:
                character.state.spoken_text = ""

            maybe_interrupt(character)

            force = bool(getattr(character.state, "awaiting_reply_from_id", ""))

            llm_result = maybe_run_decision_llm(character.model_dump(), world, force=force)
            if llm_result:
                apply_llm_action(character, llm_result, world["tick"])

        world["tagged_characters"] = {cid: c.model_dump() for cid, c in TAGGED_CHARACTERS.items()}

        await manager.broadcast(world)
        await asyncio.sleep(world.get("config", {}).get("tick_rate", 1.0))
