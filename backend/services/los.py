def bresenham(x0, y0, x1, y1):
    points = []
    dx = abs(x1 - x0)
    dy = -abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx + dy
    x, y = x0, y0
    while True:
        points.append((x, y))
        if x == x1 and y == y1:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x += sx
        if e2 <= dx:
            err += dx
            y += sy
    return points

def line_of_sight(world, a, b):
    from services.grid import get_tile
    pts = bresenham(a[0], a[1], b[0], b[1])
    for x, y in pts[1:-1]:
        tile = get_tile(world, x, y, 0)
        if tile and tile["blocks_sight"]:
            return False
    return True
