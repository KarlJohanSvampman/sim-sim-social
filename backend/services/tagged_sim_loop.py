import asyncio
import random
from services.activity_engine import start_activity, tick_current_activity, interrupt_activity
from services.decision_engine_v2 import choose_action_v2, validate_decision_action, build_prompt_payload
from services.state import get_world
from services.tagged_profile_store import TAGGED_CHARACTERS
from services.tagged_runtime import seed_default_tagged_characters
from services.ws import manager
from services.roam_planner import choose_roam_destination
from services.roam_path import path_to
from services.speech_engine import pick_line

TRIGGER_DOUBLES = {(1,1), (2,2), (3,3), (4,4), (5,5), (6,6)}

def tick_base_state(character):
    character.state.needs.hunger = min(100.0, character.state.needs.hunger + 0.12)
    character.state.needs.thirst = min(100.0, character.state.needs.thirst + 0.14)
    character.state.needs.bladder = min(100.0, character.state.needs.bladder + 0.10)
    character.state.needs.sleep = min(100.0, character.state.needs.sleep + 0.08)
    character.state.fatigue = min(100.0, character.state.fatigue + 0.04)

def requirements_for_character(character) -> set[str]:
    return {"smartphone", "computer", "bed", "food", "restroom", "tv", "book", "stove"}

def sync_tagged_characters_into_world():
    world = get_world()
    world.setdefault("tagged_characters", {})
    world["tagged_characters"] = {}
    for char_id, character in TAGGED_CHARACTERS.items():
        world["tagged_characters"][char_id] = character.model_dump()

def roll_idle_dice(character):
    d1 = random.randint(1, 6)
    d2 = random.randint(1, 6)
    character.state.last_idle_roll = [d1, d2]
    character.state.roam_tiles_remaining = d1 + d2
    return d1, d2

def choose_and_store_roam_target(character):
    roam_budget = max(1, int(character.state.roam_tiles_remaining or 1))
    target = choose_roam_destination(character, roam_budget)
    character.state.roam_target = target
    character.state.roam_path = []
    if target:
        path = path_to(character.position["x"], character.position["y"], target["x"], target["y"])
        if len(path) > 1:
            character.state.roam_path = [{"x": x, "y": y, "z": 0} for x, y in path[1:]]
    return target

def maybe_set_speech(character, world_tick, text):
    character.state.spoken_text = text
    character.state.speech_expires_tick = world_tick + 5

def maybe_context_speech(character, world_tick, activity_tag=None, chance=0.2):
    if random.random() < chance:
        maybe_set_speech(character, world_tick, pick_line(character, activity_tag))

def clear_expired_speech(character, world_tick):
    if character.state.speech_expires_tick and world_tick >= character.state.speech_expires_tick:
        character.state.spoken_text = ""
        character.state.speech_expires_tick = 0

def roam_one_step(world, character):
    # Pause sometimes instead of moving every tick
    if character.state.dwell_ticks_remaining > 0:
        character.state.dwell_ticks_remaining -= 1
        character.state.mood = "pausing"
        return

    if character.state.move_cooldown_ticks > 0:
        character.state.move_cooldown_ticks -= 1
        character.state.mood = "walking_pause"
        return

    if not character.state.roam_path:
        choose_and_store_roam_target(character)

    if character.state.roam_path:
        step = character.state.roam_path.pop(0)
        character.position["x"] = step["x"]
        character.position["y"] = step["y"]
        character.state.roam_tiles_remaining = max(0, character.state.roam_tiles_remaining - 1)
        target = character.state.roam_target or {}
        room_tag = target.get("room_tag", "unknown")
        character.state.mood = f"roaming_to:{room_tag}"
        character.state.move_cooldown_ticks = 1  # move every other tick
        if random.random() < 0.18:
            character.state.dwell_ticks_remaining = random.randint(1, 3)
        if character.state.roam_tiles_remaining == 0:
            character.state.roam_target = None
            character.state.roam_path = []
            character.state.dwell_ticks_remaining = random.randint(1, 4)
        return

    character.state.roam_tiles_remaining = max(0, character.state.roam_tiles_remaining - 1)
    character.state.dwell_ticks_remaining = random.randint(1, 2)
    character.state.mood = "roaming"

async def tagged_sim_loop():
    seed_default_tagged_characters()
    world = get_world()
    while True:
        world["tick"] = world.get("tick", 0) + 1
        world.setdefault("calendar", {"year": 2026, "month": 4, "day": 16, "minute_of_day": 480})
        world["calendar"]["minute_of_day"] += 10
        if world["calendar"]["minute_of_day"] >= 1440:
            world["calendar"]["minute_of_day"] = 0
            world["calendar"]["day"] += 1
        for char_id, character in TAGGED_CHARACTERS.items():
            tick_base_state(character)
            clear_expired_speech(character, world["tick"])

            if character.state.current_activity is not None:
                tick_current_activity(character, world["tick"])
                activity = character.state.current_activity
                if activity:
                    character.state.mood = "busy"
                    maybe_context_speech(character, world["tick"], activity.tag, chance=0.35 if activity.tag in {"conversation", "phone_call"} else 0.15)
                else:
                    character.state.mood = "idle"
                    roll_idle_dice(character)
                    choose_and_store_roam_target(character)
                    character.state.dwell_ticks_remaining = random.randint(1, 3)
                continue

            if character.state.roam_tiles_remaining > 0:
                roam_one_step(world, character)
                if character.state.mood in {"pausing", "idle_pause", "walking_pause"}:
                    maybe_context_speech(character, world["tick"], None, chance=0.12)
                continue

            # pause at idle points before next decision/roll
            if character.state.dwell_ticks_remaining > 0:
                character.state.dwell_ticks_remaining -= 1
                character.state.mood = "idle_pause"
                maybe_context_speech(character, world["tick"], None, chance=0.2)
                continue

            d1, d2 = roll_idle_dice(character)
            choose_and_store_roam_target(character)

            available_requirements = requirements_for_character(character)
            prompt_payload = build_prompt_payload(character, available_requirements, world["tick"])
            decision = choose_action_v2(character, available_requirements, world["tick"])
            character.memory.append({"tick": world["tick"], "idle_roll": [d1, d2], "prompt_payload": prompt_payload, "decision": decision, "roam_target": character.state.roam_target})
            character.memory = character.memory[-25:]

            ok, reason = validate_decision_action(character, decision, available_requirements)
            if not ok:
                character.memory.append({"tick": world["tick"], "decision_rejected": reason})
                roam_one_step(world, character)
            else:
                action = decision["action"]
                if action["type"] == "engage_activity":
                    start_activity(character, world["tick"], action["activity_type"], action["tag"], float(action["hours"]), [], action.get("contacts", []))
                    character.state.mood = "busy"
                    character.state.roam_target = None
                    character.state.roam_path = []
                    maybe_set_speech(character, world["tick"], pick_line(character, action["tag"]))
                elif action["type"] == "interrupt_activity":
                    interrupt_activity(character, action.get("reason", "unknown"))
                elif action["type"] == "wander":
                    roam_one_step(world, character)

        sync_tagged_characters_into_world()
        await manager.broadcast(world)
        await asyncio.sleep(1.0)
