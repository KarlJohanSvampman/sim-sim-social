def compress_memories(c):
    if len(c.get("memory", [])) >= 10:
        c.setdefault("compressed_memory", []).append({"memory_id":f"m_{len(c.get('compressed_memory', []))+1}","time_range":"recently","summary_belief":"A stressful sequence of events happened.","emotional_core":"stress","confidence_in_memory":0.6,"self_justification":None,"associated_topics":[],"related_people":[],"concealment_tendency":0.2,"volatility":0.3})
        c["memory"]=c["memory"][-3:]
