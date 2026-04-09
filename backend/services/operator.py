from services.state import get_world
from services.db import upsert_character, log_event
from services.institutions import assign_role

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
        c[k] = v if not isinstance(v, dict) or not isinstance(c.get(k), dict) else {**c[k], **v}
    if updates.get("institution_role"):
        assign_role(world, char_id, "inst_news", updates["institution_role"])
    upsert_character(char_id, c)
    log_event(world["tick"], "character_patched", char_id, None, updates)
    return c
