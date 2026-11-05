# P012 — Playground endpoint grid

## Context

Square dropdowns hide occupancy and cannot select Graveyard endpoints.

## Decision

Display the confirmed snapshot as an 8×8 board and two 4×4 Graveyard grids.
Both selection roles can use either endpoint type. Board transfers use the
existing MOVE envelope. Graveyard transfers use a single-transfer PLAN.
Selection highlights use the same blue and gold colors in Tk and the MuJoCo
viewer. Viewer overlays never become physics geoms.

The launcher uses a new experimental scene with 32 named physical supports.
It keeps older bundles intact. Older bundles show their available slots and
disable unconfigured tiles. Slot color organizes the display. This fixture
does not establish reachability or calibrated layout.
