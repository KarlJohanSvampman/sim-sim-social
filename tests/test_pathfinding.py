from backend.services.pathfinding import heuristic

def test_heuristic():
    assert heuristic((0,0,0), (2,3,0)) == 5
