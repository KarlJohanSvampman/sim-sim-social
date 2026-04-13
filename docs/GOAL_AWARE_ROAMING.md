This patch replaces random idle stepping with goal-aware roaming.

New behavior:
- when a sim becomes idle and rolls 2d6, the sum sets a roaming budget
- instead of picking arbitrary next steps, the sim picks a local destination
- destinations are chosen from nearby tiles based on:
  - current needs
  - nearby room tags
  - nearby objects
  - intelligence spectrum bias
  - ranked interests
- examples:
  - sleepy sims prefer bedrooms / beds
  - hungry sims prefer kitchens / food / stove
  - stressed sims prefer living rooms or yards
  - EQ-skewed sims mildly prefer social rooms
  - IQ-skewed sims mildly prefer quiet rooms

Added fields:
- roam_target
- roam_path
