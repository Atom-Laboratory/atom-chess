# EXP-0003 — Unchanged robot forward and single-step parity

Date: 2026-11-21. Related ADR: S054. Status: limited screen passed; full rollout
qualification pending. No policy training or candidate optimization occurred.

## Question and protocol

Can canonical MuJoCo 3.17.0 and MJWarp 3.17.0 reproduce the parked and restored
isolated-grasp states of the unchanged full-gripper robot? The experiment uses
Warp 1.19.0 on the native Windows RTX 5070 Ti, SM120. The model SHA is
`a88b0cdb6c2ac529d443f2bc695d4b94cf8306c2debd81838d06eda6f0790da7`.

Two worlds use a complete `mjSTATE_INTEGRATION` representation. The historical
final snapshot lacked some fields; those omitted fields are initialized to the
same defaults in both engines. This is a newly defined comparison state, not an
exact reconstruction of the historical solver warmstart or forces. The engine
model, colliders, contact settings, actuator gains, equality and masks are not
changed. Tolerances are declared in S054 and recorded per field.

## Measurements

[VERIFIED-RESULT] All declared forward and single-step screens passed at these
two states. Maximum body-position difference: 4.191e-8 m. Single-step maximum
qpos difference: 3.497e-8 (mixed model position coordinates); maximum qvel
difference: 1.179e-7 (mixed velocity units). Two unambiguous pad/target contact
pairs matched, with normal-force differences below 7.557e-7 N. Resetting one
world left the other's integration state bit-identical.

No overflow/convergence flag was set. Contact capacity was 128 across two worlds;
constraint capacity 256 per world. Final counts were two contacts and constraint
counts 1/9 for the two states. Warp pool usage was approximately 15.1 MB.
The bounded process took 312.04 s, dominated by cold compilation; this is not a
physics-throughput result.

Raw result: [robot-forward-step.json](../../../simulation/mujoco/accelerated/reports/EXP-0003/robot-forward-step.json).
Executed source hashes and complete initial states remain in the original fresh
run. The source was a precommit diff over 3c94488; the immutable source snapshot
is the exact executed implementation. Later additions record config/snapshot
hashes and return a nonzero CLI status on a failed screen; they do not alter this
historical result.

## Limitations and next gate

Only two states and one step were evaluated. No complete descent/closure/lift,
extended lifted hold, non-target collision trajectory, CEM population or learned
policy was validated. Unconditioned dynamics passed here; a later discrepancy
must examine float32 affine actuation and mass conditioning rather than infer a
backend defect from a long diverging rollout. State-array host copies are
qualification overhead, not optimized collection throughput.

Reproduce via the [GPU README](../../../simulation/mujoco/accelerated/README.md).
Ten CPU resource/state/contact matching tests passed. GPU robot execution was
measured separately; a test-suite pass alone is not GPU parity evidence.
