# Prepare and run a two-piece capture

This example uses the current five-actuator prototype. It prepares a white pawn
at e4 and a black pawn at d5, then runs a supervised physical capture through
the Playground. The black pawn goes to its assigned Graveyard slot first.
This is a deterministic simulation exercise. The P038 PPO launcher expects a
separate one-piece fixture.

Run from the repository root in Windows PowerShell. Install the Python
environment using the [MuJoCo README](../../README.md).

## Select matching inputs

- **Bundle** is the full interactive scene folder with model.xml and
  manifest.json. Use playground-fingertip-only-v1.
- **Reference scene** is reference-scene.xml generated from that same bundle
  with the high-camera layout. If it is missing, follow steps 3–4 of the
  [MuJoCo README](../../README.md) and use the generated $base and $reference.
- **Layout** is the high-camera-layout.json used when generating that XML.
- **Graveyard slot** comes from the captured piece's manifest record. In this
  example black_pawn_e7 is assigned black_13. Its coordinates come from the
  scene. Optional --graveyard-slot and --graveyard-position arguments must
  agree with the existing assignment and slot geometry.

If you generated a fresh reference scene, replace the two path assignments
for $base and $scene below with your generated $base and
(Join-Path $reference "reference-scene.xml").

## Prepare the fixture and execute it headless

~~~powershell
$py = '.\simulation\mujoco\.venv\Scripts\python.exe'
$base = 'simulation/mujoco/runs/playground-fingertip-only-v1'
$scene = 'simulation/mujoco/runs/exercise-p038/reference-validation/reference-scene.xml'
$layout = 'docs/camera-rl/evidence-p035/high-camera-layout.json'
$out = Join-Path simulation/mujoco/runs ('capture-' + [guid]::NewGuid().ToString('N'))

& $py -B simulation/mujoco/examples/prepare_capture_task/prepare_capture_task.py --bundle $base --reference-scene $scene --layout $layout --output $out --attacker-piece white_pawn_e2 --attacker-source e4 --attacker-target d5 --captured-piece black_pawn_e7 --captured-source d5
if ($LASTEXITCODE -ne 0) { throw 'Capture fixture preparation failed' }

& $py -B simulation/mujoco/examples/simulation_playground.py --bundle $out --headless --request (Join-Path $out 'playground_request.json') --output (Join-Path $out 'result.json')
~~~

On this tested fixture, the result is COMPLETED_SIMULATION_ORACLE with
completed_transfers equal to 2. Check these fields in result.json. If the first
transfer fails, the Playground reports the reason and does not run the second.

The new directory contains model.xml, manifest.json, copied assets,
reference-layout.json, capture_task.json with the scenario details, and
playground_request.json with the executable schema-2 plan. The run command adds
result.json. Use a fresh output folder to prepare the fixture again and a new
result filename for each execution.

## Watch the capture

~~~powershell
& $py -B simulation/mujoco/examples/simulation_playground.py --bundle $out
~~~

In the window, select **Execute Chess Core request file** and open
playground_request.json from the generated folder. This button accepts a physical
plan. The normal chess move controls expect a full chess position.

The success check uses MuJoCo physical state. This fixture does not establish
visual capture verification, full-board capture reliability, or hardware parity.
