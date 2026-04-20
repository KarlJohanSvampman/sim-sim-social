import asyncio
from services.llm_service import maybe_run_decision_llm
from services.state import get_world, get_world_snapshot
from services.tagged_profile_store import TAGGED_CHARACTERS
from services.tagged_runtime import seed_default_tagged_characters
from services.ws import manager

def update_motivators(c):
    for k in c.state.weekly_motivators:
        c.state.weekly_motivators[k] = min(100, c.state.weekly_motivators[k] + 0.2)


def decay_grudges(c):
    new = []
    for g in c.state.grudges:
        g["intensity"] *= 0.995
        if g["intensity"] > 1:
            new.append(g)
    c.state.grudges = new


def handle_jobs(world):
    world.setdefault("offmap", [])

    # send to work
    for cid, c in list(TAGGED_CHARACTERS.items()):
        now = world["calendar"]["minute_of_day"]

        if getattr(c.state, "job_id", None) and now == getattr(c.state, "work_start_minute", -1):
            world["offmap"].append({
                "character_id": cid,
                "return_tick": world["tick"] + 200,
                "hourly_wage": getattr(c.state, "hourly_wage", 10)
            })
            del TAGGED_CHARACTERS[cid]

    # return from work
    for entry in list(world["offmap"]):
        if entry["return_tick"] <= world["tick"]:
            seed_default_tagged_characters()
            cid = entry["character_id"]

            if cid in TAGGED_CHARACTERS:
                c = TAGGED_CHARACTERS[cid]
                h = world["households"].get(c.state.household_id)

                if h:
                    h["balance"] += entry["hourly_wage"] * 8

                c.memory.append({
                    "kind": "work",
                    "text": "Worked a shift",
                    "tick": world["tick"]
                })

            world["offmap"].remove(entry)

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

    # fallback orthogonal options so they do not just ram walls forever
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

    while True:
        world["tick"] += 1
        handle_jobs(world)

        for c in TAGGED_CHARACTERS.values():
            update_motivators(c)
            decay_grudges(c)
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
                # reject impossible targets early
                if _is_walkable(world, tgt.get("x", c.position["x"]), tgt.get("y", c.position["y"]), mover_id=c.profile.id):
                    c.state.pending_action = {"name": "move", "target_tile": tgt}
                    step_toward(world, c, tgt.get("x", 0), tgt.get("y", 0))
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
