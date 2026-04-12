ITEMS = {
    "item_apple": {
        "id": "item_apple",
        "name": "Apple",
        "type": "consumable",
        "icon": "icons/apple.png",
        "description": "A fresh apple.",
        "weight": 0.2,
        "effects": {"hunger": -12}
    },
    "item_water": {
        "id": "item_water",
        "name": "Water Bottle",
        "type": "consumable",
        "icon": "icons/water.png",
        "description": "A bottle of water.",
        "weight": 0.5,
        "effects": {"thirst": -20}
    }
}

def list_items():
    return list(ITEMS.values())

def get_item(item_id):
    return ITEMS.get(item_id)

def upsert_item(payload):
    ITEMS[payload["id"]] = payload
    return payload

def delete_item(item_id):
    ITEMS.pop(item_id, None)
