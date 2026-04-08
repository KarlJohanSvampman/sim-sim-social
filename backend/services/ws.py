from copy import deepcopy
from uuid import uuid4

class Manager:
    def __init__(self):
        self.clients = {}

    async def connect(self, ws):
        await ws.accept()
        cid = str(uuid4())
        self.clients[cid] = {"ws": ws, "thoughts_enabled": True}
        return cid

    def disconnect(self, cid):
        self.clients.pop(cid, None)

    def set_thoughts_enabled(self, cid, enabled):
        if cid in self.clients:
            self.clients[cid]["thoughts_enabled"] = enabled

    async def send_personal(self, cid, data):
        client = self.clients.get(cid)
        if not client:
            return
        payload = deepcopy(data)
        if not client["thoughts_enabled"]:
            for c in payload.get("characters", {}).values():
                c["thoughts"] = None
        await client["ws"].send_json(payload)

    async def broadcast(self, data):
        dead = []
        for cid, client in self.clients.items():
            payload = deepcopy(data)
            if not client["thoughts_enabled"]:
                for c in payload.get("characters", {}).values():
                    c["thoughts"] = None
            try:
                await client["ws"].send_json(payload)
            except Exception:
                dead.append(cid)
        for cid in dead:
            self.disconnect(cid)

manager = Manager()
