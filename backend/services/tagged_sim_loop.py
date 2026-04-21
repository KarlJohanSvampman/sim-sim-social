import asyncio
from services.llm_service import maybe_run_decision_llm
from services.state import get_world, get_world_snapshot
from services.tagged_profile_store import TAGGED_CHARACTERS
from services.tagged_runtime import seed_default_tagged_characters
from services.ws import manager


def _tile_at(world, x, y):
    return (world.get("grid", {}).get("tiles", {}) or {}).get(f"{x},{y}")


def _is_walkable(world, x, y, mover_id=None):
    tile = _tile_at(world, x, y)
    if not tile:
        return False
    if tile.get("blocks_movement", False):
        return False
    for c in TAGGED_CHARACTERS.values():
        if mover_id and c.profile.id == mover_id:
            continue
        if c.position["x"] == x and c.position["y"] == y:
            return False
    return True


def _get_action_def(world, action_name):
    for action in (world.get("action_definitions", {}) or {}).values():
        if action.get("name") == action_name:
            return action
    return None


def _apply_motivator_effects(c, action_name, world):
    action_def = _get_action_def(world, action_name)
    if not action_def:
        return
    for tag in action_def.get("motivator_tags", []):
        if tag in c.state.weekly_motivators:
            c.state.weekly_motivators[tag] = 0.0


def _update_motivators(c):
    for k in c.state.weekly_motivators:
        c.state.weekly_motivators[k] = min(100.0, c.state.weekly_motivators[k] + 0.2)


def _decay_grudges(c):
    new_grudges = []
    for g in c.state.grudges:
        try:
            g.intensity *= 0.995
            if g.intensity > 1.0:
                new_grudges.append(g)
        except Exception:
            pass
    c.state.grudges = new_grudges


def _handle_weekly_reset(world):
    calendar = world.get("calendar", {})
    minute = calendar.get("minute_of_day", 0)
    day = calendar.get("day", 1)
    if minute != 0:
        return
    if day % 7 != 0:
        return
    for c in TAGGED_CHARACTERS.values():
        for k in c.state.weekly_motivators:
            c.state.weekly_motivators[k] = 0.0


def _advance_calendar(world):
    calendar = world.setdefault("calendar", {"year": 2026, "month": 4, "day": 16, "minute_of_day": 480})
    calendar["minute_of_day"] = int(calendar.get("minute_of_day", 0)) + 10
    if calendar["minute_of_day"] >= 1440:
        calendar["minute_of_day"] = 0
        calendar["day"] = int(calendar.get("day", 1)) + 1


