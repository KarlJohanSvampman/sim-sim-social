def small_inventory_count(character):
    return len([i for i in character.get("inventory", []) if i.get("size")=="small"])
def pickup_from_object(character, obj, prefer_effect=None):
    inv=obj.get("inventory", [])
    if not inv: return None
    idx=0
    if prefer_effect:
        for i, item in enumerate(inv):
            if prefer_effect in item.get("effects", {}):
                idx=i; break
    item=inv.pop(idx)
    if small_inventory_count(character) >= character.get("carry_capacity_small", 4):
        return None
    character.setdefault("inventory", []).append(item)
    return item
def has_consumable_for(character, need_key):
    for item in character.get("inventory", []):
        if need_key in item.get("effects", {}):
            return item
    return None
def consume_item(character, item_id):
    inv=character.setdefault("inventory", [])
    item=next((it for it in inv if it["id"]==item_id), None)
    if not item: return False
    for k,v in item.get("effects", {}).items():
        if k in character["needs"]:
            character["needs"][k]=max(0,min(100,character["needs"][k]+v))
        elif k=="intoxication":
            character["intoxication"]=max(0,min(100,character.get("intoxication",0.0)+v))
        elif k=="alcohol_use":
            character["addiction"]["alcohol"]=min(100,character["addiction"]["alcohol"]+v)
            character["cravings"]["alcohol"]=max(0,character["cravings"]["alcohol"]-15)
        elif k=="tobacco_use":
            character["addiction"]["tobacco"]=min(100,character["addiction"]["tobacco"]+v)
            character["cravings"]["tobacco"]=max(0,character["cravings"]["tobacco"]-15)
    inv.remove(item); return True
