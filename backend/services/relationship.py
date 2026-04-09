from services.state import rel_key
from services.db import upsert_relationship

def get_edge(world, a_id, b_id):
    key = rel_key(a_id, b_id)
    edge = world["relationships"].setdefault(key, {"trust": 0.0, "affection": 0.0, "fear": 0.0})
    return edge

def apply_relationship_delta(world, a_id, b_id, delta):
    edge = get_edge(world, a_id, b_id)
    for k in ("trust", "affection", "fear"):
        edge[k] = max(-100.0, min(100.0, edge.get(k, 0.0) + float(delta.get(k, 0.0))))
    upsert_relationship(a_id, b_id, edge)
    return edge

def choose_conversation_goal(world, a_id, b_id):
    edge = get_edge(world, a_id, b_id)
    if edge["fear"] > 25:
        return "reassure"
    if edge["affection"] > 25:
        return "flirt"
    if edge["trust"] < -10:
        return "interrogate"
    if edge["trust"] > 15 and edge["affection"] < 5:
        return "manipulate"
    return "socialize"
