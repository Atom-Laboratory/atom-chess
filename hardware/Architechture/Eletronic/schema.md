# ATOM Chess — Industrial Electrical Schematic Package

**Document ID:** ATOM-CHESS-EL-001  
**Revision:** A — Engineering draft  
**Date:** 2026-07-31  
**System:** Autonomous robotic chess system  
**Drawing convention:** IEC-style, multi-line, functional-location-separated  
**Intended ECAD implementation:** EPLAN Electric P8, AutoCAD Electrical, or equivalent

> **Deliverable scope:** This document is the electrical design source package: page plan, circuit connectivity, device references, terminal assignments, net names, I/O list, cable schedule, protection schedule, and engineering notes. Zoo Design Studio/KCL is a mechanical CAD environment and does not generate native EPLAN/AutoCAD Electrical drawings or licensed IEC symbol graphics. Transfer the defined circuits into an ECAD package using its IEC 60617 symbol library.

> **Engineering status:** Not released for construction. Mains protection, conductor sizing, short-circuit rating, thermal design, motor current limits, emergency-stop performance level, and exact board GPIO pins require verification by a qualified electrical engineer against the selected hardware and installation jurisdiction.

---

## 0. Standards and drafting basis

Use the following basis when producing the graphical drawing set:

- IEC 60617 database — graphical symbols for electrotechnical diagrams.
- IEC 61082-1 — preparation and presentation of electrotechnical documents.
- IEC 81346-1 and IEC 81346-2 — structuring and reference designations.
- IEC 60204-1 — electrical equipment of machines.
- ISO 13850 — emergency-stop design principles.
- ISO 13849-1 — design methodology for safety-related control systems.

### Drafting rules

1. Draw power flow left-to-right and top-to-bottom.
2. Separate **POWER**, **CONTROL SIGNALS**, **COMMUNICATION**, and **SENSORS** by pages and functional frames.
3. Show every external conductor at a numbered terminal or connector pin.
4. Use net labels instead of long cross-page conductors. Include source/destination cross-references in ECAD.
5. Use protective earth symbol only for PE. Use `GND_COMMON` or `0V` for DC return.
6. Use dashed connection lines for Wi-Fi and other non-wired communication.
7. Mark active-low nets with `_N`.
8. Mark provisional ratings and unresolved hardware selections with `TBD` revision flags.

---

## 1. Drawing index

| Page | Drawing title | Functional area |
|---:|---|---|
| 00 | Cover, index, standards, general notes | Documentation |
| 01 | AC mains input and 12 VDC power supply | POWER |
| 02 | 12 VDC distribution, motor safety isolation, DC/DC converters | POWER |
| 03 | Embedded computers and communication interfaces | COMMUNICATION / CONTROL |
| 04 | DRV-01 and M1 Joint 1 | MOTOR CONTROL |
| 05 | DRV-02 and M2 Joint 2 | MOTOR CONTROL |
| 06 | DRV-03 and M3 Joint 3 | MOTOR CONTROL |
| 07 | DRV-04 and M4 Joint 4 | MOTOR CONTROL |
| 08 | DRV-05 and M5 Joint 5 | MOTOR CONTROL |
| 09 | Servo, endstops, emergency stop, safety relay | SENSORS / SAFETY |
| 10 | ESP32-S3 I/O schedule and control connector | CONTROL SIGNALS |
| 11 | Terminal plan and cable schedule | INSTALLATION |
| 12 | Bill of materials, power budget, design notes | DOCUMENTATION |

---

# PAGE 01 — AC POWER INPUT AND PSU

## 1.1 Single-phase AC circuit

```text
POWER — AC MAINS 127/220 VAC, 1 PHASE

 XAC-01                       QSW-01             FU-01                 PSU-01
 AC INPUT CONNECTOR       2-POLE MAIN SWITCH   LINE FUSE        127/220VAC → 12VDC, 10A

  XAC-01:1  L  ─────────── 1       2 ───────── [T2A, 250V]* ──────── L
  XAC-01:2  N  ─────────── 3       4 ─────────────────────────────── N
  XAC-01:PE PE ─────────── XPE-01:1 ─────────── XPE-01:2 ─────────── PE/FG
                           │
                           └──────── Protective bonding to metal enclosure/chassis

 PSU-01:+V ───── FU-02 [10A DC]* ───── +12V_DC_BUS
 PSU-01:-V ───── X0V-01:1 ───────────── GND_COMMON
```

`*` Fuse type and rating are provisional and must be coordinated with PSU-01 inrush current, branch-circuit protection, wire ampacity, and local code.

## 1.2 AC terminal and device assignments

| Reference | Terminal | Connection / marking |
|---|---:|---|
| XAC-01 | 1 | `L_IN` — line conductor |
| XAC-01 | 2 | `N_IN` — neutral conductor |
| XAC-01 | PE | `PE` — protective earth, first-make/last-break where applicable |
| QSW-01 | 1-2 | Switched line pole |
| QSW-01 | 3-4 | Switched neutral pole |
| FU-01 | 1-2 | Line fuse, touch-safe holder |
| PSU-01 | L | AC line input |
| PSU-01 | N | AC neutral input |
| PSU-01 | PE | Protective earth/frame ground |
| PSU-01 | +V | +12 VDC, 10 A rated output |
| PSU-01 | -V | DC return |
| FU-02 | 1-2 | Main DC distribution protection |
| XPE-01 | 1…n | PE terminal bar |
| X0V-01 | 1…n | Common DC return terminal bar |