def _handle_jobs(world):
    world.setdefault("offmap", [])
    now = world.get("calendar", {}).get("minute_of_day", 0)

    # send to work
    for cid, c in list(TAGGED_CHARACTERS.items()):
        if getattr(c.state, "is_offmap", False):
            continue
        if getattr(c.state, "job_id", "") and now == getattr(c.state, "work_start_minute", -1):
            duration_minutes = max(60, int(getattr(c.state, "work_duration_minutes", 480) or 480))
            ticks_away = max(1, duration_minutes // 10)
            world["offmap"].append({
                "character_id": cid,
                "return_tick": world["tick"] + ticks_away,
                "hourly_wage": float(getattr(c.state, "hourly_wage", 10.0) or 10.0),
                "minutes_worked": duration_minutes,
                "household_id": getattr(c.state, "household_id", ""),
            })
            c.state.is_offmap = True
            del TAGGED_CHARACTERS[cid]

    # return from work
    for entry in list(world["offmap"]):
        if entry.get("return_tick", 0) > world["tick"]:
            continue
        seed_default_tagged_characters()
        cid = entry.get("character_id")
        if cid in TAGGED_CHARACTERS:
            c = TAGGED_CHARACTERS[cid]
            c.state.is_offmap = False
            household_id = entry.get("household_id") or getattr(c.state, "household_id", "")
            c.state.household_id = household_id
            if household_id and household_id in world.get("households", {}):
                earnings = entry.get("hourly_wage", 0.0) * (entry.get("minutes_worked", 0) / 60.0)
                world["households"][household_id]["balance"] += earnings
            c.memory.append({
                "kind": "work",
                "text": "Worked a shift and came home.",
                "tick": world["tick"]
            })
            c.memory = c.memory[-20:]
            # respawn near household entrance
            if household_id == "house_1":
                c.position = {"x": 6, "y": 6, "z": 0}
            elif household_id == "house_2":
                c.position = {"x": 13, "y": 6, "z": 0}
        world["offmap"].remove(entry)


def step_toward(world, c, tx, ty):
    cx, cy = c.position["x"], c.position["y"]
    if (cx, cy) == (tx, ty):
        return True

    candidates = []
    if cx < tx:
        candidates.append((cx + 1, cy))
    elif cx > tx:
        candidates.append((cx - 1, cy))
    if cy < ty:
        candidates.append((cx, cy + 1))
    elif cy > ty:
        candidates.append((cx, cy - 1))

    for nx, ny in [(cx + 1, cy), (cx - 1, cy), (cx, cy + 1), (cx, cy - 1)]:
        if (nx, ny) not in candidates:
            candidates.append((nx, ny))

    best = None
    best_d = 10**9
    for nx, ny in candidates:
        if not _is_walkable(world, nx, ny, mover_id=c.profile.id):
            continue
        d = abs(tx - nx) + abs(ty - ny)
        if d < best_d:
            best_d = d
            best = (nx, ny)

    if best is None:
        return False

    c.position["x"], c.position["y"] = best
    return True


def nearest_other(c):
    best = None
    best_d = 1e9
    for o in TAGGED_CHARACTERS.values():
        if o is c:
            continue
        dx = o.position["x"] - c.position["x"]
        dy = o.position["y"] - c.position["y"]
        d = dx * dx + dy * dy
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
    world.setdefault("offmap", [])

    while True:
        world["tick"] += 1
        _advance_calendar(world)
        _handle_weekly_reset(world)
        _handle_jobs(world)

        for c in TAGGED_CHARACTERS.values():
            _update_motivators(c)
            _decay_grudges(c)
            if getattr(c.state, "speech_expires_tick", 0) and world["tick"] >= c.state.speech_expires_tick:
                c.state.spoken_text = ""
                c.state.speech_expires_tick = 0

        face_each_other()

        for c in TAGGED_CHARACTERS.values():
            pending = c.state.pending_action or {}

            if pending.get("name") == "move":
                tgt = pending.get("target_tile") or {}
                tx, ty = tgt.get("x", c.position["x"]), tgt.get("y", c.position["y"])
                if (c.position["x"], c.position["y"]) != (tx, ty):
                    moved = step_toward(world, c, tx, ty)
                    if moved:
                        c.state.current_action_name = "move"
                        _apply_motivator_effects(c, "move", world)
                        continue
                    c.state.pending_action = None
                    c.state.current_action_name = "wait"
                else:
                    c.state.pending_action = None

            res = await maybe_run_decision_llm(c.model_dump(), world)
            if not res:
                continue

            act = res.get("action", {})
            name = act.get("name", "wait")

            if c.state.conversation_partner_id and name == "move":
                name = "wait"

            if name in ["speak", "yell", "gesture"] and not act.get("target_character_id"):
                other = nearest_other(c)
                if other:
                    act["target_character_id"] = other.profile.id

            if name == "move":
                tgt = act.get("target_tile") or {"x": c.position["x"], "y": c.position["y"]}
                if _is_walkable(world, tgt.get("x", c.position["x"]), tgt.get("y", c.position["y"]), mover_id=c.profile.id):
                    c.state.pending_action = {"name": "move", "target_tile": tgt}
                    step_toward(world, c, tgt.get("x", 0), tgt.get("y", 0))
                    _apply_motivator_effects(c, "move", world)
                else:
                    name = "wait"

            if name in ["speak", "yell"]:
                utt = (act.get("utterance") or "").strip()
                if not utt:
                    c.state.current_action_name = "wait"
                    continue

                c.state.spoken_text = utt
                c.state.speech_expires_tick = world["tick"] + 12
                c.state.conversation_turns_remaining = max(c.state.conversation_turns_remaining, 3)
                _apply_motivator_effects(c, name, world)

            if name in ["gesture", "leave", "smash", "observe", "relax", "study", "wait"]:
                _apply_motivator_effects(c, name, world)

            tgt_id = act.get("target_character_id") or ""
            if tgt_id and tgt_id in TAGGED_CHARACTERS:
                c.state.conversation_partner_id = tgt_id
                target = TAGGED_CHARACTERS[tgt_id]
                target.state.conversation_partner_id = c.profile.id
                target.state.awaiting_reply_from_id = c.profile.id
                target.state.conversation_turns_remaining = max(target.state.conversation_turns_remaining, 3)

            if c.state.conversation_turns_remaining > 0:
                c.state.conversation_turns_remaining -= 1
                if c.state.conversation_turns_remaining == 0:
                    c.state.conversation_partner_id = ""
                    c.state.awaiting_reply_from_id = ""

            c.state.current_action_name = name

        world["tagged_characters"] = {cid: c.model_dump() for cid, c in TAGGED_CHARACTERS.items()}
        await manager.broadcast(get_world_snapshot())
        await asyncio.sleep(world.get("config", {}).get("tick_rate", 1.0))
