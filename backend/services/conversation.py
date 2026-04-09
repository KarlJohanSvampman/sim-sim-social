from uuid import uuid4
from services.relationship import choose_conversation_goal, apply_relationship_delta
from services.db import upsert_conversation, log_event

def maybe_start_conversation(world, speaker_id, target_id):
    speaker = world["characters"].get(speaker_id)
    target = world["characters"].get(target_id)
    if not speaker or not target:
        return None
    if speaker.get("conversation_id") or target.get("conversation_id"):
        return speaker.get("conversation_id") or target.get("conversation_id")
    goal = choose_conversation_goal(world, speaker_id, target_id)
    cid = str(uuid4())
    conv = {
        "id": cid,
        "participants": [speaker_id, target_id],
        "turn": speaker_id,
        "goal": goal,
        "history": [],
        "status": "active",
        "turn_count": 0
    }
    world["conversations"][cid] = conv
    speaker["conversation_id"] = cid
    target["conversation_id"] = cid
    upsert_conversation(cid, conv)
    log_event(world["tick"], "conversation_started", speaker_id, target_id, {"conversation_id": cid, "goal": goal})
    return cid

def conversation_turn(world, speaker_id):
    speaker = world["characters"][speaker_id]
    cid = speaker.get("conversation_id")
    if not cid:
        return None
    conv = world["conversations"].get(cid)
    if not conv or conv["status"] != "active":
        speaker["conversation_id"] = None
        return None
    if conv["turn"] != speaker_id:
        return None
    other_id = [p for p in conv["participants"] if p != speaker_id][0]
    goal = conv["goal"]
    if goal == "flirt":
        speech = "You look nice today."
        delta = {"affection": 2.0, "trust": 0.5, "fear": 0.0}
    elif goal == "interrogate":
        speech = "Where were you earlier?"
        delta = {"trust": -0.5, "affection": -0.2, "fear": 1.0}
    elif goal == "reassure":
        speech = "It's okay, you're safe."
        delta = {"trust": 1.5, "affection": 0.5, "fear": -1.0}
    elif goal == "manipulate":
        speech = "You can trust me on this."
        delta = {"trust": 0.8, "affection": 0.1, "fear": 0.2}
    else:
        speech = "Mm-hm."
        delta = {"trust": 0.2, "affection": 0.1, "fear": 0.0}
    conv["history"].append({"speaker": speaker_id, "text": speech})
    conv["turn_count"] += 1
    conv["turn"] = other_id
    speaker["speech"] = speech
    apply_relationship_delta(world, speaker_id, other_id, delta)
    upsert_conversation(cid, conv)
    log_event(world["tick"], "conversation_turn", speaker_id, other_id, {"conversation_id": cid, "goal": goal, "speech": speech, "relationship_update": delta})
    if conv["turn_count"] >= 6:
        conv["status"] = "closed"
        for pid in conv["participants"]:
            world["characters"][pid]["conversation_id"] = None
        upsert_conversation(cid, conv)
    return speech