### AC installation note

The requested notation `L / N / PE` applies to a single-phase supply with a defined neutral. If the unit is connected to North American 208/240 V line-to-line service, use `L1 / L2 / PE`, provide two-pole overcurrent/disconnect protection appropriate to the installation, and do not identify either live leg as neutral.

---

# PAGE 02 — DC POWER DISTRIBUTION

## 2.1 Bus architecture

```text
                                  ┌─ FU-201 ─ DRV-01 VMOT
                                  ├─ FU-202 ─ DRV-02 VMOT
 +12V_DC_BUS ─ K1-01 main contact ├─ FU-203 ─ DRV-03 VMOT
                1          2      ├─ FU-204 ─ DRV-04 VMOT
                                  └─ FU-205 ─ DRV-05 VMOT
                                         NET: +12V_MOTOR

 +12V_DC_BUS ─ FU-211 ─ +12V_LOGIC ─ BUCK-01 ─ LOGIC_5V
                         │
                         └─ FU-212 ─ BUCK-02 ─ CONTROL_5V

 PSU-01:-V ─────────────────────────────────── GND_COMMON
```

### Bus definitions

| Net | Voltage | Function |
|---|---:|---|
| `+12V_DC_BUS` | +12 VDC nominal | Main PSU output before functional branches |
| `+12V_MOTOR` | +12 VDC nominal, safety-switched | VMOT supply to DRV-01…DRV-05 |
| `+12V_LOGIC` | +12 VDC nominal | Input supply to BUCK-01 and BUCK-02 |
| `LOGIC_5V` | +5 VDC regulated | Orange Pi and Banana Pi M5 |
| `CONTROL_5V` | +5 VDC regulated | ESP32-S3, ESP32-CAM, servo, endstop sensors |
| `+3V3_CTRL` | +3.3 VDC local | ESP32-S3 board regulated logic; pull-ups only unless board rating permits more |
| `GND_COMMON` | 0 VDC | Common return for all 12 V, 5 V, logic, sensor, and communication circuits |
| `PE` | Protective earth | Personnel protection and chassis bonding; not interchangeable with `GND_COMMON` |

## 2.2 DC protective devices and converters

| Reference | Input | Output | Provisional minimum rating | Loads |
|---|---|---|---|---|
| FU-201…FU-205 | `+12V_MOTOR` | Driver branch | 2 A DC each, slow/time-delay; verify per motor | One DRV8825 each |
| FU-211 | `+12V_DC_BUS` | `+12V_LOGIC` to BUCK-01 | 5 A DC; verify | Logic converter input |
| FU-212 | `+12V_LOGIC` | BUCK-02 input | 4 A DC; verify | Control converter input |
| BUCK-01 | 12 VDC | 5 VDC | 8 A continuous minimum, protected and thermally rated | Orange Pi, Banana Pi M5 |
| BUCK-02 | 12 VDC | 5 VDC | 5 A continuous minimum; servo surge capability required | ESP32-S3, ESP32-CAM, servo, sensors |

## 2.3 Grounding and bonding

- All DC returns connect to `GND_COMMON` at X0V-01.
- Do not route motor current through logic-device ground pins; use star or low-impedance distribution back to X0V-01.
- Keep `PE` and `GND_COMMON` distinct in the drawing.
- If an intentional 0 V-to-PE bond is required for EMC or the selected PSU architecture, install a documented single-point bond `NT-01`; do not create multiple uncontrolled bonds.
- Bond all exposed conductive enclosure parts to XPE-01 using green/yellow protective conductors.

---

# PAGE 03 — COMPUTING AND COMMUNICATION

## 3.1 Computing devices

| Reference | Device | Function | Power |
|---|---|---|---|
| CPU-01 | Orange Pi, exact model TBD | Computer Vision | `LOGIC_5V`, `GND_COMMON` |
| CPU-02 | Banana Pi M5 | Chess Brain | `LOGIC_5V`, `GND_COMMON` |
| CTRL-01 | ESP32-S3 module/dev board, exact model TBD | Motion Controller | `CONTROL_5V`, `GND_COMMON` |
| CAM-01 | ESP32-CAM module | Camera | `CONTROL_5V`, `GND_COMMON` |

## 3.2 Power connectors

| Connector | Pin | Net | Destination |
|---|---:|---|---|
| X31-01 | 1 | `LOGIC_5V` | CPU-01 Orange Pi +5 V input |
| X31-01 | 2 | `GND_COMMON` | CPU-01 return |
| X31-02 | 1 | `LOGIC_5V` | CPU-02 Banana Pi M5 +5 V input |
| X31-02 | 2 | `GND_COMMON` | CPU-02 return |
| X31-03 | 1 | `CONTROL_5V` | CTRL-01 ESP32-S3 5 V/VIN input |
| X31-03 | 2 | `GND_COMMON` | CTRL-01 return |
| X31-04 | 1 | `CONTROL_5V` | CAM-01 ESP32-CAM 5 V input |
| X31-04 | 2 | `GND_COMMON` | CAM-01 return |

