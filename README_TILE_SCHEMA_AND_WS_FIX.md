This update adds richer tile data and fixes websocket support.

Websocket fix:
- `backend/requirements.txt` now uses `uvicorn[standard]`
- rebuild with:
  ```bash
  docker compose down
  docker compose build --no-cache backend
  docker compose up
  ```

Added tile fields:
- `lot_id`
- `zone_type`
- `elevation`
- `road`
- `sidewalk`
- `building_id`
- `interactions`
- `cover_value`
- `noise_modifier`
- `light_level`

Base tile fields:
- `x`
- `y`
- `z`
- `type`
- `blocks_movement`
- `blocks_sight`

Example tile:
```json
{
  "x": 2,
  "y": 2,
  "z": 0,
  "type": "house_floor",
  "blocks_movement": false,
  "blocks_sight": false,
  "lot_id": "lot_a",
  "zone_type": "residential",
  "elevation": 0.0,
  "road": false,
  "sidewalk": false,
  "building_id": "house_a",
  "interactions": ["walk", "inspect"],
  "cover_value": 0.0,
  "noise_modifier": 1.0,
  "light_level": 0.8
}
```
