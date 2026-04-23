import asyncio
from services.llm_service import maybe_run_decision_llm
from services.state import get_world, get_world_snapshot
from services.tagged_profile_store import TAGGED_CHARACTERS
from services.tagged_runtime import seed_default_tagged_characters
from services.ws import manager


EMOTION_TO_ACTION_MOOD = {
    "calm": "calm",
    "playful": "playful",
    "warm": "calm",
    "awkward": "sad",
    "annoyed": "annoyed",
    "angry": "angry",
    "furious": "furious",
    "fearful": "sad",
    "sad": "sad",
    "smug": "smug",
    "curious": "playful",
    "suspicious": "annoyed",
}


def _tile_at(world: dict, x: int, y: int) -> dict | None:
    return (world.get("grid", {}).get("tiles", {}) or {}).get(f"{x},{y}")


def _is_walkable(world: dict, x: int, y: int, mover_id: str | None = None) -> bool:
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


def _get_action_def(world: dict, action_name: str) -> dict | None:
    for action in (world.get("action_definitions", {}) or {}).values():
        if action.get("name") == action_name:
            return action
    return None


def _apply_motivator_effects(c, action_name: str, world: dict) -> None:
    action_def = _get_action_def(world, action_name)
    if not action_def:
        return
    for tag in action_def.get("motivator_tags", []):
        if tag in c.state.weekly_motivators:
            c.state.weekly_motivators[tag] = 0.0


def _update_motivators(c) -> None:
    for k in c.state.weekly_motivators:
        c.state.weekly_motivators[k] = min(100.0, c.state.weekly_motivators[k] + 0.2)


def _decay_grudges(c) -> None:
    new_grudges = []
    for g in c.state.grudges:
        try:
            g.intensity *= 0.995
            if g.intensity > 1.0:
                new_grudges.append(g)
        except Exception:
            pass
    c.state.grudges = new_grudges


def _memory_importance(memory: dict) -> float:
    importance = float(memory.get("importance", 0.5) or 0.5)
    speech_act = str(memory.get("speech_act", "") or "")
    source = str(memory.get("source", "direct") or "direct")
    if speech_act == "insult":
        importance += 0.35
    elif speech_act == "threat":
        importance += 0.45
    elif speech_act == "request":
        importance += 0.10
    elif speech_act == "question":
        importance += 0.05
    if source == "gossip":
        importance -= 0.10
    return max(0.05, min(1.0, importance))


def _remember(c, memory: dict) -> None:
    normalized = dict(memory)
    normalized["importance"] = _memory_importance(normalized)
    normalized.setdefault("source", "direct")
    c.memory.append(normalized)
    c.memory = c.memory[-80:]


def _decay_memories(c, current_tick: int) -> None:
    kept = []
    for m in c.memory:
        if not isinstance(m, dict):
            continue
        age = max(0, current_tick - int(m.get("tick", current_tick) or current_tick))
        importance = float(m.get("importance", 0.5) or 0.5)
        decay = 0.003 if m.get("source") == "direct" else 0.005
        importance = max(0.0, importance - (age * decay / 10.0))
        m["importance"] = importance
        if importance >= 0.08:
            kept.append(m)
    c.memory = kept[-80:]


def _nearby_observers(source, target, radius: int = 4):
    observers = []
    sx, sy = source.position["x"], source.position["y"]
    tx, ty = target.position["x"], target.position["y"]
    mx = (sx + tx) / 2.0
    my = (sy + ty) / 2.0
    for other in TAGGED_CHARACTERS.values():
        if other is source or other is target:
            continue
        dist = abs(other.position["x"] - mx) + abs(other.position["y"] - my)
        if dist <= radius:
            observers.append(other)
    return observers


def _propagate_gossip(source, target, utt: str, speech_act: str, topic: str, tick: int) -> None:
    about = target.profile.id if speech_act in ["insult", "threat"] else source.profile.id
    gossip_keywords = []
    if speech_act == "insult":
        gossip_keywords = ["hostile", "dramatic"]
    elif speech_act == "threat":
        gossip_keywords = ["dangerous", "threatening"]
    elif speech_act in ["question", "statement", "request"]:
        gossip_keywords = ["talkative"]

    for observer in _nearby_observers(source, target):
        _remember(observer, {
            "kind": "gossip",
            "target": source.profile.id,
            "about": about,
            "text": utt,
            "speech_act": speech_act,
            "topic": topic,
            "source": "gossip",
            "tick": tick,
            "importance": 0.35,
        })
        if gossip_keywords:
            _add_or_update_subjective_view(observer, "character", about, gossip_keywords, tick)