## 3.3 Communication topology

```text
 CAM-01 ESP32-CAM ))) - - - - - Wi-Fi - - - - - ((( CPU-01 Orange Pi

 CPU-01 Orange Pi [RJ45] ═══════ CAT5e/CAT6 ═══════ [RJ45] CPU-02 Banana Pi M5
                    Cable/net identifier: ETH_CV_BRAIN

 CPU-02 Banana Pi M5                       CTRL-01 ESP32-S3
 UART_TX_BPI ─────────────────────────────> UART_RX_ESP
 UART_RX_BPI <───────────────────────────── UART_TX_ESP
 GND_COMMON  ────────────────────────────── GND_COMMON
              Interface identifier: UART_MICROROS_01
```

### Communication connector X32-01 — UART / micro-ROS

| Pin | Net | Source | Destination |
|---:|---|---|---|
| 1 | `UART_TX_BPI` | CPU-02 UART TX | CTRL-01 UART RX |
| 2 | `UART_RX_BPI` | CPU-02 UART RX | CTRL-01 UART TX |
| 3 | `GND_COMMON` | Common return | Common return |
| 4 | Shield/drain, optional | Chassis termination as EMC design requires | Chassis termination |

### Communication notes

- Verify the selected Banana Pi UART and ESP32-S3 GPIO voltage levels before connection. The intended interface is 3.3 V logic.
- Do not connect `LOGIC_5V` or `CONTROL_5V` through X32-01 unless a specific powered interface is designed.
- Use a short, twisted signal/return arrangement or a differential transceiver if UART routing is long or exposed to motor noise.
- Show Wi-Fi as a dashed functional connection, not a physical wire.

---

# PAGES 04–08 — STEPPER MOTOR DRIVER CIRCUITS

## 4.1 Common driver architecture

Each driver circuit shall be shown independently on its assigned page with identical topology and unique references.

```text
 POWER
 +12V_MOTOR ─ FU-20x ──────┬────────────── DRV-0x:VMOT
                            ├─ C-BULK-0x 100µF / 25V electrolytic
                            │             (+ to VMOT, - to GND_COMMON)
                            └─ C-VM-0x 100nF ceramic, voltage rating ≥ 25V
                                          (local VMOT bypass)

 CONTROL_5V ─────────────────────────────── DRV-0x:VDD* 
                 └─ C-LOGIC-0x 100nF ceramic to GND_COMMON

 GND_COMMON ─────────────────────────────── DRV-0x:GND power and logic returns

 CONTROL SIGNALS FROM CTRL-01
 STEP_Jx ────────────────────────────────── DRV-0x:STEP
 DIR_Jx ─────────────────────────────────── DRV-0x:DIR
 DRV_ENABLE_N ───────────────────────────── DRV-0x:ENABLE / nENABLE
 DRV_WAKE ───────────────────────────────── DRV-0x:nSLEEP / nRESET as module permits

 MOTOR OUTPUT
 DRV-0x:A1 ─ X4x-0x:1 ──────────────────── MOTOR_0x_A+
 DRV-0x:A2 ─ X4x-0x:2 ──────────────────── MOTOR_0x_A-
 DRV-0x:B1 ─ X4x-0x:3 ──────────────────── MOTOR_0x_B+
 DRV-0x:B2 ─ X4x-0x:4 ──────────────────── MOTOR_0x_B-
```

`*` **DRV8825 module variant note:** The bare TI DRV8825 and common carrier-module pinouts do not necessarily expose or require a separate `VDD` pin. The final ECAD symbol and `C-LOGIC-0x` connection must match the exact purchased module. If the selected module has no VDD terminal, omit the VDD pin and retain the manufacturer-required local supply bypass components. Do not force 5 V onto a non-VDD pin.

## 4.2 Driver instance schedule

| Page | Driver | Motor | Function | Step net | Direction net | Motor connector |
|---:|---|---|---|---|---|---|
| 04 | DRV-01 | M1 | Joint 1 | `STEP_J1` | `DIR_J1` | X41-01 |
| 05 | DRV-02 | M2 | Joint 2 | `STEP_J2` | `DIR_J2` | X42-01 |
| 06 | DRV-03 | M3 | Joint 3 | `STEP_J3` | `DIR_J3` | X43-01 |
| 07 | DRV-04 | M4 | Joint 4 | `STEP_J4` | `DIR_J4` | X44-01 |
| 08 | DRV-05 | M5 | Joint 5 | `STEP_J5` | `DIR_J5` | X45-01 |

## 4.3 Driver component schedule

