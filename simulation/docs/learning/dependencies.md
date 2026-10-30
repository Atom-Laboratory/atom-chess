# Free local experimentation tools

Primary sources checked on 2026-10-30. Only the existing Windows/Python 3.12
MuJoCo stack was exercised; no training framework was installed.

| Tool | Decision |
|---|---|
| Python standard library | Selected: scripts, JSON and provenance |
| MuJoCo 3.17.0 | Selected: direct physics API/viewer. [Documentation](https://mujoco.readthedocs.io/en/stable/python.html), [Apache-2.0](https://github.com/google-deepmind/mujoco/blob/main/LICENSE) |
| NumPy 2.5.4 | Selected: arrays/algebra/RNG. [BSD license](https://github.com/numpy/numpy/blob/main/LICENSE.txt) |
| pytest 9.2.0 | Selected development dependency in the verified lock |
| Gymnasium | Candidate after choosing spaces/task, for API/checker. [API](https://gymnasium.farama.org/api/env/), [MIT](https://github.com/Farama-Foundation/Gymnasium/blob/main/LICENSE). Not installed |
| PyTorch | Future candidate for personal networks/autograd on CPU. [Installation](https://pytorch.org/get-started/locally/), [license/component notices](https://github.com/pytorch/pytorch/blob/main/LICENSE). Not installed |
| Stable-Baselines3 | Later reference/baseline candidate. [Installation](https://stable-baselines3.readthedocs.io/en/master/guide/install.html), [MIT](https://github.com/DLR-RM/stable-baselines3/blob/master/LICENSE). Consulted docs require Python >=3.10 and PyTorch >=2.8; ATOM combination untested |
| Local JSON | Selected: readable records without account/server; derive CSV/plots later |

Official documentation/repositories offer public study/modification paths.
The consulted PyTorch page contains differing version references: resolve and
test a compatible stack in a separate venv when neural development begins.
CPU suffices for current exercises; training time depends on task/algorithm and
was not measured. Paid GPUs, hosted tracking and commercial APIs are unnecessary.
Preserve license notices. Tool licenses do not relicense ATOM/third-party hardware
or CAD. The lock is not a complete transitive license audit.