def _handle_weekly_reset(world: dict) -> None:
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


def _advance_calendar(world: dict) -> None:
    calendar = world.setdefault("calendar", {"year": 2026, "month": 4, "day": 16, "minute_of_day": 480})
    calendar["minute_of_day"] = int(calendar.get("minute_of_day", 0)) + 10
    if calendar["minute_of_day"] >= 1440:
        calendar["minute_of_day"] = 0
        calendar["day"] = int(calendar.get("day", 1)) + 1


def _handle_jobs(world: dict) -> None:
    world.setdefault("offmap", [])
    now = world.get("calendar", {}).get("minute_of_day", 0)
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
            _remember(c, {"kind": "work", "text": "Worked a shift and came home.", "tick": world["tick"], "importance": 0.45})
            if household_id == "house_1":
                c.position = {"x": 6, "y": 6, "z": 0}
            elif household_id == "house_2":
                c.position = {"x": 13, "y": 6, "z": 0}
        world["offmap"].remove(entry)


def step_toward(world: dict, c, tx: int, ty: int) -> bool:
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


def _view_keywords_for_subject(c, subject_ref: str) -> list[str]:
    out = []
    for view in getattr(c, "subjective_views", []):
        try:
            if getattr(view, "subject_ref", "") == subject_ref:
                out.extend(list(getattr(view, "keywords", []) or []))
            elif isinstance(view, dict) and view.get("subject_ref") == subject_ref:
                out.extend(list(view.get("keywords", []) or []))
        except Exception:
            pass
    return list(dict.fromkeys(out))[:12]


def _grudge_intensity_against(c, target_id: str) -> float:
    total = 0.0
    for g in c.state.grudges:
        try:
            if g.target_character_id == target_id:
                total += float(g.intensity)
        except Exception:
            pass
    return total


def _update_social_bias_lists(c) -> None:
    avoid_ids = set()
    feared_ids = set()
    for other in TAGGED_CHARACTERS.values():
        if other is c:
            continue
        grudge = _grudge_intensity_against(c, other.profile.id)
        kws = _view_keywords_for_subject(c, other.profile.id)
        if grudge >= 18 or any(k in kws for k in ["annoying", "hostile", "untrustworthy"]):
            avoid_ids.add(other.profile.id)
        if grudge >= 30 or any(k in kws for k in ["threatening", "dangerous"]):
            feared_ids.add(other.profile.id)
    c.state.avoid_character_ids = sorted(avoid_ids)
    c.state.feared_character_ids = sorted(feared_ids)


def pick_social_target(c):
    best = None
    best_score = -10**9

    for o in TAGGED_CHARACTERS.values():
        if o is c:
            continue

        score = 0.0
        score += float(c.state.affinity.get(o.profile.id, 0.0)) * 1.2
        grudge = _grudge_intensity_against(c, o.profile.id)
        score -= grudge * 1.5

        if c.state.household_id and c.state.household_id == o.state.household_id:
            score += 12.0

        kws = _view_keywords_for_subject(c, o.profile.id)
        positive_kws = {"nice", "warm", "interesting", "fun", "loyal", "kind"}
        negative_kws = {"annoying", "threatening", "untrustworthy", "hostile", "boring", "weird"}
        score += len([k for k in kws if k in positive_kws]) * 4.0
        score -= len([k for k in kws if k in negative_kws]) * 5.0

        if o.profile.id in getattr(c.state, "avoid_character_ids", []):
            score -= 20.0
        if o.profile.id in getattr(c.state, "feared_character_ids", []):
            score -= 25.0

        dx = o.position["x"] - c.position["x"]
        dy = o.position["y"] - c.position["y"]
        score -= (abs(dx) + abs(dy)) * 0.3

        if score > best_score:
            best_score = score
            best = o

    return best


def face_each_other() -> None:
    for c in TAGGED_CHARACTERS.values():
        pid = c.state.conversation_partner_id
        if not pid or pid not in TAGGED_CHARACTERS:
            continue
        other = TAGGED_CHARACTERS[pid]
        dx = other.position["x"] - c.position["x"]
        dy = other.position["y"] - c.position["y"]
        c.state.facing = {"x": dx, "y": dy}