| Driver | Branch fuse | Bulk capacitor | VMOT ceramic | Logic decoupling | Stepper motor |
|---|---|---|---|---|---|
| DRV-01 | FU-201 | C401 100 µF/25 V | C402 100 nF/≥25 V | C403 100 nF | M1 Joint 1 |
| DRV-02 | FU-202 | C501 100 µF/25 V | C502 100 nF/≥25 V | C503 100 nF | M2 Joint 2 |
| DRV-03 | FU-203 | C601 100 µF/25 V | C602 100 nF/≥25 V | C603 100 nF | M3 Joint 3 |
| DRV-04 | FU-204 | C701 100 µF/25 V | C702 100 nF/≥25 V | C703 100 nF | M4 Joint 4 |
| DRV-05 | FU-205 | C801 100 µF/25 V | C802 100 nF/≥25 V | C803 100 nF | M5 Joint 5 |

## 4.4 Motor connector and cable labels

### X41-01 — M1 Joint 1

| Pin | Driver terminal | Wire label | Cable core |
|---:|---|---|---|
| 1 | DRV-01 A1 | `MOTOR_01_A+` | W-M01.1 |
| 2 | DRV-01 A2 | `MOTOR_01_A-` | W-M01.2 |
| 3 | DRV-01 B1 | `MOTOR_01_B+` | W-M01.3 |
| 4 | DRV-01 B2 | `MOTOR_01_B-` | W-M01.4 |
| SH | Cable shield | `SHIELD_M01` | Overall shield |

### X42-01 — M2 Joint 2

| Pin | Driver terminal | Wire label | Cable core |
|---:|---|---|---|
| 1 | DRV-02 A1 | `MOTOR_02_A+` | W-M02.1 |
| 2 | DRV-02 A2 | `MOTOR_02_A-` | W-M02.2 |
| 3 | DRV-02 B1 | `MOTOR_02_B+` | W-M02.3 |
| 4 | DRV-02 B2 | `MOTOR_02_B-` | W-M02.4 |
| SH | Cable shield | `SHIELD_M02` | Overall shield |

### X43-01 — M3 Joint 3

| Pin | Driver terminal | Wire label | Cable core |
|---:|---|---|---|
| 1 | DRV-03 A1 | `MOTOR_03_A+` | W-M03.1 |
| 2 | DRV-03 A2 | `MOTOR_03_A-` | W-M03.2 |
| 3 | DRV-03 B1 | `MOTOR_03_B+` | W-M03.3 |
| 4 | DRV-03 B2 | `MOTOR_03_B-` | W-M03.4 |
| SH | Cable shield | `SHIELD_M03` | Overall shield |

### X44-01 — M4 Joint 4

| Pin | Driver terminal | Wire label | Cable core |
|---:|---|---|---|
| 1 | DRV-04 A1 | `MOTOR_04_A+` | W-M04.1 |
| 2 | DRV-04 A2 | `MOTOR_04_A-` | W-M04.2 |
| 3 | DRV-04 B1 | `MOTOR_04_B+` | W-M04.3 |
| 4 | DRV-04 B2 | `MOTOR_04_B-` | W-M04.4 |
| SH | Cable shield | `SHIELD_M04` | Overall shield |

### X45-01 — M5 Joint 5

| Pin | Driver terminal | Wire label | Cable core |
|---:|---|---|---|
| 1 | DRV-05 A1 | `MOTOR_05_A+` | W-M05.1 |
| 2 | DRV-05 A2 | `MOTOR_05_A-` | W-M05.2 |
| 3 | DRV-05 B1 | `MOTOR_05_B+` | W-M05.3 |
| 4 | DRV-05 B2 | `MOTOR_05_B-` | W-M05.4 |
| SH | Cable shield | `SHIELD_M05` | Overall shield |

## 4.5 Driver engineering notes

1. Place each 100 µF bulk capacitor and ceramic bypass capacitor physically close to the corresponding VMOT/GND terminals.
2. Set the current limit for the selected motor phase current and the actual module sense-resistor value before motor connection.
3. Confirm MODE0/MODE1/MODE2 strap states and document the selected microstep setting in the released schematic.
4. Keep STEP/DIR wiring separated from stepper phase conductors.
5. Use keyed, touch-safe motor connectors where practical. Never connect or disconnect a stepper motor while its driver is energized.
6. `DRV_ENABLE_N` is the common normal-operation enable signal. The emergency-stop safety function does not rely solely on this software-controlled signal; it removes `+12V_MOTOR` through K1-01.

---

# PAGE 09 — SERVO, ENDSTOPS, AND EMERGENCY STOP

## 9.1 Servo system

```text
 CONTROL_5V ─ FU-901 [3A provisional] ─ X91-01:1 ─ SERVO-01:+5V
 GND_COMMON ────────────────────────── X91-01:2 ─ SERVO-01:GND
 CTRL-01 SERVO_PWM ─────────────────── X91-01:3 ─ SERVO-01:PWM

 C901 470µF / ≥10V between X91-01:1 and X91-01:2, close to connector
 C902 100nF ceramic between X91-01:1 and X91-01:2
```

| Connector | Pin | Net / wire label | Function |
|---|---:|---|---|
| X91-01 | 1 | `CONTROL_5V_SERVO` | Fused servo power |
| X91-01 | 2 | `GND_COMMON` | Servo return |
| X91-01 | 3 | `SERVO_PWM` | PWM from CTRL-01 |

