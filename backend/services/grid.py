def key(x,y,z=0):
    return f"{x},{y},{z}"

def get_tile(world, x, y, z=0):
    return world["grid"]["tiles"].get(key(x,y,z))

def in_bounds(world, x, y):
    return 0 <= x < world["grid"]["width"] and 0 <= y < world["grid"]["height"]

def is_walkable(world, x, y, z=0):
    tile = get_tile(world, x, y, z)
    return bool(tile) and not tile["blocks_movement"]

def neighbors4(world, x, y, z=0):
    out = []
    for dx,dy in [(1,0),(-1,0),(0,1),(0,-1)]:
        nx, ny = x+dx, y+dy
        if in_bounds(world, nx, ny) and is_walkable(world, nx, ny, z):
            out.append((nx,ny,z))
    return out