def _append_speech_bubble(c, text: str, tick: int) -> None:
    c.state.speech_bubbles.append({"text": text, "tick": tick})
    c.state.speech_bubbles = c.state.speech_bubbles[-4:]


def _expire_speech(c, tick: int) -> None:
    if getattr(c.state, "speech_expires_tick", 0) and tick >= c.state.speech_expires_tick:
        c.state.spoken_text = ""
        c.state.speech_expires_tick = 0
    kept = []
    for b in c.state.speech_bubbles:
        try:
            if tick - int(b.get("tick", tick)) < 18:
                kept.append(b)
        except Exception:
            pass
    c.state.speech_bubbles = kept


def _start_waiting_turn(speaker, listener) -> None:
    speaker.state.waiting_on_character_id = listener.profile.id
    speaker.state.awaiting_reply_from_id = ""
    listener.state.awaiting_reply_from_id = speaker.profile.id
    listener.state.waiting_on_character_id = ""
    speaker.state.conversation_partner_id = listener.profile.id
    listener.state.conversation_partner_id = speaker.profile.id


def _end_conversation(a, b=None) -> None:
    a.state.conversation_partner_id = ""
    a.state.awaiting_reply_from_id = ""
    a.state.waiting_on_character_id = ""
    a.state.conversation_turns_remaining = 0
    a.state.conversation_topic = ""
    if b is not None:
        b.state.conversation_partner_id = ""
        b.state.awaiting_reply_from_id = ""
        b.state.waiting_on_character_id = ""
        b.state.conversation_turns_remaining = 0
        b.state.conversation_topic = ""


def _should_end_conversation(a) -> bool:
    scores = list(a.state.conversation_score_history[-5:])
    if not scores:
        return False
    avg = sum(scores) / len(scores)
    return avg < float(a.state.social_patience)


def _remember_conversation_line(c, speaker_id: str, text: str, speech_act: str, topic: str, tick: int) -> None:
    c.conversation_history.append({
        "speaker_id": speaker_id,
        "text": text,
        "speech_act": speech_act,
        "topic": topic,
        "tick": tick,
    })
    c.conversation_history = c.conversation_history[-20:]


def _add_or_update_subjective_view(c, subject_type: str, subject_ref: str, keywords: list[str], tick: int) -> None:
    if not subject_ref or not keywords:
        return
    existing = None
    for view in getattr(c, "subjective_views", []):
        try:
            if getattr(view, "subject_ref", "") == subject_ref and getattr(view, "subject_type", "") == subject_type:
                existing = view
                break
        except Exception:
            if isinstance(view, dict) and view.get("subject_ref") == subject_ref and view.get("subject_type") == subject_type:
                existing = view
                break

    if existing is None:
        c.subjective_views.append({
            "subject_type": subject_type,
            "subject_ref": subject_ref,
            "keywords": keywords[:8],
            "summary": ", ".join(keywords[:4]),
            "confidence": 0.5,
            "last_updated_tick": tick,
        })
        c.subjective_views = c.subjective_views[-40:]
        return

    try:
        merged = list(dict.fromkeys(list(existing.keywords) + list(keywords)))[:12]
        existing.keywords = merged
        existing.summary = ", ".join(merged[:4])
        existing.confidence = min(1.0, float(existing.confidence) + 0.1)
        existing.last_updated_tick = tick
    except Exception:
        merged = list(dict.fromkeys(list(existing.get("keywords", [])) + list(keywords)))[:12]
        existing["keywords"] = merged
        existing["summary"] = ", ".join(merged[:4])
        existing["confidence"] = min(1.0, float(existing.get("confidence", 0.5)) + 0.1)
        existing["last_updated_tick"] = tick


