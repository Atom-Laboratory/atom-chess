# ATOM Chess — Bring-up manual for Dejan / How To Mechatronics SCARA

This guide is specific to the SCARA robot from the How To Mechatronics tutorial by Dejan and the ATOM Chess electronics/software architecture.

Official mechanical reference:
https://howtomechatronics.com/projects/scara-robot-how-to-build-your-own-arduino-based-robot/

## 0. Important compatibility status

The reference robot uses:

- Joint 1 — NEMA 17 rotational axis;
- Joint 2 — NEMA 17 rotational axis;
- Joint 3 — NEMA 17 rotational/distal axis;
- Z axis — NEMA 17 + lead screw;
- gripper — MG996R servo.

ATOM currently models J1, J2, Z and gripper in `JointTarget`. J3 is not yet represented in the autonomous execution contract.

Issue #160 tracks that migration.

### What you can safely do before #160

- assemble and wire the robot;
- configure current limits;
- verify each motor independently;
- verify endstops;
- test servo independently;
- verify SBC ↔ ESP32 serial communication;
- run repository unit tests;
- measure mechanical geometry;
- calibrate coordinate frames;
- test J1/J2 IK numerically/offline;
- move individual axes with dedicated low-level firmware/test commands.

### What must wait for #160

Do not execute autonomous Cartesian ATOM trajectories on the complete arm until J3 is represented in:

- JointTarget;
- IK/orientation;
- ACM protocol;
- ESP32 firmware.

---

# 1. Mechanical inspection

Before electronics:

1. Check all printed parts for cracks.
2. Check that all three rotary joints move freely by hand.
3. Tension GT2 belts without over-tensioning bearings.
4. Check pulley set screws.
5. Verify there is no mechanical collision across the intended work area.
6. Verify the Z carriage moves freely along the rods.
7. Turn the lead screw manually through the intended Z range.
8. Verify the gripper can open/close without binding.
9. Keep the chessboard out of the workspace for the first powered tests.

Record backlash in each belt-driven joint.

Do not try to compensate backlash in software before measuring it.

---

# 2. Identify and label every actuator

Label connectors physically before connecting drivers.

Recommended labels:

```
M1 = Joint 1
M2 = Joint 2
M3 = Joint 3
M4 = Z axis
S1 = gripper servo
LS1 = Joint 1 reference/endstop
LS2 = Joint 2 reference/endstop
LS3 = Joint 3 reference/endstop
LSZ = Z reference/endstop
```

Use the same names in firmware, wiring diagrams, logs and calibration records.

---

# 3. ATOM electronics architecture

The original tutorial uses Arduino UNO + CNC Shield + A4988 drivers.

ATOM replaces the control architecture with:

```
Banana Pi / Linux SBC
        |
        | USB/UART - ACM protocol
        v
ESP32-S3
        |
        +--> DRV8825 J1 --> NEMA 17
        +--> DRV8825 J2 --> NEMA 17
        +--> DRV8825 J3 --> NEMA 17
        +--> DRV8825 Z  --> NEMA 17
        |
        +--> servo output --> MG996R gripper
        |
        +<-- endstops / E-stop
```

The Linux SBC performs high-level planning and IK.

The ESP32-S3 performs deterministic motor execution.

---

# 4. Power architecture

Use separate power domains conceptually:

## Motor rail

12 V supply → DRV8825 VMOT.

## Logic rail

Stable regulated logic supply → ESP32-S3.

## Servo rail

Use a suitable regulated supply for the MG996R.

Do not power the MG996R directly from a weak MCU regulator.

All control-domain grounds that exchange STEP/DIR/PWM signals must share a valid reference ground.

Before connecting motors:

1. disconnect motor power;
2. verify supply polarity;
3. verify 12 V rail;
4. verify logic supply;
5. verify servo supply;
6. verify common ground;
7. check for shorts with a multimeter.

---

# 5. DRV8825 preparation

For each axis:

1. install the driver with correct orientation;
2. install the bulk capacitor close to VMOT/GND;
3. configure microstepping consistently;
4. leave motor disconnected initially;
5. set the current limit before sustained motion.

Do not copy a current-limit value blindly.

Use the actual NEMA 17 rated phase current and the specific DRV8825 carrier-board sense resistor/calibration.

Record the final settings in:

`software/acmotion/docs/physical-calibration-template.md`

---

# 6. ESP32-S3 minimum firmware bring-up

Do not begin with ATOM autonomous firmware.

First create/flash a hardware-test firmware able to:

- toggle J1 STEP/DIR;
- toggle J2 STEP/DIR;
- toggle J3 STEP/DIR;
- toggle Z STEP/DIR;
- command the gripper;
- read every endstop;
- report E-stop;
- print state through serial.

Test with motor power disconnected first.

Expected serial diagnostics should identify every input explicitly.

Example conceptual output:

```
J1_LIMIT=0
J2_LIMIT=0
J3_LIMIT=0
Z_LIMIT=0
ESTOP=0
```

---

# 7. Linux preparation on Banana Pi

From repository root:

```bash
bash software/acmotion/scripts/setup_linux.sh
bash software/acmotion/scripts/build_and_test.sh
```

Then run:

```bash
bash software/acmotion/scripts/preflight_linux.sh
```

When ESP32 is connected:

```bash
bash software/acmotion/scripts/preflight_linux.sh /dev/ttyUSB0
```

