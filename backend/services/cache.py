import json
import redis
from services.config import REDIS_URL

r = redis.Redis.from_url(REDIS_URL, decode_responses=True)

def set_world_snapshot(snapshot: dict):
    r.set("world:snapshot", json.dumps(snapshot))

def get_world_snapshot_cache():
    raw = r.get("world:snapshot")
    return json.loads(raw) if raw else None

def push_recent_event(event: dict):
    pipe = r.pipeline()
    pipe.lpush("timeline:recent", json.dumps(event))
    pipe.ltrim("timeline:recent", 0, 499)
    pipe.execute()

def get_recent_events(limit=100):
    return [json.loads(x) for x in r.lrange("timeline:recent", 0, limit - 1)]
