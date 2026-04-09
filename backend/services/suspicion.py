def update_suspicion(observer, speaker_id, statement):
    susp=observer.setdefault("suspicion", {})
    base=susp.get(speaker_id,0.0)
    if statement.get("is_lie"):
        base += 0.3
    else:
        base *= 0.97
    susp[speaker_id] = min(1.0, base)
