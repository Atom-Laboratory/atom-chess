# ESP32-S3 Motion Controller Firmware

Reference firmware for the ATOM Chess adaptation of Dejan's How To Mechatronics SCARA.

It receives the host-side ACM1 joint contract:

```
ACM1|<seq>|SEG|<j1_rad>|<j2_rad>|<j3_rad>|<z_mm>|<gripper_pct>|<duration_ms>
```

and controls:

- J1 NEMA 17 through STEP/DIR;
- J2 NEMA 17 through STEP/DIR;
- J3 NEMA 17 through STEP/DIR;
- Z NEMA 17 through STEP/DIR;
- MG996R-compatible gripper servo.

## Safety default

`robot_config.hpp` ships with:

```cpp
configured = false;
```

In this state the firmware boots and parses protocol traffic but replies `ERR|100` to movement commands.

Do not change this flag until all physical values are measured.

## Before enabling motion

Fill:

- STEP/DIR GPIOs for J1/J2/J3/Z;
- endstop GPIOs;
- E-stop GPIO;
- servo GPIO;
- J1/J2/J3 steps per radian;
- Z steps per millimetre;
- motor direction inversion;
- speed/acceleration limits;
- servo pulse limits.

Record the same values in:

`software/acmotion/docs/physical-calibration-template.md`

## Build

Install PlatformIO, then:

```bash
cd firmware/esp32-s3-motion
pio run
pio run -t upload
pio device monitor -b 115200
```

## Bring-up order

1. Build with `configured=false`.
2. Verify serial boot message.
3. Verify endstop/E-stop inputs.
4. Measure and enter pin/conversion configuration.
5. Keep motor power disabled and verify ACM1 parsing.
6. Enable one driver/axis at a time at conservative current and speed.
7. Verify J1, then J2, then J3, then Z.
8. Verify gripper.
9. Verify E-stop/limit interruption.
10. Only then enable full host MotionExecution.

The firmware contains no chess-domain logic and no inverse kinematics.


## Runtime cancellation

Cancellation is polled during active motion, not only between segments.

A matching:

```
ACM1|<active-seq>|CANCEL
```

discards the four step targets/speeds and returns `ACM1|<active-seq>|CANCELLED`.
`DONE` is reserved for normal segment completion. Wrong-sequence CANCEL is
rejected without cancelling the active segment. Idle CANCEL, including after
normal completion, returns `ERR|105`, not a cancellation acknowledgement.
Additional SEG commands during active motion are rejected rather than re-entered.

Cancellation, ESTOP and LIMIT latch motion inhibition. Further SEG commands are
rejected (`ERR|104`) even after the input clears. ESTOP/LIMIT take priority over
cancel at each polling boundary. The serial reader is shared between idle/active
paths, bounds work per poll, and discards overlong/NUL-containing frames through
their newline; empty fields and unsigned-number overflow are rejected.

`CANCELLED` confirms request acceptance and logical termination together, only
after discarding targets; there is no separate CANCEL ACK. It does not certify
deceleration, physical standstill, driver disable or power removal. The servo
gripper retains its command. `AccelStepper::stop()` alone would only schedule a
deceleration; this firmware clears software targets/speeds and exits the loop.

Host and firmware must be upgraded together. The ACM1 frame format remains, but
old hosts/firmware do not implement this cancellation contract. See
[ADR-005](../../software/docs/adrs/ADR-005-acm1-motion-protocol.md) for compatibility
and the deliberately unsupported concurrent host cancellation path (PR 4B).

There is no protocol unlock/resume command. A reboot alone is not proof of safe
recovery: inspect hardware, reconcile/home positions and resynchronize the host
session under an explicit recovery policy before deliberately restarting.
The shipped `configured=false` setting is unchanged. PlatformIO build success
does not validate any physical stop or safety input.

The physical E-stop must still be wired as an independent hardware safety mechanism; software cancellation is not a substitute for it.
