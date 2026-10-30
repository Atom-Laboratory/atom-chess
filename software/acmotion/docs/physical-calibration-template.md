# ATOM Chess SCARA Physical Calibration Template

Copy this file into the hardware/integration records for each physical robot revision. Do not commit secrets or host-specific credentials.

## Record metadata

- Date:
- Operator:
- Robot revision:
- Mechanical/CAD revision:
- SBC model:
- SBC OS/version:
- ESP32-S3 board:
- ESP32 firmware commit:
- Host software commit:
- Power-supply configuration:
- Stepper driver/current configuration:

## 1. Coordinate-frame convention

Document with a sketch/photo reference if possible.

- Base origin description:
- +X direction:
- +Y direction:
- +Z direction:
- Joint 1 positive rotation:
- Joint 2 positive rotation:
- Joint 3 positive rotation:
- Tool yaw zero orientation:
- Z zero/reference:
- Tool-center-point definition:
- Board plane Z:
- Units: millimetres / radians

## 2. SCARA geometry

Values used by `ScaraGeometry`.

| Parameter | Value | Unit | Measurement source |
| --- | ---: | --- | --- |
| L1 | TBD | mm | CAD / measured |
| L2 | TBD | mm | CAD / measured |
| Joint 1 minimum | TBD | rad | mechanical |
| Joint 1 maximum | TBD | rad | mechanical |
| Joint 2 minimum | TBD | rad | mechanical |
| Joint 2 maximum | TBD | rad | mechanical |
| Joint 3 minimum | TBD | rad | mechanical |
| Joint 3 maximum | TBD | rad | mechanical |
| Joint 3 zero offset | TBD | rad | measured/reference |
| Z minimum | TBD | mm | mechanical |
| Z maximum | TBD | mm | mechanical |
| Preferred elbow | TBD | Up/Down | integration decision |

Never replace TBD with values copied from unit-test fixtures.

## 3. Joint zero calibration

### Joint 1

- Physical reference:
- Endstop/reference sensor:
- Motor direction:
- Steps/revolution:
- Microstepping:
- Transmission ratio:
- Zero offset:

### Joint 2

- Physical reference:
- Endstop/reference sensor:
- Motor direction:
- Steps/revolution:
- Microstepping:
- Transmission ratio:
- Zero offset:

### Joint 3

- Physical reference:
- Endstop/reference sensor:
- Motor direction:
- Steps/revolution:
- Microstepping:
- Transmission ratio:
- Zero offset:
- Tool yaw when J1=J2=J3=0:

### Z axis

- Physical reference:
- Lead-screw pitch:
- Steps/revolution:
- Microstepping:
- Travel per revolution:
- Zero offset:
- Positive motor direction:

## 4. Board calibration

CoordinateMapper inputs:

| Point | X (mm) | Y (mm) |
| --- | ---: | ---: |
| A1 center | TBD | TBD |
| H1 center | TBD | TBD |

- Rank direction: TBD
- Measured square spacing: TBD mm
- Board fixed/secured: yes / no

Validation points:

| Square | Expected X | Expected Y | Measured error |
| --- | ---: | ---: | ---: |
| A1 | | | |
| H1 | | | |
| A8 | | | |
| H8 | | | |
| E4 | | | |

## 5. Graveyard calibration

### White-piece graveyard

- origin:
- column step:
- row step:
- rows: 2
- columns: 8

### Black-piece graveyard

- origin:
- column step:
- row step:
- rows: 2
- columns: 8

Verify all 16 slots are physically reachable before capture tests.

## 6. Gripper calibration

- Fully open command percentage:
- Fully closed command percentage:
- Safe piece-grasp percentage:
- Maximum safe force/current configuration:
- Piece-set used during calibration:
- Tallest piece:
- Widest piece:

## 7. Motion safety parameters

- Initial bench-test maximum joint velocity:
- Initial bench-test maximum joint acceleration:
- Initial Z velocity:
- Safe Cartesian Z height:
- Pick/place Z height:
- Emergency-stop tested: yes / no
- All limit switches tested: yes / no

These values belong in runtime/hardware configuration, not undocumented source constants.

## 8. Serial/protocol configuration

- Device path used during integration:
- Baud:
- Data bits:
- Stop bits:
- Parity:
- Firmware protocol version: ACM1
- ACK timeout:
- DONE timeout:

Device paths such as `/dev/ttyUSB0` may change across boots. Prefer stable udev aliases for production deployment.

## 9. Acceptance measurements

### Single-axis

- Joint 1 + / -:
- Joint 2 + / -:
- Joint 3 + / -:
- Z + / -:
- Gripper:

### Combined motion

- Known Cartesian target 1:
- Known Cartesian target 2:
- Repeatability result:

### Board manipulation

- Empty-board square approach:
- Single-piece pick:
- Single-piece place:
- Capture:
- Graveyard:
- En passant:
- Castling:

## 10. Known deviations / follow-up issues

List mechanical offsets, backlash, calibration residuals and any software workaround that still exists.

Every workaround that changes an architectural boundary should be promoted to an ADR or tracked issue.
