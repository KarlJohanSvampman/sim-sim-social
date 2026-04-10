# Lightweight in-process fallback storage for the editor-focused repo.
_EVENTS = []
_CHARS = {}

def init_db():
    return

def upsert_character(char_id, data):
    _CHARS[char_id] = data

def list_timeline_events(limit=200):
    return list(reversed(_EVENTS[-limit:]))

def replay_events(start_tick, end_tick):
    return [e for e in _EVENTS if start_tick <= e.get("tick", 0) <= end_tick]

def replay_window(cursor_tick, radius=15):
    start_tick = max(1, cursor_tick - radius)
    end_tick = cursor_tick + radius
    return [e for e in _EVENTS if start_tick <= e.get("tick", 0) <= end_tick]

def log_event(tick, kind, actor_id=None, target_id=None, payload=None):
    _EVENTS.append({
        "id": len(_EVENTS) + 1,
        "tick": tick,
        "kind": kind,
        "actor_id": actor_id,
        "target_id": target_id,
        "payload": payload or {}
    })
