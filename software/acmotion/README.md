# acmotion

`acmotion` is the high-level motion subsystem of ATOM Chess.

It runs primarily on the Linux SBC / Brain and converts validated chess moves into physically executable SCARA motion while keeping low-level motor control on the ESP32-S3.

## Runtime pipeline

```
ac::chess::Move
    ↓
TaskPlanner
    ↓
PhysicalTask[]
    ↓
MotionPlanner
    ↓
Pose[]
    ↓
InverseKinematics
    ↓
JointSegment[]
    ↓
MotionExecution
    ↓
ACM1 / IMotionTransport
    ↓
ESP32-S3
    ↓
interpolation / motion profile / STEP-DIR
```

## Component responsibilities

| Component | Responsibility | Runtime |
| --- | --- | --- |
| CoordinateMapper | Board/graveyard → calibrated XY | Linux SBC |
| GraveyardAllocator | Deterministic captured-piece slot allocation | Linux SBC |
| TaskPlanner | Validated Move → ordered PhysicalTask[] | Linux SBC |
| MotionPlanner | Physical transfer → safe Pose[] | Linux SBC |
| InverseKinematics | Pose → joint-space target | Linux SBC |
| MotionExecution | JointSegment sequencing and controller responses | Linux SBC |
| MotionProtocol | ACM1 encoding/parsing | Linux SBC + compatible firmware |
| ESP32-S3 firmware | Interpolation, profiles, STEP/DIR, limits, E-stop | ESP32-S3 |

## Documentation

Start here for physical integration:

- [Physical integration runbook](docs/physical-integration-runbook.md)
- [Physical calibration template](docs/physical-calibration-template.md)

Architecture decisions:

- [ADR-002 — SBC/ESP32 boundary](../docs/adrs/ADR-002-acmotion-sbc-esp32-boundary.md)
- [ADR-003 — TaskPlanner/PhysicalTask boundary](../docs/adrs/ADR-003-task-planner-physical-task-boundary.md)
- [ADR-004 — IK on SBC](../docs/adrs/ADR-004-inverse-kinematics-on-sbc.md)
- [ADR-005 — ACM1 protocol](../docs/adrs/ADR-005-acm1-motion-protocol.md)

## Linux quick start

From repository root:

```bash
bash software/acmotion/scripts/setup_linux.sh
bash software/acmotion/scripts/build_and_test.sh
bash software/acmotion/scripts/preflight_linux.sh
```

For a specific serial device:

```bash
bash software/acmotion/scripts/preflight_linux.sh /dev/ttyUSB0
python3 software/acmotion/scripts/serial_monitor.py \
  --device /dev/ttyUSB0 \
  --baud 115200
```

The serial monitor is intentionally read-only.

## Build without ROS2

ROS2/ament remains optional for the MVP motion core.

Repository headless build:

```bash
cmake -S . -B build -G Ninja \
  -DCMAKE_BUILD_TYPE=Debug \
  -DACCHESS_BUILD_VIEWER=OFF \
  -DACVISION_BUILD_HARDWARE_TESTS=OFF

cmake --build build --parallel
ctest --test-dir build --output-on-failure
```

## Rules for contributors

- Do not introduce production mocks into runtime motion code.
- Do not duplicate chess legality in `acmotion`.
- Do not put FEN, Board, PieceType or chess-square semantics in ESP32 firmware.
- Do not hard-code physical SCARA dimensions in the IK solver.
- Do not bypass CoordinateMapper with duplicated physical board constants.
- Keep units explicit in public APIs and Doxygen.
- Hardware-independent tests must remain runnable on CI.
- New hardware/protocol decisions should receive an ADR.