The servo branch must be sized for stall current. If servo transients disturb control electronics, use a dedicated 5 V converter or additional branch filtering rather than increasing capacitance without analysis.

## 9.2 Endstop sensors

Assume five 3-wire endstop sensors, one per joint. Sensors are powered by `CONTROL_5V`. To protect ESP32-S3 inputs, use sensors with NPN open-collector/open-drain outputs and pull the signal up to `+3V3_CTRL` at CTRL-01.

```text
 CONTROL_5V ───────── X92-0x:1 ─ ENDSTOP-0x:+V
 GND_COMMON ───────── X92-0x:2 ─ ENDSTOP-0x:0V
 ENDSTOP_RAW_Jx ───── X92-0x:3 ─ ENDSTOP-0x:OUT (open collector)

 +3V3_CTRL ─ R92x [10k] ─┐
                          ├─ R93x [1k series] ─ CTRL-01 GPIO: ENDSTOP_Jx
 ENDSTOP_RAW_Jx ──────────┘
                          └─ C92x [100nF] to GND_COMMON at controller input
```

| Sensor | Connector | Pin 1 | Pin 2 | Pin 3 / signal |
|---|---|---|---|---|
| ENDSTOP-01 Joint 1 | X92-01 | `CONTROL_5V` | `GND_COMMON` | `ENDSTOP_RAW_J1` |
| ENDSTOP-02 Joint 2 | X92-02 | `CONTROL_5V` | `GND_COMMON` | `ENDSTOP_RAW_J2` |
| ENDSTOP-03 Joint 3 | X92-03 | `CONTROL_5V` | `GND_COMMON` | `ENDSTOP_RAW_J3` |
| ENDSTOP-04 Joint 4 | X92-04 | `CONTROL_5V` | `GND_COMMON` | `ENDSTOP_RAW_J4` |
| ENDSTOP-05 Joint 5 | X92-05 | `CONTROL_5V` | `GND_COMMON` | `ENDSTOP_RAW_J5` |

If a selected sensor produces a 5 V push-pull output, add an approved level shifter or resistor-divider/input protection circuit; do not connect a 5 V push-pull signal directly to an ESP32-S3 GPIO.

## 9.3 Emergency-stop safety circuit

Use a red mushroom-head, latching emergency-stop actuator with two positively driven normally-closed channels. A single NC contact directly connected only to a microcontroller input is not the safety function.

```text
 SAFETY INPUT — DUAL CHANNEL

 SR-01:S11 ─── S0-01:11 ──/ ── S0-01:12 ─── SR-01:S12     Channel A, NC
 SR-01:S21 ─── S0-01:21 ──/ ── S0-01:22 ─── SR-01:S22     Channel B, NC

 S0-02 RESET PB, NO ───────────────────────── SR-01 reset/start input
 K1-01 mirror/feedback NC auxiliary ───────── SR-01 EDM feedback input

 SAFETY OUTPUT

 +12V_DC_BUS ─ SR-01 safety output 13-14 ─ K1-01:A1
 GND_COMMON  ───────────────────────────── K1-01:A2

 K1-01 main DC contact 1-2 is shown on Page 02 and feeds +12V_MOTOR.
 K1-01 auxiliary status contact 13-14 ─ CTRL-01 input MOTION_POWER_OK.
```

### Required behavior

- **Normal state:** S0-01 released, both NC channels closed, manual reset completed, SR-01 healthy, K1-01 energized, `+12V_MOTOR` available.
- **Emergency stop pressed, wire broken, or channel fault:** SR-01 de-energizes K1-01; K1-01 opens the motor-power path to all five DRV8825 VMOT inputs.
- **Reset:** Releasing S0-01 must not automatically restart motion. Operator reset and a separate motion command are required.
- `MOTION_POWER_OK` is diagnostic only and must not be credited as the safety function.
- Select SR-01 and K1-01 ratings and architecture after machinery risk assessment and required performance level determination.

---

# PAGE 10 — ESP32-S3 CONTROL I/O

Because the exact ESP32-S3 board/module is not specified, this schedule assigns functional interface terminals. Map them to verified, available 3.3 V GPIO pins after the exact part number and boot/flash/USB pin restrictions are known.

## 10.1 CTRL-01 motion-control connector X101-01

| Pin | Direction at CTRL-01 | Net | Destination / function |
|---:|---|---|---|
| 1 | Output | `STEP_J1` | DRV-01 STEP |
| 2 | Output | `DIR_J1` | DRV-01 DIR |
| 3 | Output | `STEP_J2` | DRV-02 STEP |
| 4 | Output | `DIR_J2` | DRV-02 DIR |
| 5 | Output | `STEP_J3` | DRV-03 STEP |
| 6 | Output | `DIR_J3` | DRV-03 DIR |
| 7 | Output | `STEP_J4` | DRV-04 STEP |
| 8 | Output | `DIR_J4` | DRV-04 DIR |
| 9 | Output | `STEP_J5` | DRV-05 STEP |
| 10 | Output | `DIR_J5` | DRV-05 DIR |
| 11 | Output | `DRV_ENABLE_N` | Common active-low enable to DRV-01…DRV-05 |
| 12 | Output | `DRV_WAKE` | Driver reset/sleep control if supported |
| 13 | Output | `SERVO_PWM` | SERVO-01 PWM |
| 14 | Input | `ENDSTOP_J1` | Joint 1 endstop, conditioned 3.3 V signal |
| 15 | Input | `ENDSTOP_J2` | Joint 2 endstop, conditioned 3.3 V signal |
| 16 | Input | `ENDSTOP_J3` | Joint 3 endstop, conditioned 3.3 V signal |
| 17 | Input | `ENDSTOP_J4` | Joint 4 endstop, conditioned 3.3 V signal |
| 18 | Input | `ENDSTOP_J5` | Joint 5 endstop, conditioned 3.3 V signal |
| 19 | Input | `MOTION_POWER_OK` | K1-01 auxiliary contact status |
| 20 | — | `GND_COMMON` | Signal reference |

