import asyncio
from services.state import get_world
from services.pathfinding import astar

def tick_character(c):
    n = c.setdefault("needs", {"hunger": 10, "thirst": 10, "fatigue": 10, "bladder": 10})
    n["hunger"] = min(100, n["hunger"] + 0.2)
    n["thirst"] = min(100, n["thirst"] + 0.25)
    n["fatigue"] = min(100, n["fatigue"] + 0.15)
    n["bladder"] = min(100, n["bladder"] + 0.18)

def maybe_move_character(world, c):
    pos = c.get("position", {"x": 1, "y": 1, "z": 0})
    target = c.setdefault("sim_target", {"x": 6, "y": 6, "z": 0})
    path = astar(world, (pos["x"], pos["y"], 0), (target["x"], target["y"], 0))
    if len(path) > 1:
        nx, ny, _ = path[1]
        pos["x"], pos["y"] = nx, ny
        c["thoughts"] = f"Moving toward {target['x']},{target['y']}"
        c["last_action"] = {"type": "move", "target": {"x": nx, "y": ny, "z": 0}}
    else:
        c["sim_target"] = {"x": max(1, (target["x"] + 7) % max(2, world["grid"]["width"] - 1)), "y": max(1, (target["y"] + 5) % max(2, world["grid"]["height"] - 1)), "z": 0}
        c["thoughts"] = "Replanning route."
        c["last_action"] = {"type": "replan"}

async def live_sim_loop():
    world = get_world()
    while True:
        world["tick"] = world.get("tick", 0) + 1
        for c in world.get("characters", {}).values():
            tick_character(c)
            maybe_move_character(world, c)
        await asyncio.sleep(1.0)
