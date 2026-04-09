def propagate_gossip(speaker, others, memory_event):
    for other in others:
        if other["id"] != speaker["id"]:
            other.setdefault("memory", []).append({"type":"gossip","about":speaker["id"],"content":memory_event})