## 10.2 CTRL-01 communication connector X101-02

| Pin | Direction at CTRL-01 | Net | Function |
|---:|---|---|---|
| 1 | Input | `UART_TX_BPI` | ESP32 UART RX from Banana Pi |
| 2 | Output | `UART_RX_BPI` | ESP32 UART TX to Banana Pi |
| 3 | — | `GND_COMMON` | UART reference |
| 4 | — | Shield/drain optional | Chassis termination per EMC design |

## 10.3 Signal defaults

- `DRV_ENABLE_N`: provide a hardware pull-up so the default state is disabled during CTRL-01 reset or disconnection.
- `DRV_WAKE`: default low/inactive until firmware initialization if the selected module permits this behavior.
- `STEP_J1…STEP_J5`: default low with no startup pulses.
- `SERVO_PWM`: default inactive until the servo power branch and command state are validated.
- Endstop inputs: use external pull-ups/filters as shown, not firmware-only pull-ups.

---

# PAGE 11 — TERMINAL AND CABLE PLAN

## 11.1 Primary terminal groups

| Terminal group | Purpose | Terminals |
|---|---|---|
| XAC-01 | Field AC input | 1 L, 2 N, PE |
| XPE-01 | Protective earth bar | PE1…PEn |
| X0V-01 | Common DC return bar | 0V1…0Vn |
| X20-01 | 12 V distribution | 1 `+12V_DC_BUS`, 2 `+12V_MOTOR`, 3 `+12V_LOGIC`, 4 `GND_COMMON` |
| X21-01 | 5 V distribution | 1 `LOGIC_5V`, 2 `CONTROL_5V`, 3 `GND_COMMON` |
| X31-01…04 | Computing power | Two pins each, supply and return |
| X32-01 | UART / micro-ROS | TX, RX, GND, optional shield |
| X41-01…X45-01 | Stepper motors | A+, A-, B+, B-, shield |
| X91-01 | Servo | +5 V, GND, PWM |
| X92-01…X92-05 | Endstops | +5 V, GND, signal |
| X101-01 | ESP32-S3 motion I/O | 20-pin control interface |
| X101-02 | ESP32-S3 UART | 4-pin communication interface |

## 11.2 Cable schedule

| Cable ID | From | To | Construction | Core labels |
|---|---|---|---|---|
| W-AC01 | Facility supply | XAC-01 | 3 conductor, voltage/current/code rated | L, N, PE |
| W-M01 | X41-01 | M1 Joint 1 | 4 conductor shielded motor cable, size per phase current/length | MOTOR_01_A+, MOTOR_01_A-, MOTOR_01_B+, MOTOR_01_B- |
| W-M02 | X42-01 | M2 Joint 2 | 4 conductor shielded motor cable | MOTOR_02_A+, MOTOR_02_A-, MOTOR_02_B+, MOTOR_02_B- |
| W-M03 | X43-01 | M3 Joint 3 | 4 conductor shielded motor cable | MOTOR_03_A+, MOTOR_03_A-, MOTOR_03_B+, MOTOR_03_B- |
| W-M04 | X44-01 | M4 Joint 4 | 4 conductor shielded motor cable | MOTOR_04_A+, MOTOR_04_A-, MOTOR_04_B+, MOTOR_04_B- |
| W-M05 | X45-01 | M5 Joint 5 | 4 conductor shielded motor cable | MOTOR_05_A+, MOTOR_05_A-, MOTOR_05_B+, MOTOR_05_B- |
| W-SV01 | X91-01 | SERVO-01 | 3 conductor, servo-current rated | CONTROL_5V_SERVO, GND_COMMON, SERVO_PWM |
| W-ES01…05 | X92-01…05 | ENDSTOP-01…05 | 3 conductor shielded/twisted control cable where needed | CONTROL_5V, GND_COMMON, ENDSTOP_RAW_Jx |
| W-COM01 | CPU-01 | CPU-02 | CAT5e or CAT6 Ethernet patch cable | ETH_CV_BRAIN |
| W-COM02 | X32-01 | X101-02 | 3 conductor signal cable, TX/GND and RX/GND paired where practical | UART_TX_BPI, UART_RX_BPI, GND_COMMON |
| W-ESTOP01 | S0-01 | SR-01 | Safety-control cable, physically protected | ESTOP_CH_A, ESTOP_CH_B |

