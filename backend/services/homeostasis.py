def decide_goal(c):
    n = c["needs"]
    if n["bladder"] > 80:
        return {"type": "use_toilet", "target": (1, 10, 0)}
    if n["thirst"] > 60:
        return {"type": "drink", "target": (2, 10, 0)}
    if n["hunger"] > 60:
        return {"type": "eat", "target": (10, 1, 0)}
    if n["fatigue"] > 70:
        return {"type": "sleep", "target": (1, 1, 0)}
    return {"type": "socialize", "target": (6, 6, 0)}
