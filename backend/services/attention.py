def filter_attention(perception, bandwidth=4):
    return sorted(perception, key=lambda ev: ev.get("certainty",0.1)+(0.2 if ev["type"]=="auditory" else 0), reverse=True)[:bandwidth]
