from copy import deepcopy
from models.character_profile import CharacterProfile
from services.character_factory import create_character_entity

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

    ada_profile = CharacterProfile(name="Ada")
    bryn_profile = CharacterProfile(name="Bryn", appearance={"sex":"male","age":34,"body_type":"average","skin_tone":"light","profession":"paramedic"}, render={"mesh_id":"human_m_adult_02","animation_controller":"biped_v2","idle_set":"idle_guarded","gesture_set":"gesture_reserved","voice_profile":"baritone_calm_02","material_preset":"skin_light_01","locomotion_style":"measured_walk","scale":1.03})

    WORLD["characters"] = {
        "npc_1": create_character_entity("npc_1", ada_profile, {"x": 2, "y": 2, "z": 0}),
        "npc_2": create_character_entity("npc_2", bryn_profile, {"x": 9, "y": 9, "z": 0}),
    }

    WORLD["institutions"] = {
        "inst_police": {"id":"inst_police","name":"Police Department","kind":"law","members":[],"policies":{"respond_to_reports":True}},
        "inst_clinic": {"id":"inst_clinic","name":"Community Clinic","kind":"health","members":["npc_2"],"policies":{"treat_injured":True}},
        "inst_news": {"id":"inst_news","name":"Neighborhood Bulletin","kind":"media","members":["npc_1"],"policies":{"publish_news":True}}
    }
    WORLD["characters"]["npc_1"]["institution_id"] = "inst_news"
    WORLD["characters"]["npc_1"]["institution_role"] = "reporter"
    WORLD["characters"]["npc_2"]["institution_id"] = "inst_clinic"
    WORLD["characters"]["npc_2"]["institution_role"] = "paramedic"

    for a in WORLD["characters"]:
        for b in WORLD["characters"]:
            if a != b:
                WORLD["relationships"][rel_key(a, b)] = {"trust": 0.0, "affection": 0.0, "fear": 0.0}

def get_world():
    return WORLD

def get_world_snapshot():
    return deepcopy(WORLD)
