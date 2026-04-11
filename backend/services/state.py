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

def make_tile(x, y, z=0, tile_type="floor", **overrides):
    base = {
        "x": x,
        "y": y,
        "z": z,
        "type": tile_type,
        "blocks_movement": False,
        "blocks_sight": False,
        "lot_id": None,
        "zone_type": "residential",
        "elevation": 0.0,
        "road": False,
        "sidewalk": False,
        "building_id": None,
        "interactions": [],
        "cover_value": 0.0,
        "noise_modifier": 1.0,
        "light_level": 1.0
    }
    base.update(overrides)
    return base

def init_world():
    if WORLD["grid"]["tiles"]:
        return

    width = 12
    height = 12

    for y in range(height):
        for x in range(width):
            tile = make_tile(x, y, 0)

            if x in (0, width - 1) or y in (0, height - 1):
                tile.update({
                    "type": "wall",
                    "blocks_movement": True,
                    "blocks_sight": True,
                    "building_id": "boundary",
                    "cover_value": 1.0,
                    "light_level": 0.5
                })
            elif y in (4, 5):
                tile.update({
                    "type": "road",
                    "road": True,
                    "zone_type": "street",
                    "noise_modifier": 1.25,
                    "light_level": 0.9
                })
            elif y in (3, 6):
                tile.update({
                    "type": "sidewalk",
                    "sidewalk": True,
                    "zone_type": "street_edge",
                    "noise_modifier": 1.05,
                    "light_level": 1.0
                })
            elif 1 <= x <= 4 and 1 <= y <= 2:
                tile.update({
                    "type": "house_floor",
                    "lot_id": "lot_a",
                    "zone_type": "residential",
                    "building_id": "house_a",
                    "interactions": ["walk", "inspect"],
                    "light_level": 0.8
                })
            elif 7 <= x <= 10 and 1 <= y <= 2:
                tile.update({
                    "type": "house_floor",
                    "lot_id": "lot_b",
                    "zone_type": "residential",
                    "building_id": "house_b",
                    "interactions": ["walk", "inspect"],
                    "light_level": 0.8
                })
            elif x == 2 and y == 3:
                tile.update({
                    "type": "door",
                    "lot_id": "lot_a",
                    "zone_type": "residential",
                    "building_id": "house_a",
                    "interactions": ["open", "close", "enter"],
                    "cover_value": 0.2
                })
            elif x == 8 and y == 3:
                tile.update({
                    "type": "door",
                    "lot_id": "lot_b",
                    "zone_type": "residential",
                    "building_id": "house_b",
                    "interactions": ["open", "close", "enter"],
                    "cover_value": 0.2
                })
            elif 1 <= x <= 10 and 7 <= y <= 10:
                tile.update({
                    "type": "yard",
                    "lot_id": "shared_green",
                    "zone_type": "outdoor",
                    "noise_modifier": 0.9,
                    "light_level": 1.1
                })

            WORLD["grid"]["tiles"][f"{x},{y},0"] = tile

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
        "npc_1": dict(base, **{
            "id": "npc_1",
            "name": "Ada",
            "position": {"x": 2, "y": 2, "z": 0},
            "appearance_summary": {"age": 30, "sex": "female", "body_type": "average"},
            "render_ref": {"mesh_id": "human_base_f01", "animation_controller": "biped_v1"}
        }),
        "npc_2": dict(base, **{
            "id": "npc_2",
            "name": "Bryn",
            "position": {"x": 9, "y": 9, "z": 0},
            "appearance_summary": {"age": 34, "sex": "male", "body_type": "average"},
            "render_ref": {"mesh_id": "human_m_adult_02", "animation_controller": "biped_v2"}
        })
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
