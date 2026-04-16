This archive fixes:
- Character Creator tab now shows the full tagged profile editor form again.
- Debug and Tile Types page crash fixed.

Root cause of the crash:
- some pages passed an async loader directly to useEffect
- React treated the returned Promise as a cleanup handler on unmount
- switching tabs then produced: TypeError: destroy is not a function

Fix:
- useEffect now calls load() inside a sync callback instead of returning a Promise