## 11.3 Provisional conductor guidance

Final wire sizes must be calculated from current, length, temperature, bundling, voltage drop, fault current, terminal rating, and local code.

| Circuit | Preliminary engineering range |
|---|---|
| AC input | 0.75–1.5 mm² / 18–16 AWG, subject to branch protection and code |
| Main 12 V bus | 1.5–2.5 mm² / 16–14 AWG, subject to load and voltage drop |
| Individual motor supply branch | 0.75–1.5 mm² / 18–16 AWG |
| Stepper phase conductors | 0.5–0.75 mm² / 20–18 AWG typical; calculate for motor current and flex duty |
| 5 V high-current distribution | 0.75–1.5 mm² / 18–16 AWG; voltage-drop calculation is critical |
| Low-current control signals | 0.14–0.34 mm² / 26–22 AWG |
| PE bonding | Per applicable machinery/electrical code; never smaller than permitted for the protected circuit |

## 11.4 Routing / EMC notes

- Route AC mains separately from SELV/PELV and logic wiring.
- Route motor phase wiring separately from endstop, UART, STEP, DIR, and camera wiring.
- Terminate motor cable shields to chassis using a low-impedance clamp strategy selected for the enclosure and EMC plan.
- Avoid pigtail shield terminations for high-frequency noise where a 360° shield clamp is available.
- Use ferrules for stranded conductors in suitable screw-clamp terminals.
- Label both ends of every field conductor and cable.

---

# PAGE 12 — BILL OF MATERIALS AND ENGINEERING CHECKS

## 12.1 Principal bill of materials

| Reference | Qty | Description / minimum requirement |
|---|---:|---|
| XAC-01 | 1 | AC input connector, L/N/PE, rated for maximum mains voltage/current |
| QSW-01 | 1 | Two-pole main disconnect/switch, rated for PSU input and inrush |
| FU-01 | 1 | Touch-safe AC line fuse holder and coordinated time-delay fuse |
| PSU-01 | 1 | Universal-input switching PSU, 127/220 VAC input, 12 VDC 10 A output, protected, PE terminal |
| FU-02 | 1 | Main DC fuse/protection device |
| XPE-01 | 1 | Protective-earth terminal bar |
| X0V-01 | 1 | Common DC return terminal bar |
| K1-01 | 1 | 12 VDC motor-power contactor/relay with DC-rated main contact and monitored auxiliary contact |
| SR-01 | 1 | Certified safety relay/controller suitable for selected architecture and supply |
| S0-01 | 1 | Latching red mushroom emergency-stop actuator, two positive-opening NC contacts |
| S0-02 | 1 | Manual safety-reset pushbutton, NO |
| BUCK-01 | 1 | 12 V to regulated 5 V converter, logic-computer capacity, minimum 8 A provisional |
| BUCK-02 | 1 | 12 V to regulated 5 V converter, control/servo capacity, minimum 5 A provisional |
| CPU-01 | 1 | Orange Pi, exact model TBD |
| CPU-02 | 1 | Banana Pi M5 |
| CTRL-01 | 1 | ESP32-S3 module/dev board, exact model TBD |
| CAM-01 | 1 | ESP32-CAM module |
| DRV-01…DRV-05 | 5 | DRV8825 stepper driver modules, exact manufacturer/variant TBD |
| C401/C501/C601/C701/C801 | 5 | 100 µF, 25 V electrolytic, low-ESR as appropriate |
| C402/C502/C602/C702/C802 | 5 | 100 nF ceramic, VMOT bypass, voltage rating ≥25 V |
| C403/C503/C603/C703/C803 | 5 | 100 nF ceramic, logic decoupling when required by module |
| M1…M5 | 5 | Bipolar stepper motors: Joint 1…Joint 5, ratings TBD |
| SERVO-01 | 1 | 5 V servo, stall current and PWM requirements TBD |
| ENDSTOP-01…ENDSTOP-05 | 5 | 5 V endstop sensor, NPN open-collector/open-drain output preferred |
| FU-201…FU-205 | 5 | Individual driver branch protection, rating TBD after motor selection |
| FU-211/FU-212/FU-901 | 3 | Converter/servo branch protection, coordinated ratings |
| X41-01…X45-01 | 5 | Keyed 4-pole stepper motor connectors plus shield termination |
| X92-01…X92-05 | 5 | 3-pole endstop connectors |
| X91-01 | 1 | 3-pole servo connector |

## 12.2 Power budget worksheet

PSU-01 is specified as 12 V × 10 A = **120 W maximum nameplate output**. Use a continuous design target below the nameplate rating and verify transient response.

| Load | Quantity | Required data | 12 V input contribution |
|---|---:|---|---|
| DRV8825 + stepper motor | 5 | Motor phase current, resistance, duty cycle, acceleration profile, driver efficiency | TBD |
| Orange Pi | 1 | Exact model and peak 5 V current | TBD through BUCK-01 |
| Banana Pi M5 | 1 | Peak 5 V current and peripheral load | TBD through BUCK-01 |
| ESP32-S3 | 1 | Board and peripheral peak current | TBD through BUCK-02 |
| ESP32-CAM | 1 | Wi-Fi/camera peak current | TBD through BUCK-02 |
| Servo | 1 | Running and stall current | TBD through BUCK-02 |
| Endstop sensors | 5 | Per-sensor current | TBD through BUCK-02 |

