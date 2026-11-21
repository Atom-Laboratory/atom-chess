# Stage A shared parameter-policy evidence

Read the [experiment](../../../../../docs/research/experiments/EXP-0008-shared-stage-a-parameter-policy.md)
for methodology, counts, source identities and limitations. Reproduction commands
and prerequisites are in the [module README](../../README.md).

| Files | Meaning |
| --- | --- |
| `pilot-*` | First three shared PPO updates: 24 macro episodes; pre/post GPU/CPU outcomes; BC and PPO raw metrics |
| `resume-*` | Restored model/Adam/Torch RNG, update 4, four additional macro episodes |
| `fresh-970202-*` | Frozen update-4 inference and CPU/GPU evaluation on one additional camera-localized entry |
| `FIG-0004-*`, `figure-provenance.json` | Unsmoothed metrics and deterministic CPU durations, with input hashes |
| `pilot-watch.json` | Two completed CPU replay cycles, explicitly not live optimization |
| `policy-update-4.pt` | Small identical copy of the latest verified policy/optimizer checkpoint; schema differs from legacy camera/reach PPO ZIPs |

Checkpoint SHA-256:
`f56f6e2d0c0e36539cc78748393b8e5d39b6578692b5fbe13ef668ff01ee9428`.
Size: 143,625 bytes. Large physical tapes/initial states and exact worker source
snapshots remain in local ignored runs named by the experiment and requests.

Actor inference uses native-camera source XY, issued actuator commands and the
logical task. Physics measurements supply reward/reset/safety/outcome only.
One macro episode is an entire isolated close/lift/hold, not one physics step.
There was one training entry; 28 successful parameter samples are not 28
independent board configurations. The BC mean already passed. Neither success
counts nor decreasing losses establish hardware readiness or occupied-board grasp.
