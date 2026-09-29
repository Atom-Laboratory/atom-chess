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
ACM1|<seq>|SEG|<j1_rad>|<j2_rad>|<z_mm>|<gripper_pct>|<duration_ms>
```

Cancellation:

```
ACM1|<seq>|CANCEL
```

### Responses

```
ACM1|<seq>|ACK
ACM1|<seq>|DONE
ACM1|<seq>|ERR|<code>
ACM1|<seq>|ESTOP
ACM1|<seq>|LIMIT
```

### Sequence semantics

- sequence IDs are non-zero;
- host trajectory sequence IDs are strictly increasing;
- every SEG requires an ACK before execution is considered accepted;
- every accepted SEG requires DONE before the host advances to the next segment;
- a response for the wrong sequence is a protocol error;
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
