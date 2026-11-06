# P030 — Live arena as an optional training display

Mirror independent worker states into a single render-only MuJoCo scene.
Sample the display at most five times per second, with no intentional
training delay. Headless collection avoids display and state transfer costs.
The viewer uses simplified chess geometry and a shared mesh set. Each worker
keeps its own physics state while contributing to the same PPO policy.
