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
$base = 'simulation/mujoco/assets/bundles/playground-fingertip-only-v1'
$scene = 'simulation/mujoco/training/camera-manipulation/runs/exercise-p038/reference-validation/reference-scene.xml'
$layout = 'docs/camera-rl/evidence-p035/high-camera-layout.json'
$out = Join-Path simulation/mujoco/runs ('capture-' + [guid]::NewGuid().ToString('N'))

& $py -B simulation/mujoco/examples/prepare_capture_task/prepare_capture_task.py --bundle $base --reference-scene $scene --layout $layout --output $out --attacker-piece white_pawn_e2 --attacker-source e4 --attacker-target d5 --captured-piece black_pawn_e7 --captured-source d5
if ($LASTEXITCODE -ne 0) { throw 'Capture fixture preparation failed' }

& $py -B simulation/mujoco/playground/run.py --bundle $out --headless --request (Join-Path $out 'playground_request.json') --output (Join-Path $out 'result.json')
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
& $py -B simulation/mujoco/playground/run.py --bundle $out
~~~

In the window, select **Execute Chess Core request file** and open
playground_request.json from the generated folder. This button accepts a physical
plan. The normal chess move controls expect a full chess position.

The success check uses MuJoCo physical state. This fixture does not establish
visual capture verification, full-board capture reliability, or hardware parity.

## Inspect the camera-only inputs

The camera inspection command renders RGB and runs native acvision. It writes
the original images, rectified board images when available, and report.json.
This inspection exits with code 1 and BLOCKED_BEFORE_MOTION because the current
pipeline lacks a qualified grasp pose, visual grip/release verification and
visual occupancy of the selected Graveyard slot.

~~~powershell
$inspection = Join-Path simulation/mujoco/runs ('capture-camera-' + [guid]::NewGuid().ToString('N'))
& $py -B simulation/mujoco/examples/prepare_capture_task/inspect_camera_capture.py --bundle $out --library build/p038-core/bin/Release/acvision_runtime.dll --output $inspection
Get-Content (Join-Path $inspection 'report.json')
~~~

The tested fixture yielded three oriented frames with white candidates at e4
and black candidates at d5. They were static observations. The commands above
for executing playground_request.json use the MuJoCo oracle. See
[ADR P040](../../../../docs/adrs/P040-camera-capture-evidence.md) for the camera
evidence required before a camera-only transfer can proceed.

## Validate the Graveyard camera region

~~~powershell
$slotRun = Join-Path simulation/mujoco/runs ('graveyard-vision-' + [guid]::NewGuid().ToString('N'))
& $py -B simulation/mujoco/examples/prepare_capture_task/validate_graveyard_camera.py --bundle $out --library build/p038-core/bin/Release/acvision_runtime.dll --output $slotRun
Get-Content (Join-Path $slotRun 'report.json')
~~~

The validator calibrates a pixel region using the fixed virtual camera and
static support geometry. The estimator receives an empty-slot RGB frame,
the calibrated polygon, and current RGB observations with native ArUco
registration. Loss of registration or excessive image drift yields unknown.

The tested static fixtures produced 0% changed pixels when black_13 was empty,
77.7% with the pawn in black_13, and 0% with the pawn in black_14.
The test harness positions pieces to generate labeled images. No piece pose
is passed to the estimator. The thresholds apply to this experimental camera
and lighting. Foreground can also come from the arm, a shadow or another object.
This evidence needs a clear observation pose and separate identity/release checks
before it can authorize the second transfer. See
[ADR P040](../../../../docs/adrs/P040-camera-capture-evidence.md).

## Run the camera-gated capture

This separate executor uses the existing C++ nominal planner and MuJoCo
controller. Fresh RGB observations at the parked arm pose gate both transfers.
It checks the initial occupancy, then requires d5 to clear and black_13 to
show foreground before moving the attacker. It checks the final pattern again
after retreat. The decision path uses RGB and static scene calibration.

~~~powershell
$cameraRun = Join-Path simulation/mujoco/runs ('rgb-capture-' + [guid]::NewGuid().ToString('N'))
& $py -B simulation/mujoco/examples/prepare_capture_task/run_camera_capture.py --bundle $out --library build/p038-core/bin/Release/acvision_runtime.dll --motion-library build/p038-core/bin/Release/motion_runtime.dll --output $cameraRun
Get-Content (Join-Path $cameraRun 'report.json')
~~~

The tested centered-pawn fixture returned COMPLETED_RGB_TRANSITIONS with two
completed transfers. Review before.png, removed.png and placed.png. A failed
visual transition or nominal swept preflight stops the sequence.

The executor matches RGB crops against synthetic calibration images of each
known pawn at 1 mm XY increments. The search extent comes from the support
half-width minus the pawn-base radius. The best consistent match supplies
pick XY. Static support and stem geometry supply Z. Before the attacker
moves, the black pawn must also match its appearance at the Graveyard slot.
After retreat, both placed pawns must match their respective appearances. The fixed camera and empty calibration are experimental. The board
foreground threshold is 7% and the Graveyard threshold is 25% in the central
regions. These checks measure visible region changes after retreat. They do
not distinguish every occluder or verify a grip during transport. Swept
preflight uses a reconstructed scene populated from RGB estimates
and models a joint-linear path. Live actuator dynamics can deviate from it.

To reproduce a displaced-piece trial, add --fixture-offset-mm 2 -2 -2 2
to the run_camera_capture.py command, with a fresh output directory. The first
two values move the white pawn in world XY and the last two move the black
pawn. They configure the simulation fixture only. The estimator searches the
same calibration grid regardless of those values. Inspect grasp_estimates in
report.json for the image matches and fit errors.

Both tested opposite ±2 mm arrangements completed both transfers. Calibration
and thresholds are specific to the two known pawn meshes, fixed virtual
camera, lighting and clear observation pose. This remains a controlled
simulation example. Physical use requires real calibration images or a
qualified camera/appearance model and validation under occlusion.

## Watch live RGB and homography during the capture

Add --preview to the run_camera_capture.py command above, using a fresh output
directory. The left panel shows the live RGB frame. The right panel shows
the board rectified by acvision from that same frame. The text below shows
the image-to-board matrix and the motion phase. If the references are
occluded, the right panel clears and reports that homography is unavailable.
The final frame stays visible until the window closes.

Tk runs on the main thread. Simulation, image rendering and native perception
run on a worker. The window displays the newest available frame and skips
older ones when necessary. Preview frames are sampled during motion. The
post-retreat verification still uses its own three observations. Closing
the window hides the preview while the local simulation finishes.

## Use the shared H-file camera

Generate a matching reference scene with validate_board_reference.py using
--layout simulation/mujoco/configs/perception/h-file-layout.json
and the existing docs/camera-rl/aruco-assets-v4 marker textures. Use its
reference-scene.xml and the same layout when preparing the capture fixture.
The shared camera is selected automatically. For a historical scene that used
azimuth 270, supply --camera-config with a JSON file containing {"azimuth": 270}.
The override and the marker scene should match the experiment.

The centered e4-to-d5 fixture completed both RGB-gated transfers with the
H-file camera. This verification uses the five-actuator model.

Crowded capture fixtures accept repeated --obstacle piece_name@square options.
The camera executor checks neighbor images after victim removal and attacker
placement. On wrist-enabled bundles, --wrist-deg accepts four angles in
remove-pick, remove-place, attack-pick and attack-place order. Each transfer
still runs swept collision preflight using nominal bystander poses. Inspect
neighbor_change in report.json after each completed observation gate. A
checked fixture with eight bystanders and wrist angles of 180 degrees was
rejected at the descent preflight before either transfer.
