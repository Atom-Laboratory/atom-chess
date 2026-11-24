# P016 — Official piece visuals and visible playback

## Context

The exported CAD meshes were separate from the generated scene. P015 target
playback advanced simulation faster than wall time, making short motions hard
to follow in the passive viewer.

## Decision

The launcher creates a new bundle with official_piece_visuals enabled. Mesh
hashes are checked against the export manifest. Each piece uses its millimetre
visual asset at scale 0.001 and its bottom-centered origin. Existing experimental
contact primitives remain hidden in geom group 3. The scene manifest names both
representations. Viewer callbacks pace control frames to the existing simulation
interval. Headless execution retains its current timing.

## Consequences

The official silhouettes are visible and copied into immutable bundles. Contact
shapes and inertial properties still require physical qualification. The larger
visuals can extend beyond the current contact proxies. This option therefore
updates visual fidelity, not manipulation geometry or collision guarantees.
