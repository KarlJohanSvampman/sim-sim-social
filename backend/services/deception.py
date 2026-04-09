import random
def maybe_lie(character, truth):
    chance=character.get("deception",0.1)
    if random.random() < chance:
        return {"is_lie":True,"content":f"Not really... {truth}"}
    return {"is_lie":False,"content":truth}
