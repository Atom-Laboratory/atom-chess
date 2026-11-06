# P030 — Live arena as an optional training display

Mirror independent worker states into a single render-only MuJoCo scene.
Sample the display at most five times per second, with no intentional
training delay. Headless collection avoids display and state transfer costs.
The viewer uses simplified chess geometry and a shared mesh set. Each worker
keeps its own physics state while contributing to the same PPO policy.

The arena copies compiled source poses. Before writing mesh geoms back to
MJCF it removes each mesh asset pose, which the compiler reapplies. This
avoids offsetting and rotating CAD parts twice. The live arena also uses
the source piece meshes when present. Verified positions and orientations
against 212 source geom instances across two stations.
