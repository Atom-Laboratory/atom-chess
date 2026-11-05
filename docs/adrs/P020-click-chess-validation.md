# P020 — Click moves validated by Chess Core

The console submits a proposed UCI move with the successfully completed move
history to a C++ command-line bridge. Chess Core replays and validates history,
validates the proposal, and TaskPlanner decomposes captures and castling.
The bridge returns the pre-move FEN and ordered physical steps. Python maps
capture removals to the captured physical identity home slot. The logical
history advances only when every physical step succeeds. Partial failure
preserves confirmed physical progress and blocks further chess dispatch.
Promotion is rejected before movement until replacement is available.
The bridge uses synthetic XY solely for decomposition. MuJoCo endpoints come
from the configured scene. This is task integration, not C++ trajectory playback.