def _apply_speech_act_effects(c, target, speech_act: str, tick: int) -> None:
    c.state.conversation_last_speech_act = speech_act
    if speech_act == "insult":
        target.state.emotional_temperature = min(100.0, target.state.emotional_temperature + 10.0)
        target.state.grudges.append({
            "target_character_id": c.profile.id,
            "reason": "insult",
            "intensity": 20.0,
            "created_tick": tick,
            "decay_rate": 0.25,
        })
        _add_or_update_subjective_view(target, "character", c.profile.id, ["annoying", "hostile"], tick)
    elif speech_act == "threat":
        target.state.emotional_temperature = min(100.0, target.state.emotional_temperature + 15.0)
        target.state.grudges.append({
            "target_character_id": c.profile.id,
            "reason": "threat",
            "intensity": 28.0,
            "created_tick": tick,
            "decay_rate": 0.2,
        })
        _add_or_update_subjective_view(target, "character", c.profile.id, ["threatening", "dangerous"], tick)
    elif speech_act in ["question", "statement", "request"]:
        c.state.affinity[target.profile.id] = float(c.state.affinity.get(target.profile.id, 0.0)) + 0.5
        target.state.affinity[c.profile.id] = float(target.state.affinity.get(c.profile.id, 0.0)) + 0.3


