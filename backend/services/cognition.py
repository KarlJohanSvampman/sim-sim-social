from services.relationship import get_edge
def build_context(c, focused, world):
    rels={}
    for other_id in world["characters"]:
        if other_id != c["id"]:
            rels[other_id]=get_edge(world,c["id"],other_id)
    return {
        "identity":{"id":c["id"],"name":c["name"]},
        "needs":c["needs"],
        "goal":c["goal"],
        "beliefs":c.get("beliefs", [])[-8:],
        "memory":c.get("memory", [])[-8:],
        "compressed_memory":c.get("compressed_memory", [])[-5:],
        "perception":focused,
        "suspicion":c.get("suspicion", {}),
        "conversation_id":c.get("conversation_id"),
        "news":world.get("news", [])[-5:],
        "hazards":world.get("hazards", [])[-8:],
        "inventory":c.get("inventory", []),
        "health":c.get("health"),
        "intoxication":c.get("intoxication"),
        "addiction":c.get("addiction"),
        "cravings":c.get("cravings"),
        "withdrawal":c.get("withdrawal"),
        "relationships":rels,
        "objects":list(world.get("objects", {}).values())
    }
