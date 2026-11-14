# ADR-005: Versioned ACM1 protocol and transport abstraction

## Status

Proposed for #154 / PR #155.

## Context

The Linux SBC must send joint-space motion segments to the ESP32-S3 while remaining independent of a specific serial library or device path.

The protocol must be simple enough to inspect during bring-up, explicit about sequence ownership, and robust enough to distinguish successful completion from timeout, controller error, emergency stop and limit-switch events.

## Decision

Use a versioned, line-delimited ASCII protocol named ACM1 for the MVP.

### Commands

Segment:

```
ACM1|<seq>|SEG|<j1_rad>|<j2_rad>|<j3_rad>|<z_mm>|<gripper_pct>|<duration_ms>
```

Cancellation:

```
ACM1|<seq>|CANCEL
```

### Responses

```
ACM1|<seq>|ACK
ACM1|<seq>|DONE
ACM1|<seq>|CANCELLED
ACM1|<seq>|ERR|<code>
ACM1|<seq>|ESTOP
ACM1|<seq>|LIMIT
```

### Sequence semantics

- sequence IDs are non-zero;
- host trajectory sequence IDs are strictly increasing;
- every SEG requires an ACK before execution is considered accepted;
- every accepted SEG requires DONE before the host advances to the next segment;
- a normal response for the wrong sequence is a protocol error; valid ESTOP/LIMIT
  events latch SafeStop even when their sequence differs;
- timeout is never treated as success;
- ESTOP and LIMIT force host SafeStop state.

### Transport abstraction

`MotionExecution` depends on `IMotionTransport`, not directly on UART/termios.

This enables:
- deterministic fake transport tests;
- Linux UART implementation later;
- USB CDC or socket transports if needed;
- protocol testing without powered motors.

## Why ASCII for MVP

ASCII is intentionally chosen for the first hardware integration because it:
- is easy to inspect with terminal tools;
- reduces firmware parser complexity;
- makes logs directly readable;
- allows protocol bring-up before binary framing is necessary.

A future binary protocol may supersede ACM1 if throughput or integrity requirements demand it. That requires a new ADR/version.

## Consequences

Host code can be validated before firmware is complete.

Firmware does not need chess or Cartesian types.

The protocol does not currently define checksums, retries or streaming windows. Those are intentionally deferred until real serial measurements show they are necessary.

## Bring-up rule

Do not start with motor power enabled.

First validate:
1. Linux device permissions;
2. baud/framing configuration;
3. line parsing;
4. sequence matching;
5. ACK/DONE;
6. ERR/ESTOP/LIMIT;
7. cancel behavior;
8. then enable low-current/low-speed motion.

## Related

- #56
- #58
- #154
- #155


## Joint 3 field

ACM1 segment frames include J1, J2, J3, Z and gripper. Because no production firmware had been frozen when J3 support was added, the MVP retained the ACM1 version while extending the SEG payload.

Any future incompatible framing change should increment the protocol version.


## Cancellation during execution

The ESP32-S3 parser must remain responsive to `CANCEL` while a segment is active. The reference firmware polls serial input inside the active-motion loop and rejects re-entrant SEG commands.

Software cancellation is operational control, not the primary safety mechanism. E-stop must remain independently wired at the hardware level.

### Cancellation completion and recovery (PR 4A)

- `ACK` accepts a SEG; `DONE` means only normal completion of that segment.
- Sending `CANCEL` proves only transport acceptance, not controller acceptance.
- Only a matching active CANCEL is accepted by the firmware. It discards the
  four STEP targets/speeds, latches motion inhibition and returns `CANCELLED`.
  This single terminal acknowledgement confirms request acceptance and logical
  cancellation together; there is no separate CANCEL ACK. No later `run()` call
  schedules a step for that segment. A wrong sequence does not cancel it.
- Idle CANCEL (including after DONE) returns `ERR|105` (NoActiveSegment), never
  DONE or CANCELLED. `ERR|104` rejects SEG after cancellation/safety inhibition.
- ESTOP has priority over LIMIT; both have priority over cancellation when
  observed at a polling boundary, including immediately after serial parsing.
- `CANCELLED` does **not** prove motor/arm standstill, successful deceleration,
  gripper release, driver disable or power removal. The gripper command is not
  reversed. Software positions are step counts, not measured physical positions.
  AccelStepper `stop()` only schedules a deceleration target; abandoning its
  polling loop does not execute that deceleration. The firmware instead clears
  targets with `setCurrentPosition(currentPosition())` and exits the segment.
  See the [AccelStepper reference](https://www.airspayce.com/mikem/arduino/AccelStepper/classAccelStepper.html).

Host `cancel()` keeps its bool signature but now blocks for `doneTimeout` and
returns true **only** after matching CANCELLED. It is available only after
`execute()` returned Error with a possibly outstanding command. During the wait
its state is CancelRequested; DONE/ACK, malformed/wrong-sequence replies, ERR,
missing replies and send failure cannot produce Cancelled. Valid ESTOP/LIMIT
instead latch SafeStop. Queued unrelated replies cause conservative failure;
this PR does not drain/reconcile a stale response stream.

The host is single-owner, blocking and not thread-safe: do not call cancel from
another thread or re-enter execution/transport from callbacks. Live cancellation
of a healthy blocking execute is **not supported** here. PR 4B must provide an
owner event loop/non-blocking progression with bounded safety/cancel latency,
serialized transport and deterministic interleaving tests before claiming it.

Error, SafeStop and confirmed Cancelled forbid another trajectory on the same
host instance (`RecoveryRequired`), without sending anything or clearing state.
There is deliberately no reset/resume API or firmware unlock command. Recreating
the host object or rebooting the controller is not a recovery policy. Recovery
requires external physical inspection, safe driver control, position/homing
reconciliation and transport/session resynchronization before any deliberate
restart. That policy and physical evidence remain prerequisites for PR 4B.
The firmware default remains `configured=false`.

### ACM1 compatibility decision

The SEG/CANCEL framing stays ACM1; CANCELLED is an additive response token for
the unfrozen MVP profile. Cancellation semantics are **not backward compatible**:
upgrade host and firmware together. A new host rejects legacy DONE cancellation
and remains blocked; an old host can still falsely report Cancelled merely on
send, so mixed versions must not be used. There is no capability negotiation.
A frozen/deployed protocol needs explicit version/capability agreement before
further incompatible changes; this patch does not claim mixed-version safety.

### Validation boundaries

Fake-transport tests cover acknowledgement correlation, failures and host latches.
They do not validate physical motion. An ESP32-S3 PlatformIO build proves target
compilation, not endstop wiring, cancellation latency, STEP pulses, mechanical
standstill or independent E-stop operation. Verify those on a powered-off-driver
bench first, then with a physically supervised low-energy bring-up. No firmware
hardware-in-loop test environment is supplied by this repository.
