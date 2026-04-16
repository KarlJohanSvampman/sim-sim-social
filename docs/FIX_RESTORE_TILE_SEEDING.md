This archive restores grid tile seeding in backend/services/state.py.

It fixes the issue where:
- /world returned "grid.tiles": {}
- the frontend showed only the red/blue axes lines
- activity requirement checks could not inspect real tiles/rooms

Included in the fix:
- 12x12 seeded grid
- border walls + interior floors
- room tags (bedroom, kitchen, living_room, bathroom, yard)
- seeded objects for activity requirements
- restored create_object() and move_object()
- init() called at module load

Base archive used:
- v12_dice_idle_requirements_fix_state.zip

Rebuild:
docker compose down
docker compose build --no-cache backend
docker compose up

Verify:
- open http://localhost:8000/world
- confirm grid.tiles has 144 entries
