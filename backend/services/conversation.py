from uuid import uuid4
from services.conversation_llm import generate_conversation_turn
def maybe_start_conversation(world, speaker, target_id):
    target=world["characters"].get(target_id)
    if not target:
        return None
    if speaker.get("conversation_id") or target.get("conversation_id"):
        return speaker.get("conversation_id") or target.get("conversation_id")
    cid=str(uuid4())
    world["conversations"][cid]={"id":cid,"participants":[speaker["id"],target_id],"turn":speaker["id"],"history":[],"goal":"socialize","status":"active","turn_count":0}
    speaker["conversation_id"]=cid
    target["conversation_id"]=cid
    return cid
def step_conversation(world, speaker):
    cid=speaker.get("conversation_id")
    if not cid:
        return None
    conv=world["conversations"].get(cid)
    if not conv or conv["status"]!="active":
        speaker["conversation_id"]=None
        return None
    if conv["turn"]!=speaker["id"]:
        return {"action":"continue_conversation"}
    other_id=[p for p in conv["participants"] if p!=speaker["id"]][0]
    other=world["characters"][other_id]
    generated=generate_conversation_turn(speaker, other, conv, world)
    conv["turn_count"] += 1
    conv["turn"] = other_id
    conv["history"].append({"speaker":speaker["id"],"text":generated["speech"]})
    if generated.get("end_conversation") or conv["turn_count"]>=6:
        conv["status"]="closed"
        for pid in conv["participants"]:
            world["characters"][pid]["conversation_id"]=None
    return {"action":"continue_conversation","target":other_id,"speech":generated["speech"]}