Use:

```text
I_PSU ≈ Σ I_MOTOR_BRANCH + (P_LOGIC_5V / (12V × η_BUCK01))
                         + (P_CONTROL_5V / (12V × η_BUCK02))
```

Do not release PSU-01 as adequate until the calculated continuous load, motor acceleration demand, regenerative energy behavior, and servo stall transient are tested with margin. Five stepper axes plus two single-board computers may exceed a 12 V / 10 A supply depending on the selected motors and duty cycle.

## 12.3 Required release checks

- [ ] Exact Orange Pi model and supply connector defined.
- [ ] Exact ESP32-S3 board/module and allowable GPIO mapping defined.
- [ ] Exact DRV8825 module pinout verified; VDD note resolved.
- [ ] Motor phase current, winding pairing, connector pinout, and current-limit settings documented.
- [ ] Microstep strap settings documented.
- [ ] Buck converter thermal and transient ratings verified.
- [ ] Servo stall-current test completed.
- [ ] Endstop output topology verified as 3.3 V-safe.
- [ ] AC fuse, switch, inlet, wire, and PSU inrush coordination completed.
- [ ] DC fuse ratings and conductor ampacities calculated.
- [ ] Short-circuit current rating and enclosure protective bonding reviewed.
- [ ] Emergency-stop risk assessment and required PLr established.
- [ ] SR-01/K1-01 architecture validated to the required safety performance.
- [ ] Manual reset and prevention of unexpected restart tested.
- [ ] EMC cable separation and shield termination plan reviewed.
- [ ] Final ECAD pages use IEC symbols, cross-references, terminal strips, wire numbers, and title blocks.

---

# Net-name master list

## Power nets

- `L_IN`
- `N_IN`
- `PE`
- `+12V_DC_BUS`
- `+12V_MOTOR`
- `+12V_LOGIC`
- `LOGIC_5V`
- `CONTROL_5V`
- `CONTROL_5V_SERVO`
- `+3V3_CTRL`
- `GND_COMMON`

## Motion-control nets

- `STEP_J1`, `DIR_J1`
- `STEP_J2`, `DIR_J2`
- `STEP_J3`, `DIR_J3`
- `STEP_J4`, `DIR_J4`
- `STEP_J5`, `DIR_J5`
- `DRV_ENABLE_N`
- `DRV_WAKE`

## Motor cable nets

- `MOTOR_01_A+`, `MOTOR_01_A-`, `MOTOR_01_B+`, `MOTOR_01_B-`
- `MOTOR_02_A+`, `MOTOR_02_A-`, `MOTOR_02_B+`, `MOTOR_02_B-`
- `MOTOR_03_A+`, `MOTOR_03_A-`, `MOTOR_03_B+`, `MOTOR_03_B-`
- `MOTOR_04_A+`, `MOTOR_04_A-`, `MOTOR_04_B+`, `MOTOR_04_B-`
- `MOTOR_05_A+`, `MOTOR_05_A-`, `MOTOR_05_B+`, `MOTOR_05_B-`

## Sensor and servo nets

- `ENDSTOP_RAW_J1`, `ENDSTOP_J1`
- `ENDSTOP_RAW_J2`, `ENDSTOP_J2`
- `ENDSTOP_RAW_J3`, `ENDSTOP_J3`
- `ENDSTOP_RAW_J4`, `ENDSTOP_J4`
- `ENDSTOP_RAW_J5`, `ENDSTOP_J5`
- `SERVO_PWM`
- `MOTION_POWER_OK`
- `ESTOP_CH_A`
- `ESTOP_CH_B`

## Communication nets

- `ETH_CV_BRAIN`
- `UART_TX_BPI`
- `UART_RX_BPI`
- `UART_MICROROS_01`
- `WIFI_CAM_CV`

---

# ECAD title-block fields

| Field | Value |
|---|---|
| Project | ATOM Chess |
| Description | Autonomous robotic chess system — electrical schematics |
| Document | ATOM-CHESS-EL-001 |
| Revision | A |
| Status | Engineering draft / not for construction |
| Voltage systems | 127/220 VAC; 12 VDC; 5 VDC; 3.3 V logic |
| Drawing method | IEC multi-line schematic |
| Prepared date | 2026-07-31 |
| Prepared by | Engineering |
| Checked by | TBD |
| Approved by | TBD |

---

## Final design intent summary

The ATOM Chess electrical system uses a universal-input 12 VDC supply, a safety-switched `+12V_MOTOR` bus for five DRV8825 stepper axes, separate 5 V converters for computing and control loads, common DC return distribution, Orange Pi/Banana Pi/ESP32 processing layers, Ethernet/UART/Wi-Fi communication, a separately fused servo branch, five conditioned endstop inputs, and a dual-channel emergency-stop architecture that removes motor-driver power independently of software.
