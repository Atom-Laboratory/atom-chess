# P017 — Fixed home slots in two-row Graveyards

Each color has two rows of eight. The first row maps A1–H1 for white and
A8–H8 for black. The second maps A2–H2 and A7–H7 respectively. The piece
manifest binds stable identity to its home slot once at scene construction.
Runtime square names are not used to derive identity or the destination slot.
Configured home slots are enforced at dispatch. Legacy slots remain supported.
This change does not qualify piece contact geometry, masses or material properties.
Official mesh visuals still use experimental primitive colliders. Physics model
qualification remains required before reinforcement learning is enabled.