def _apply_emotion_enforcement(c, name: str, act: dict, emotion: str, world: dict) -> tuple[str, dict]:
    act = dict(act or {})
    if emotion in ["fearful", "sad"]:
        if name in ["smash", "yell"]:
            name = "leave" if emotion == "fearful" else "relax"
        if emotion == "fearful" and name == "speak":
            name = "leave"
    elif emotion == "awkward":
        if name in ["yell", "smash"]:
            name = "wait"
    elif emotion == "calm":
        if name in ["smash", "yell"]:
            name = "speak"
    elif emotion == "curious":
        if name in ["smash", "leave"]:
            name = "observe"
    elif emotion == "suspicious":
        if name == "smash":
            name = "observe"
    elif emotion == "annoyed":
        if name == "smash":
            name = "yell"
    elif emotion == "angry":
        if name == "relax":
            name = "gesture"
    elif emotion == "furious":
        if name in ["wait", "observe", "relax", "study"]:
            name = "yell"
        if name == "smash" and float(getattr(c.state, "emotional_temperature", 0.0)) < 75.0:
            name = "yell"
    elif emotion in ["warm", "playful"]:
        if name in ["smash", "leave"]:
            name = "speak"
    elif emotion == "smug":
        if name == "leave":
            name = "gesture"

    if name == "leave":
        cx, cy = c.position["x"], c.position["y"]
        candidate_tiles = [
            {"x": max(1, cx - 2), "y": cy},
            {"x": min(world.get("grid", {}).get("width", 20) - 2, cx + 2), "y": cy},
            {"x": cx, "y": max(1, cy - 2)},
            {"x": cx, "y": min(world.get("grid", {}).get("height", 12) - 2, cy + 2)},
        ]
        chosen = None
        for tile in candidate_tiles:
            if _is_walkable(world, tile["x"], tile["y"], mover_id=c.profile.id):
                chosen = tile
                break
        act["target_tile"] = chosen or {"x": cx, "y": cy}

    if name in ["speak", "yell"] and not str(act.get("utterance") or "").strip():
        name = "wait"

    c.state.action_mood = EMOTION_TO_ACTION_MOOD.get(emotion, "calm")
    return name, act


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
            _decay_memories(c, world["tick"])
            _update_social_bias_lists(c)
            _expire_speech(c, world["tick"])

        face_each_other()

        for c in list(TAGGED_CHARACTERS.values()):
            pending = c.state.pending_action or {}

            if c.state.waiting_on_character_id:
                c.state.current_action_name = "wait"
                c.state.spoken_text = "..."
                c.state.speech_expires_tick = world["tick"] + 2
                continue

            if pending.get("name") == "move":
                tgt = pending.get("target_tile") or {}
                tx = tgt.get("x", c.position["x"])
                ty = tgt.get("y", c.position["y"])
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

            act = res.get("action", {}) or {}
            name = act.get("name", "wait")
            speech_act = str(res.get("speech_act", "statement")).strip() or "statement"
            emotion = str(res.get("emotion", "calm")).strip() or "calm"
            conversation_score = float(res.get("conversation_score", 50.0))
            topic = str(res.get("topic", "")).strip()
            view_keywords = [str(x).strip() for x in (res.get("view_keywords") or []) if str(x).strip()]

            c.state.mood = emotion
            c.state.conversation_last_score = conversation_score
            c.state.conversation_score_history.append(conversation_score)
            c.state.conversation_score_history = c.state.conversation_score_history[-5:]

            if topic:
                c.state.conversation_topic = topic

            if c.state.conversation_partner_id and name == "move":
                name = "wait"

            if name in ["speak", "yell", "gesture", "evaluate_subjective"] and not act.get("target_character_id"):
                other = pick_social_target(c)
                if other:
                    act["target_character_id"] = other.profile.id

            name, act = _apply_emotion_enforcement(c, name, act, emotion, world)

            if name == "evaluate_subjective":
                subject_type = (act.get("subject_type") or "character").strip()
                subject_ref = (act.get("subject_ref") or act.get("target_character_id") or "").strip()
                if subject_ref:
                    _add_or_update_subjective_view(c, subject_type, subject_ref, view_keywords or ["interesting"], world["tick"])
                    _remember(c, {
                        "kind": "evaluation",
                        "target": subject_ref,
                        "about": subject_ref,
                        "text": ", ".join(view_keywords or ["interesting"]),
                        "speech_act": "statement",
                        "topic": topic,
                        "source": "direct",
                        "tick": world["tick"],
                        "importance": 0.40,
                    })
                c.state.current_action_name = "evaluate_subjective"
                _apply_motivator_effects(c, "study", world)
                continue

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

                tgt_id = (act.get("target_character_id") or "").strip()
                if not tgt_id or tgt_id not in TAGGED_CHARACTERS:
                    c.state.current_action_name = "wait"
                    continue

                target = TAGGED_CHARACTERS[tgt_id]

                c.state.spoken_text = utt
                c.state.speech_expires_tick = world["tick"] + 12
                _append_speech_bubble(c, utt, world["tick"])

                c.state.conversation_partner_id = tgt_id
                target.state.conversation_partner_id = c.profile.id
                c.state.conversation_turns_remaining = max(c.state.conversation_turns_remaining, 3)
                target.state.conversation_turns_remaining = max(target.state.conversation_turns_remaining, 3)

                if topic:
                    target.state.conversation_topic = topic
                elif not target.state.conversation_topic:
                    target.state.conversation_topic = c.state.conversation_topic

                _remember_conversation_line(c, c.profile.id, utt, speech_act, c.state.conversation_topic, world["tick"])
                _remember_conversation_line(target, c.profile.id, utt, speech_act, c.state.conversation_topic, world["tick"])

                _remember(c, {
                    "kind": "interaction",
                    "target": tgt_id,
                    "about": tgt_id,
                    "text": utt,
                    "speech_act": speech_act,
                    "topic": c.state.conversation_topic,
                    "source": "direct",
                    "tick": world["tick"],
                    "importance": 0.50,
                })
                _remember(target, {
                    "kind": "interaction",
                    "target": c.profile.id,
                    "about": c.profile.id,
                    "text": utt,
                    "speech_act": speech_act,
                    "topic": c.state.conversation_topic,
                    "source": "direct",
                    "tick": world["tick"],
                    "importance": 0.55,
                })

                _apply_speech_act_effects(c, target, speech_act, world["tick"])
                _propagate_gossip(c, target, utt, speech_act, c.state.conversation_topic, world["tick"])

                if view_keywords:
                    _add_or_update_subjective_view(c, "character", tgt_id, view_keywords, world["tick"])

                _start_waiting_turn(c, target)
                _apply_motivator_effects(c, name, world)

            if name in ["gesture", "leave", "smash", "observe", "relax", "study", "wait"]:
                _apply_motivator_effects(c, name, world)

            if c.state.awaiting_reply_from_id:
                c.state.awaiting_reply_from_id = ""

            if c.state.conversation_turns_remaining > 0:
                c.state.conversation_turns_remaining -= 1
                if c.state.conversation_turns_remaining == 0:
                    partner_id = c.state.conversation_partner_id
                    if partner_id and partner_id in TAGGED_CHARACTERS:
                        _end_conversation(c, TAGGED_CHARACTERS[partner_id])
                    else:
                        _end_conversation(c)

            if _should_end_conversation(c):
                partner_id = c.state.conversation_partner_id
                if partner_id and partner_id in TAGGED_CHARACTERS:
                    _end_conversation(c, TAGGED_CHARACTERS[partner_id])
                else:
                    _end_conversation(c)

            c.state.current_action_name = name

        world["tagged_characters"] = {cid: c.model_dump() for cid, c in TAGGED_CHARACTERS.items()}
        await manager.broadcast(get_world_snapshot())
        await asyncio.sleep(world.get("config", {}).get("tick_rate", 1.0))
