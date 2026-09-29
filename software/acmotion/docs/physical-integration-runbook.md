# BLOCKER: Dejan How To Mechatronics Joint 3

The selected physical SCARA is Dejan's How To Mechatronics design. That arm uses four NEMA 17 driven DOFs: J1, J2, J3 and Z, with a separate servo gripper.

Current acmotion models J1, J2, Z and gripper only. Issue #160 tracks the missing J3/orientation contract.

**Do not start autonomous powered Cartesian motion from this runbook until #160 is resolved.**

The setup, build, calibration-recording, protocol-only and read-only serial sections below are still valid.

# acmotion — Physical Integration Runbook

This runbook is the operational guide for bringing the ATOM Chess motion stack from a clean Linux SBC to the first controlled SCARA movements.

It complements the architectural decisions in:

- `software/docs/adrs/ADR-002-acmotion-sbc-esp32-boundary.md`
- `software/docs/adrs/ADR-003-task-planner-physical-task-boundary.md`
- `software/docs/adrs/ADR-004-inverse-kinematics-on-sbc.md`
- `software/docs/adrs/ADR-005-acm1-motion-protocol.md`

## 1. Safety prerequisites

Before powering motor drivers:

- secure the SCARA base mechanically;
- verify the emergency-stop circuit independently of software;
- verify limit/endstop wiring;
- set DRV8825 current limits according to the actual motors;
- keep the 12 V motor rail disconnected during protocol-only testing;
- verify common ground between the SBC/ESP32 logic and motor-control electronics;
- ensure the Z axis cannot fall freely when power is removed;
- establish a clear physical emergency-stop procedure.

Software tests do not replace electrical/mechanical safety checks.

## 2. Supported Linux workflow

The core motion stack is designed to build on a headless Linux SBC without ROS2.

Recommended environment:

- Ubuntu 24.04 / Armbian based on Ubuntu 24.04;
- CMake >= 3.23;
- Ninja;
- GCC or Clang;
- Git;
- Python 3 for serial diagnostics;
- Stockfish/OpenCV may still be required by the repository-wide build.

From the repository root:

```bash
bash software/acmotion/scripts/setup_linux.sh
bash software/acmotion/scripts/build_and_test.sh
```

The second script performs a headless repository build and executes CTest.

## 3. Verify acmotion without hardware

Run the module-focused test subset:

```bash
ctest --test-dir build --output-on-failure -R "motion|task|graveyard|coordinate|inverse"
```

Expected before hardware integration:

- CoordinateMapper tests pass;
- GraveyardAllocator tests pass;
- TaskPlanner tests pass;
- MotionPlanner tests pass;
- MotionProtocol tests pass;
- MotionExecution tests pass;
- InverseKinematics tests pass.

## 4. Record physical robot geometry

Do not edit source code to insert real robot dimensions.

Record the measured/CAD values in your hardware configuration source:

- link 1 length, mm;
- link 2 length, mm;
- joint 1 minimum/maximum, rad;
- joint 2 minimum/maximum, rad;
- Z minimum/maximum, mm;
- joint zero/reference positions;
- selected elbow configuration;
- tool-center-point offset, if present.

The current IK API expects these values through `ScaraGeometry`.

## 5. Establish the SCARA coordinate frame

Before board calibration, document:

- base-frame origin;
- +X direction;
- +Y direction;
- +Z direction;
- positive joint-1 rotation;
- positive joint-2 rotation;
- board plane Z;
- gripper/tool-center reference.

Use one convention consistently in:

- CAD;
- CoordinateMapper calibration;
- IK configuration;
- firmware motor direction;
- integration logs.

If one layer inverts an axis independently, physical targets will be wrong even when unit tests pass.

## 6. Calibrate the chessboard

CoordinateMapper assumes a fixed board relative to the SCARA.

Measure and store:

- A1 physical coordinate;
- H1 physical coordinate;
- board orientation/rank direction;
- graveyard origins;
- graveyard row/column steps.

