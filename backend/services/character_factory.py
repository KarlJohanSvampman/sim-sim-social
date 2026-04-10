from copy import deepcopy
from models.character_profile import CharacterProfile

BASE_CHARACTER = {
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
    "institution_id": None,
    "inventory": [],
    "hands": {"left": None, "right": None},
    "compressed_memory": [],
    "suspicion": {},
    "deception": 0.1,
    "addiction": {"alcohol": 0.0, "tobacco": 0.0},
    "cravings": {"alcohol": 0.0, "tobacco": 0.0},
    "withdrawal": {"alcohol": 0.0, "tobacco": 0.0},
}

def create_character_entity(char_id: str, profile: CharacterProfile, position: dict):
    data = deepcopy(BASE_CHARACTER)
    data.update({
        "id": char_id,
        "name": profile.name,
        "position": position,
        "nicknames": profile.nicknames,
        "profile": profile.model_dump(),
        "appearance_summary": {
            "age": profile.appearance.age,
            "sex": profile.appearance.sex,
            "skin_tone": profile.appearance.skin_tone,
            "body_type": profile.appearance.body_type,
            "attractiveness_symmetry": profile.appearance.attractiveness_symmetry,
            "uniqueness_score": profile.appearance.uniqueness_score,
            "profession": profile.appearance.profession,
            "titles": profile.appearance.titles,
        },
        "personality_summary": profile.mind.traits.model_dump(),
        "render_ref": {
            "mesh_id": profile.render.mesh_id,
            "animation_controller": profile.render.animation_controller,
            "idle_set": profile.render.idle_set,
            "gesture_set": profile.render.gesture_set,
            "voice_profile": profile.render.voice_profile,
        }
    })
    return data
