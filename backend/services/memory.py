from services.db import append_memory
def recall(c): return c.get("memory", [])[-8:]
def store(c, event):
    c.setdefault("memory", []).append(event)
    c["memory"]=c["memory"][-80:]
    append_memory(c["id"], event)
