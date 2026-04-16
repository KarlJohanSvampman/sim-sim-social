This is a full-project merged archive.

Base used:
- v20_cors_profiles_nav_fix.zip

Included fix:
- backend/main.py import corrected so:
  - WebSocket and WebSocketDisconnect are imported from fastapi
  - CORSMiddleware is imported from fastapi.middleware.cors

No manual edits should be required before rebuild.

Suggested rebuild:
docker compose down
docker compose build --no-cache
docker compose up
