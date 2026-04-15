import asyncio
import random
from services.activity_engine import start_activity, tick_current_activity, interrupt_activity
from services.decision_engine_v2 import choose_action_v2, validate_decision_action, build_prompt_payload
from services.state import get_world
from services.tagged_profile_store import TAGGED_CHARACTERS
from services.tagged_runtime import seed_default_tagged_characters
from services.ws import manager

TRIGGER_DOUBLES = {(1,1), (4,4), (6,6)}

def tick_base_state(character):
    character.state.needs.hunger = min(100.0, character.state.needs.hunger + 0.15)
    character.state.needs.thirst = min(100.0, character.state.needs.thirst + 0.18)
    character.state.needs.bladder = min(100.0, character.state.needs.bladder + 0.12)
    character.state.needs.sleep = min(100.0, character.state.needs.sleep + 0.10)
    character.state.fatigue = min(100.0, character.state.fatigue + 0.05)

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

def valid_neighbors(world, x, y):
    candidates = [(x+1,y), (x-1,y), (x,y+1), (x,y-1)]
    out = []
    for nx, ny in candidates:
        tile = world["grid"]["tiles"].get(f"{nx},{ny}")
        if tile and not tile.get("blocks_movement"):
            out.append((nx, ny))
    return out

def roam_one_step(world, character):
    pos = character.position
    neighbors = valid_neighbors(world, pos["x"], pos["y"])
    if not neighbors:
        character.state.roam_tiles_remaining = 0
        return
    nx, ny = random.choice(neighbors)
    pos["x"], pos["y"] = nx, ny
    character.state.roam_tiles_remaining = max(0, character.state.roam_tiles_remaining - 1)
    character.state.mood = "roaming"

async def tagged_sim_loop():
    seed_default_tagged_characters()
    world = get_world()
    while True:
        world["tick"] = world.get("tick", 0) + 1
        for char_id, character in TAGGED_CHARACTERS.items():
            tick_base_state(character)

            if character.state.current_activity is not None:
                tick_current_activity(character, world["tick"])
                character.state.mood = "busy" if character.state.current_activity else "idle"
                if character.state.current_activity is None:
                    roll_idle_dice(character)
                continue

            if character.state.roam_tiles_remaining > 0:
                roam_one_step(world, character)
                continue

            d1, d2 = roll_idle_dice(character)
            if (d1, d2) not in TRIGGER_DOUBLES:
                roam_one_step(world, character)
                continue

            available_requirements = requirements_for_character(character)
            prompt_payload = build_prompt_payload(character, available_requirements, world["tick"])
            decision = choose_action_v2(character, available_requirements, world["tick"])
            character.memory.append({"tick": world["tick"], "idle_roll": [d1, d2], "prompt_payload": prompt_payload, "decision": decision})
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
                elif action["type"] == "interrupt_activity":
                    interrupt_activity(character, action.get("reason", "unknown"))
                elif action["type"] == "wander":
                    roam_one_step(world, character)

        sync_tagged_characters_into_world()
        await manager.broadcast(world)
        await asyncio.sleep(1.0)
