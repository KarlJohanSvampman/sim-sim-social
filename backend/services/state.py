from copy import deepcopy

WORLD = {
    "tick": 0,
    "grid": {"width": 12, "height": 12, "tiles": {}},
    "characters": {},
    "relationships": {},
    "conversations": {},
    "institutions": {},
    "news": []
}

def rel_key(a_id, b_id):
    return f"{a_id}->{b_id}"

def init_world():
    if WORLD["grid"]["tiles"]:
        return
    for y in range(12):
        for x in range(12):
            WORLD["grid"]["tiles"][f"{x},{y},0"] = {
                "x": x, "y": y, "z": 0, "type": "floor",
                "blocks_movement": False, "blocks_sight": False
            }
    base = {
        "goal": None,
        "plan": [],
        "memory": [],
        "beliefs": [],
        "speech": None,
        "thoughts": "...",
        "conversation_id": None,
        "needs": {"hunger": 10, "thirst": 10, "fatigue": 10, "bladder": 10},
        "health": 100.0,
        "intoxication": 0.0,
        "institution_role": None,
        "institution_id": None
    }
    WORLD["characters"] = {
        "npc_1": dict(base, **{"id": "npc_1", "name": "Ada", "position": {"x": 2, "y": 2, "z": 0}}),
        "npc_2": dict(base, **{"id": "npc_2", "name": "Bryn", "position": {"x": 9, "y": 9, "z": 0}})
    }
    WORLD["institutions"] = {
        "inst_police": {
            "id": "inst_police",
            "name": "Police Department",
            "kind": "law",
            "members": [],
            "policies": {"respond_to_reports": True}
        },
        "inst_clinic": {
            "id": "inst_clinic",
            "name": "Community Clinic",
            "kind": "health",
            "members": [],
            "policies": {"treat_injured": True}
        },
        "inst_news": {
            "id": "inst_news",
            "name": "Neighborhood Bulletin",
            "kind": "media",
            "members": [],
            "policies": {"publish_news": True}
        }
    }
    for a in WORLD["characters"]:
        for b in WORLD["characters"]:
            if a != b:
                WORLD["relationships"][rel_key(a, b)] = {"trust": 0.0, "affection": 0.0, "fear": 0.0}

def get_world():
    return WORLD

def get_world_snapshot():
    return deepcopy(WORLD)
