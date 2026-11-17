# Fixed-camera approach screening (M2)

This paired experiment adds the RGB endpoint screen from
[S036](../../simulation/docs/adrs/S036-visual-approach-screen.md)
to the [M1 setup](native-approach-handoff-m1.md). It retains the camera,
models, seed set, native waypoint family, collision parameters, and
48-candidate limit. The preview renders a scratch scene assembled using
the visual scene estimates. It does not issue commands.

| Fixture | Seed | Rejected by visual screen | Sweep unresolved | Entry region uncertified | Admitted |
| --- | ---: | ---: | ---: | ---: | ---: |
| Full board | 7 | 40 | 3 | 5 | 0 |
| Full board | 8 | 40 | 3 | 5 | 0 |
| Isolated pawn | 7 | 34 | 6 | 8 | 0 |
| Isolated pawn | 8 | 32 | 8 | 8 | 0 |

Sweeps that blocked a route exhausted the existing preflight sample
budget. A timeout leaves safety unresolved. No approach command was
issued in these four trials. Local descent and lift were consequently
unavailable for this comparison. The earlier D2 interference remains
documented in the [local supervision report](hybrid-m4-supervision.md).

The next controlled comparison can vary the sweep budget alone to learn
whether otherwise viable visible candidates are certifiable. That leaves
the separate entry-box requirement in force. If the same candidate family
remains blocked, test a bounded lateral pre-approach waypoint with the
same camera. Workspace qualification and the deterministic grasp/lift
reference remain prerequisites to PPO.

Local results are under `simulation/mujoco/runs/native-handoff-m2-full-board-01`
and `simulation/mujoco/runs/native-handoff-m2-isolated-01`. The summary
and seed records preserve preview verdicts, IK and sweep evidence.
The handoff and approach regression modules gave 23 passes and one
fixture-dependent skip. The fixed-seed CLI runs supplied native evidence
for both fixtures separately.
