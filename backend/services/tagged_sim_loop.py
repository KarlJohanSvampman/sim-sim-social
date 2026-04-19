import asyncio

from services.llm_service import maybe_run_decision_llm
from services.state import get_world
from services.tagged_profile_store import TAGGED_CHARACTERS
from services.tagged_runtime import seed_default_tagged_characters
from services.ws import manager


def clamp(v, lo, hi):
    return max(lo, min(hi, v))


def _tile_key(x, y):
    return f"{x},{y}"


def _get_tile(world, x, y):
    return (world.get("grid", {}).get("tiles", {}) or {}).get(_tile_key(x, y))


def _is_walkable(world, x, y):
    tile = _get_tile(world, x, y)
    return bool(tile) and not tile.get("blocks_movement", False)


def _occupied_positions(exclude_id=None):
    out = set()
    for cid, c in TAGGED_CHARACTERS.items():
        if cid == exclude_id:
            continue
        out.add((c.position["x"], c.position["y"]))
    return out


def _pick_fallback_tile(world, character, prefer_far=False):
    occupied = _occupied_positions(character.profile.id)
    cx, cy = character.position["x"], character.position["y"]
    candidates = []
    for key, tile in (world.get("grid", {}).get("tiles", {}) or {}).items():
        x, y = tile["x"], tile["y"]
        if tile.get("blocks_movement"):
            continue
        if (x, y) in occupied:
            continue
        dist = abs(x - cx) + abs(y - cy)
        if dist == 0:
            continue
        candidates.append((dist, x, y))

    if not candidates:
        return {"x": cx, "y": cy}

    candidates.sort(reverse=prefer_far)
    _, x, y = candidates[0]
    return {"x": x, "y": y}


def _resolve_target_tile(world, character, action):
    target = action.get("target_tile") or {}
    tx = target.get("x")
    ty = target.get("y")
    if isinstance(tx, int) and isinstance(ty, int) and _is_walkable(world, tx, ty) and (tx, ty) not in _occupied_positions(character.profile.id):
        return {"x": tx, "y": ty}

    name = action.get("name", "")
    if name == "leave":
        return _pick_fallback_tile(world, character, prefer_far=True)
    return _pick_fallback_tile(world, character, prefer_far=False)


def _step_toward(world, character, target_tile):
    if not target_tile:
        return
    occupied = _occupied_positions(character.profile.id)
    cx, cy = character.position["x"], character.position["y"]
    tx, ty = target_tile["x"], target_tile["y"]

    if (cx, cy) == (tx, ty):
        return

    options = []
    for nx, ny in [(cx + 1, cy), (cx - 1, cy), (cx, cy + 1), (cx, cy - 1)]:
        if not _is_walkable(world, nx, ny):
            continue
        if (nx, ny) in occupied:
            continue
        dist = abs(tx - nx) + abs(ty - ny)
        options.append((dist, nx, ny))

    if not options:
        return

    options.sort(key=lambda t: t[0])
    _, nx, ny = options[0]
    character.position["x"] = nx
    character.position["y"] = ny


def tick_base_state(character):
    character.state.needs.hunger = min(100.0, character.state.needs.hunger + 0.12)
    character.state.needs.thirst = min(100.0, character.state.needs.thirst + 0.14)
    character.state.needs.bladder = min(100.0, character.state.needs.bladder + 0.10)
    character.state.needs.sleep = min(100.0, character.state.needs.sleep + 0.08)
    character.state.fatigue = min(100.0, character.state.fatigue + 0.04)

    character.state.emotional_temperature = clamp(
        getattr(character.state, "emotional_temperature", 20.0) * 0.995,
        0,
        100,
    )


def compute_social_layers(world):
    chars = TAGGED_CHARACTERS

    reputation = {}
    alliances = []
    rivalries = []

    for cid, c in chars.items():
        state = c.state

        rep = {
            "drama": state.drama_bias * state.emotional_temperature,
            "danger": state.aggression_bias * state.emotional_temperature,
            "stability": 100 - state.volatility * 100,
        }
        reputation[cid] = rep

    ids = list(chars.keys())

    for i in range(len(ids)):
        for j in range(i + 1, len(ids)):
            a = chars[ids[i]].state
            b = chars[ids[j]].state

            affinity_ab = a.affinity.get(ids[j], 0)
            affinity_ba = b.affinity.get(ids[i], 0)

            if affinity_ab > 25 and affinity_ba > 25:
                alliances.append({"members": [ids[i], ids[j]], "strength": (affinity_ab + affinity_ba) / 2})

            if affinity_ab < -10 or affinity_ba < -10:
                rivalries.append({"members": [ids[i], ids[j]]})

    world["reputation"] = reputation
    world["alliances"] = alliances
    world["rivalries"] = rivalries


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

    pending = {"name": name}
    if name in {"move", "leave"}:
        pending["target_tile"] = _resolve_target_tile(world, character, action)

    character.state.current_action_name = name
    character.state.pending_action = pending

    update_emotions(character, name)

    if utterance:
        character.state.spoken_text = utterance
        character.state.speech_expires_tick = world_tick + 30

    if target_character_id:
        character.state.conversation_partner_id = target_character_id
        character.state.awaiting_reply_from_id = target_character_id
        character.state.conversation_turns_remaining = 4


def progress_action(character, world_tick):
    pending = getattr(character.state, "pending_action", None)
    if not pending:
        return False

    world = get_world()
    name = pending.get("name")
    if name in {"move", "leave"}:
        _step_toward(world, character, pending.get("target_tile"))

    character.state.pending_action = None
    return False


async def tagged_sim_loop():
    seed_default_tagged_characters()
    world = get_world()

    while True:
        world["tick"] += 1

        compute_social_layers(world)

        for character in TAGGED_CHARACTERS.values():
            tick_base_state(character)

            if getattr(character.state, "speech_expires_tick", 0) and world["tick"] >= character.state.speech_expires_tick:
                character.state.spoken_text = ""

            progress_action(character, world["tick"])
            maybe_interrupt(character)

            force = bool(getattr(character.state, "awaiting_reply_from_id", ""))

            llm_result = maybe_run_decision_llm(character.model_dump(), world, force=force)
            if llm_result:
                apply_llm_action(character, llm_result, world["tick"])

        world["tagged_characters"] = {cid: c.model_dump() for cid, c in TAGGED_CHARACTERS.items()}

        await manager.broadcast(world)
        await asyncio.sleep(world.get("config", {}).get("tick_rate", 1.0))
