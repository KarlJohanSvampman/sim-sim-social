This archive patches the backend import error:

ImportError: cannot import name 'create_object' from 'services.state'

Fix applied:
- restored create_object() in backend/services/state.py
- restored move_object() in backend/services/state.py

Rebuild:
docker compose down
docker compose build --no-cache backend
docker compose up
