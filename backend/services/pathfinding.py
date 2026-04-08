import heapq

def heuristic(a,b):
    return abs(a[0]-b[0]) + abs(a[1]-b[1])

def neighbors4(world, x, y, z=0):
    out=[]
    for dx,dy in [(1,0),(-1,0),(0,1),(0,-1)]:
        nx,ny=x+dx,y+dy
        if 0<=nx<world["grid"]["width"] and 0<=ny<world["grid"]["height"]:
            out.append((nx,ny,z))
    return out

def reconstruct(came_from, current):
    out=[current]
    while current in came_from:
        current = came_from[current]
        out.append(current)
    out.reverse()
    return out

def astar(world, start, goal):
    frontier=[]
    heapq.heappush(frontier,(0,start))
    came_from={}
    g={start:0}
    while frontier:
        _,current=heapq.heappop(frontier)
        if current==goal:
            return reconstruct(came_from,current)
        for nxt in neighbors4(world,*current):
            cost=g[current]+1
            if nxt not in g or cost<g[nxt]:
                g[nxt]=cost
                came_from[nxt]=current
                heapq.heappush(frontier,(cost+heuristic(nxt,goal),nxt))
    return []