Validate several known squares before attempting a pick:

```
a1
h1
a8
h8
e4
```

The measured physical position should match the mapped point within the mechanical tolerance accepted by the project.

## 7. Validate IK offline

Before connecting the ESP32:

1. create `ScaraGeometry` from measured values;
2. solve known Cartesian points;
3. independently calculate or measure expected joint angles;
4. reject points outside the physical workspace;
5. verify both configured joint limits and Z limits.

Do not use the default values from unit tests as robot configuration. They are synthetic fixtures only.

## 8. Prepare Linux serial access

List serial devices:

```bash
ls -l /dev/ttyUSB* /dev/ttyACM* 2>/dev/null || true
```

Check group ownership:

```bash
stat -c '%n %U %G %a' /dev/ttyUSB0
```

On Debian/Ubuntu systems, serial devices are commonly assigned to `dialout`.

If required:

```bash
sudo usermod -aG dialout "$USER"
```

Log out and back in after changing group membership.

Do not use `chmod 777` as a persistent serial-device fix.

## 9. Protocol-only bring-up

Keep motor power disabled.

Run the read-only serial monitor:

```bash
python3 software/acmotion/scripts/serial_monitor.py \
  --device /dev/ttyUSB0 \
  --baud 115200
```

Then reset the ESP32-S3 and inspect startup/protocol lines.

Expected runtime protocol is documented in ADR-005.

Do not send movement commands until:

- parser framing is verified;
- sequence IDs are echoed correctly;
- ACK/DONE semantics are implemented;
- ERR/ESTOP/LIMIT can be observed.

## 10. First powered test

Use conservative settings:

- low motor current appropriate for safe bench testing;
- low velocity;
- low acceleration;
- one axis at a time;
- no chess pieces;
- no camera dependency;
- operator within reach of hardware E-stop.

Test order:

1. joint 1 small positive/negative move;
2. joint 2 small positive/negative move;
3. Z small positive/negative move;
4. gripper open/close;
5. each limit switch independently;
6. emergency stop during motion;
7. two-joint coordinated move;
8. Cartesian point produced through IK;
9. board-square approach with gripper open;
10. only then test pick-and-place.

## 11. First board transfer

Use a single disposable/test piece and a central board square.

Recommended sequence:

1. map source/target with CoordinateMapper;
2. TaskPlanner produces one PhysicalTask;
3. MotionPlanner expands it to Pose[];
4. IK converts every Pose to joint targets;
5. inspect/log all targets before execution;
6. MotionExecution sends segments;
7. firmware returns ACK/DONE for each segment;
8. verify the final physical position manually.

Do not begin with captures, graveyard movements or castling.

## 12. Special-move validation order

After simple transfers are repeatable:

1. normal capture;
2. graveyard allocation;
3. en passant;
4. castling;
5. promotion strategy only after physical replacement mechanics are defined.

## 13. Logging checklist

For every physical integration failure, capture:

- Git commit SHA;
- SBC model and OS version;
- ESP32 firmware version/commit;
- serial device and baud;
- ScaraGeometry values;
- CoordinateMapper calibration values;
- JointSegment sequence;
- raw ACM1 command;
- raw controller response;
- E-stop/limit state;
- motor power/current configuration;
- observed physical behavior.

This information should accompany hardware-related GitHub issues.

## 14. Definition of physical integration readiness

The motion stack is ready for end-to-end MVP integration when:

- repository CI is green;
- coordinate calibration is repeatable;
- IK is validated against measured geometry;
- serial transport is stable;
- ACK/DONE/ERR/ESTOP/LIMIT are implemented on firmware;
- one-axis and multi-axis tests pass;
- simple pick-and-place is repeatable;
- capture/graveyard flow works;
- emergency stop reliably enters a safe physical state.

Only after these checks should the Game Coordinator/FSM own autonomous execution.
