# S050 — Compare contact solvers in fresh grasp fixtures

Status: experimental comparison; no default physics change. Date: 2026-11-21.

## Context

An isolated factor-2.5 closure held both contacts for ten decisions, but lift
failed with approximately 0.011 mm piece rise. A separate read-only force audit
measured about 0.183 N normal load per pad at closure. During slow lift the
vertical contact forces stayed below the 0.1962 N piece weight, despite larger
nominal friction capacity. This suggests contact regularization as one possible
cause; it does not establish the cause or validate a new solver.

MuJoCo documents that soft friction constraints can slip under persistent load
even inside the Coulomb cone. It recommends elliptic cones and increased
`impratio` for reducing such slip. Increasing the friction coefficient is a
different physical change and is not required for this comparison.

## Decision

Provide a preparation tool that copies a verified input bundle into a fresh
fixture and changes only the XML option's cone and impedance ratio. Rehash the
model and record the exact input/output identities and solver options. Preserve
geometry, camera, piece mass, friction, gains, limits, collision masks, time step,
and the complete task configuration. Do not edit the source bundle or select
the new solver globally.

Compare pyramidal/1, elliptic/1 and elliptic/10 under the same seed, target,
preload, margin, speed and verification criteria. Keep NoSlip disabled. Each
diagnostic still has full sweeps, runtime contact/topple checks and the settled
grasp window. Ground-truth forces are diagnostic/evaluation data, never actor
inputs or targets.

## Alternatives and consequences

More PPO cannot diagnose a deterministic solver/geometry failure. Disabling
contacts or attaching a piece with a weld would not test a physical grasp.
Solver qualification is separate from policy learning and hardware calibration.
A positive isolated result still leaves crowded entry, visual outcome
verification, transfer, captures and hardware validation open.

References: [MuJoCo modeling, preventing slip](https://mujoco.readthedocs.io/en/3.15.0/modeling.html#preventing-slip)
and [contact computation](https://mujoco.readthedocs.io/en/stable/computation.html#contact).
