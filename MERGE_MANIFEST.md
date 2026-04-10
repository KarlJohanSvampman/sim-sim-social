# Merge manifest

- Base zip: `merged_all_archives_repo.zip`
- Overlay applied: `form_based_character_creator_repo.zip`

- Overwritten file count: **12**

## Overwritten files

- `backend/main.py`
- `backend/services/db.py`
- `backend/services/institutions.py`
- `backend/services/memory_recall.py`
- `backend/services/operator.py`
- `backend/services/state.py`
- `backend/services/tick.py`
- `frontend/index.html`
- `frontend/package.json`
- `frontend/src/App.jsx`
- `frontend/src/main.jsx`
- `frontend/vite.config.js`

## Note

This merged archive uses `merged_all_archives_repo.zip` as the base and applies the form-based character creator changes on top. That form-based repo already contains the personality/body/mind/render profile work, so the latest merged zip includes both sets of changes.
