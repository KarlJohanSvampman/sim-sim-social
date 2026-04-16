This archive fixes profile saving and simplifies the navigation.

Fixes:
- enables CORS in backend/main.py so browser preflight OPTIONS /tagged-profiles succeeds
- removes duplicate Character Creator tab
- renames Tagged Profiles tab to Profiles
- defaults the frontend to the Profiles page if it was still using the old creator page state

Why saves were failing:
- frontend on localhost:3000 triggered CORS preflight
- backend returned 405 to OPTIONS /tagged-profiles
- POST never reached the route handler
