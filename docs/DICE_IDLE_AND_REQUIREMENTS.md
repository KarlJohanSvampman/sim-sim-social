This patch changes idle behavior and activity eligibility.

Idle roaming rule:
- when a tagged sim becomes idle, it rolls 2d6
- the sum becomes roam_tiles_remaining
- the sim walks that many tiles before stopping again
- only on doubles 1+1, 4+4, or 6+6 does it attempt to engage an activity
- after an activity completes, the sim rolls again

Activity requirement rule:
- activities are only considered when the required nearby objects, tile types, or room tags are present
- seeded examples include:
  - bed / bedroom
  - stove + food / kitchen
  - tv / living_room
  - restroom / bathroom
  - smartphone/computer
