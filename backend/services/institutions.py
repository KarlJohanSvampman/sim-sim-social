from services.db import upsert_institution, log_event

def tick_institutions(world):
    for inst_id, inst in world["institutions"].items():
        upsert_institution(inst_id, inst)
    if world["news"]:
        latest = world["news"][-1]
        log_event(world["tick"], "institution_broadcast", "inst_news", None, latest)

def assign_role(world, char_id, institution_id, role):
    c = world["characters"].get(char_id)
    inst = world["institutions"].get(institution_id)
    if not c or not inst:
        return None
    c["institution_id"] = institution_id
    c["institution_role"] = role
    if char_id not in inst["members"]:
        inst["members"].append(char_id)
    upsert_institution(institution_id, inst)
    log_event(world["tick"], "institution_role_assigned", char_id, institution_id, {"role": role})
    return c
