from __future__ import annotations
from collections import deque
from services.state import get_world

def neighbors4(x, y):
    for dx, dy in ((1,0), (-1,0), (0,1), (0,-1)):
        yield x + dx, y + dy

def path_to(start_x: int, start_y: int, goal_x: int, goal_y: int):
    world = get_world()
    start = (start_x, start_y)
    goal = (goal_x, goal_y)
    if start == goal:
        return [start]
    q = deque([start])
    came = {start: None}
    while q:
        cur = q.popleft()
        for nxt in neighbors4(*cur):
            tile = world["grid"]["tiles"].get(f"{nxt[0]},{nxt[1]}")
            if not tile or tile.get("blocks_movement"):
                continue
            if nxt in came:
                continue
            came[nxt] = cur
            if nxt == goal:
                path = [nxt]
                node = cur
                while node is not None:
                    path.append(node)
                    node = came[node]
                path.reverse()
                return path
            q.append(nxt)
    return []