The actual device may be `/dev/ttyACM0`, `/dev/ttyUSB0`, or another stable udev path.

---

# 8. Verify serial communication with motor power OFF

Run:

```bash
python3 software/acmotion/scripts/serial_monitor.py \
  --device /dev/ttyUSB0 \
  --baud 115200
```

This monitor is read-only.

Confirm:

1. ESP32 boots consistently.
2. Messages are readable.
3. No random resets occur.
4. Endstop changes appear correctly.
5. E-stop state appears correctly.

Do not enable motor power if serial resets when the servo or drivers are connected.

---

# 9. Test the gripper separately

With all steppers disabled:

1. command a conservative open position;
2. command a conservative close position;
3. check current draw;
4. make sure the servo does not remain mechanically stalled;
5. establish safe open/closed percentages.

Record:

- fully open percentage;
- practical piece-grasp percentage;
- mechanical closed limit.

The chess piece should be gripped without continuously forcing the servo against a hard stop.

---

# 10. Test Z axis only

Keep rotary joints disabled.

1. position Z away from both mechanical ends;
2. enable only Z driver;
3. command a very small step count;
4. verify positive direction;
5. reverse;
6. test the Z endstop manually;
7. verify controller stops immediately when expected.

Do not attempt homing at high speed.

Establish:

- Z positive direction;
- home/reference direction;
- steps/mm;
- minimum Z;
- maximum Z.

---

# 11. Test Joint 1 only

Disable J2/J3/Z drivers if practical.

1. move J1 by a very small amount;
2. verify positive direction;
3. reverse;
4. verify belt/pulley motion;
5. test its reference/endstop;
6. measure whether commanded motion approximately matches physical rotation.

Record:

- motor full steps/revolution;
- microstepping;
- belt reduction;
- resulting steps/radian;
- zero offset;
- mechanical limits.

---

# 12. Repeat for Joint 2 and Joint 3

Perform the same procedure independently for J2 and J3.

Do not infer their directions from J1.

The reference robot uses different mechanical reductions between joints, so each axis must have its own conversion/configuration.

---

# 13. Establish homing

Only after every axis works independently:

1. home Z at low speed;
2. home J1;
3. home J2;
4. home J3;
5. back off switches after trigger;
6. establish deterministic zero offsets.

The final order may change after physical testing if one axis can collide during homing.

Document the final homing order in an ADR or firmware runbook.

---

# 14. Measure the real SCARA geometry

Do not use unit-test fixture values such as 100 mm + 100 mm.

Measure from the actual robot/CAD:

- J1 axis center → J2 axis center = L1;
- J2 axis center → relevant distal/tool axis = L2;
- J3/tool geometry;
- tool-center-point offset;
- board plane Z;
- safe Z;
- pick Z.

Also record the angular zero convention of each joint.

---

# 15. Coordinate-frame definition

Define one SCARA base frame.

Recommended documentation must state:

```
origin:
+X:
+Y:
+Z:
positive J1:
positive J2:
positive J3:
tool zero orientation:
```

Do not calibrate the board until these conventions are frozen.

---

# 16. Current software IK check

The existing solver can be used to validate J1/J2 position calculations offline.

It must not yet be considered the complete physical solver for this arm because J3 orientation is missing.

Track completion in #160.

Once #160 is implemented, the expected conceptual relationship for a fixed tool orientation is:

```
J1 + J2 + J3 = desired tool yaw
```

with the exact sign/offset convention determined by the physical joint-zero definitions.

---

# 17. Board calibration

After the arm frame is validated:

1. physically secure the chessboard;
2. define the center of A1;
3. define the center of H1;
4. verify rank direction;
5. configure CoordinateMapper;
6. validate A1/H1/A8/H8/E4.

Do not pick a piece yet.

Move/measure above each target with the tool high above the board.

---

# 18. Safe-height validation

Before picking:

1. command a central square at safe Z;
2. verify XY;
3. lower gradually without a piece;
4. establish pick Z;
5. add clearance margin;
6. verify tallest chess piece does not collide during horizontal travel.

The current MotionPlanner uses separate safe and pick heights.

Use measured values, not defaults, for the physical robot.

---

# 19. First physical pick-and-place

Only after #160 is resolved and the full four-stepper joint contract is validated:

1. use one test piece;
2. use two central board squares;
3. disable autonomous Vision/Stockfish/FSM;
4. create one controlled transfer;
5. inspect all Cartesian poses;
6. inspect all J1/J2/J3/Z targets;
7. execute at low speed;
8. keep E-stop accessible;
9. verify every ACK/DONE;
10. measure final error.

Repeat until reliable before enabling captures.

---

# 20. Integration progression

Use this order:

```
single axis
→ homing
→ joint-space move
→ IK target
→ empty-board Cartesian move
→ single-piece pick/place
→ repeated pick/place
→ capture
→ graveyard
→ castling
→ en passant
→ Vision verification
→ Game Coordinator
→ autonomous game
```

Do not jump directly from unit tests to an autonomous chess game.

---

# 21. What to record for every failure

Capture:

- host Git SHA;
- firmware Git SHA;
- measured L1/L2/tool offsets;
- steps/radian or steps/mm;
- microstepping;
- reduction ratios;
- current-limit settings;
- requested Cartesian pose;
- calculated J1/J2/J3/Z;
- ACM command;
- ESP32 response;
- actual physical result;
- endstop/E-stop state.

This information makes a motion bug reproducible instead of hardware-specific guesswork.
