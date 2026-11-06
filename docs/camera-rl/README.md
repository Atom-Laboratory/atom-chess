# Camera-based manipulation and RL

This module documents the proposed transition from the isolated E2 pixel-lift
experiment to camera-guided manipulation through the actual ATOM modules.

1. [Current implementation audit](phase-a-audit.md): observations, reward, modules,
   firmware evidence, Git state and limitations.
2. [Architecture and validation roadmap](design-and-validation.md): coordinate
   frames, contracts, bounded actions, reward, randomization and phase gates.
3. [P031 architecture decision](../adrs/P031-camera-based-perception-and-sim-to-real-rl.md):
   proposed decision and alternatives, pending review.
4. [Validation record](validation.md): what was actually checked.

Phase A is complete as a documentation increment. Phases B–F are not implemented.
No new training command is provided because the perception and conventional
baseline gates have not passed. Existing v3 experiments remain available and
unchanged; their successful lift episodes are not full chess transfers.

## Phase B1 update

The real native image bridge is implemented. See [run instructions and measured blockers](native-perception-guide.md). Initial lateral perception validation failed; subsequent environment and training phases remain gated. The Phase A status above describes the historical audit increment.

## P032 contract completion (2026-11-06)

See [schema 2, build commands, tests and acceptance report](p032-contract-completion.md). This supersedes the initial B1 contract limitations; detection algorithms remain unchanged.

## P033 geometry correction

See [pattern validation and projective corners](p033-geometry-validation.md).
