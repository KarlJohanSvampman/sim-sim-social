from models.character_profile import CharacterProfile
from services.state import get_world
from services.db import upsert_character, log_event
from services.institutions import assign_role
from services.character_factory import create_character_entity

def inject_news(content):
    world = get_world()
    world.setdefault("news", []).append({"content": content})
    log_event(world["tick"], "news_injected", None, None, {"content": content})

def get_character(char_id):
    return get_world()["characters"].get(char_id)

def patch_character(char_id, updates):
    world = get_world()
    c = world["characters"].get(char_id)
    if not c:
        return None
    for k, v in updates.items():
        if k == "profile" and isinstance(v, dict):
            c["profile"] = {**c.get("profile", {}), **v}
        elif isinstance(v, dict) and isinstance(c.get(k), dict):
            c[k] = {**c[k], **v}
        else:
            c[k] = v
    if updates.get("institution_role"):
        assign_role(world, char_id, c.get("institution_id") or "inst_news", updates["institution_role"])
    if "profile" in updates:
        c["name"] = c["profile"].get("name", c["name"])
        app = c["profile"].get("appearance", {})
        c["appearance_summary"] = {
            "age": app.get("age"),
            "sex": app.get("sex"),
            "skin_tone": app.get("skin_tone"),
            "body_type": app.get("body_type"),
            "attractiveness_symmetry": app.get("attractiveness_symmetry"),
            "uniqueness_score": app.get("uniqueness_score"),
            "profession": app.get("profession"),
            "titles": app.get("titles", []),
        }
        if c["profile"].get("mind", {}).get("traits"):
            c["personality_summary"] = c["profile"]["mind"]["traits"]
        render = c["profile"].get("render", {})
        c["render_ref"] = {
            "mesh_id": render.get("mesh_id"),
            "animation_controller": render.get("animation_controller"),
            "idle_set": render.get("idle_set"),
            "gesture_set": render.get("gesture_set"),
            "voice_profile": render.get("voice_profile"),
        }
    upsert_character(char_id, c)
    log_event(world["tick"], "character_patched", char_id, None, updates)
    return c

def create_character(char_id, profile_payload, position):
    world = get_world()
    profile = CharacterProfile.model_validate(profile_payload)
    c = create_character_entity(char_id, profile, position)
    world["characters"][char_id] = c
    for other_id in list(world["characters"].keys()):
        if other_id == char_id:
            continue
        world["relationships"][f"{char_id}->{other_id}"] = {"trust": 0.0, "affection": 0.0, "fear": 0.0}
        world["relationships"][f"{other_id}->{char_id}"] = {"trust": 0.0, "affection": 0.0, "fear": 0.0}
    upsert_character(char_id, c)
    log_event(world["tick"], "character_created", char_id, None, {"position": position, "profile": profile.model_dump()})
    return c
