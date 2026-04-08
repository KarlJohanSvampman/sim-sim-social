def filter_attention(perception, bandwidth=4):
    def score(ev):
        s=ev.get("certainty",0.1)
        if ev["data"].get("entity_type")=="hazard":
            s += 1.0
        if ev["type"]=="auditory":
            s += 0.2
        return s
    return sorted(perception, key=score, reverse=True)[:bandwidth]
