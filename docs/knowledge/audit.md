# Engineering knowledge audit — 2026-11-10

Baseline: branch `ros2_simulation`, HEAD
`1997dd60bdb1738afb3cccba973d64087b7117ef`. The checkout contains unrelated
modified and untracked MuJoCo/hybrid-control work. It must remain untouched.

## Observed sources and environment

- CMake/C++ modules exist under **`Software/`**: acvision (OpenCV), acchess
  (Board, MoveValidator, Stockfish UCI), acmotion, and integration. Some older
  README paths use lowercase `software`; ingestion preserves actual case.
- Project ADRs are in `docs/adrs`, software ADRs in `Software/docs/adrs`, and
  simulation ADRs in `simulation/docs/adrs`. Hardware/firmware have separate
  documentation. Root architecture prose contains historical claims; its age
  must not override newer source evidence.
- `BoardState` is not an exact declared class found in the audited sources.
  Related concrete types are C++ `Board` and Python `PhysicalBoardState`.
- P007 defines confirmed physical snapshots. P014 defines engine-move validation;
  `Software/integration/src/engine_turn_planner.cpp` calls `validateUci` before
  `planTasks`.
- Python MuJoCo is a separate setuptools package requiring Python >=3.12,
  MuJoCo 3.17.0 and NumPy 2.x. RL extras use Gymnasium, SB3 and Torch. The
  interactive Playground, historical v3 pixel training, and P038 native
  camera-guided residual environment are distinct workflows.
- Experiment data includes run/report/baseline/failure JSON, episode JSONL,
  and steps/ppo_updates CSV in ignored `runs/` directories. Public evidence
  snapshots also exist in `docs/camera-rl/evidence-*`. Binary policies are not
  documents. Some current runs may still be changing.
- Host: Windows PowerShell, default Python 3.14; separate Python 3.12 is
  available through uv and the existing simulation environment. No Ollama
  executable was found. No existing RAG, vector service or HTTP framework was
  found in the audited project packages.

During implementation, unrelated work added staged portable training-diagnosis
reports and canonical-v6 gzip archives. These were read, never edited. Three
stable archive directories were explicitly registered after inspecting their
contents; missing fields and causal uncertainty remain visible. Git's index uses
`software/` for most C++ files and `Software/` for a few older documents, even
though this Windows checkout resolves both to `Software/`. Discovery accounts
for this discrepancy; no repository rename is performed.

## Architecture selected before implementation

Add an isolated Python 3.12 package at `tools/knowledge-assistant`, with no
dependency on simulation, robot libraries, ROS or firmware. Use SQLite FTS5 and
persisted NumPy-compatible vectors, local multilingual E5 embeddings through
FastEmbed, reciprocal-rank fusion, and structured experiment tables. Separate
provider, ingestion, storage, retrieval, generation and HTTP responsibilities.
The default answer is quoted source evidence; optional Ollama synthesis uses a
validated structured response and separates source excerpts from inference.
CLI uses argparse; a loopback-only HTTP adapter uses the standard library.
See [ADR K001](../adrs/K001-engineering-knowledge-assistant.md).

## Dependencies and limitations

New dependencies are isolated: NumPy, FastEmbed/ONNX Runtime, tree-sitter and its
C++ grammar. Optional PDF extraction uses pypdf. No paid service is required.
The embedding weights require an initial download; cached inference is local.
Exact vector scans suit this repository but do not promise million-document
scale. No reranker is justified before an evaluated baseline exists.

Default discovery excludes ignored experiments, secrets, builds, environments,
installed dependencies and binary/CAD assets. Explicit registries opt in local
experiment directories and external document copies, preserving their metadata.
Source content is untrusted. Hashes prove source identity, not scientific truth.
Retrieval cannot establish why RL stagnated without comparable measurements;
cross-profile metric comparisons require human interpretation. No training,
movement, physical configuration change, commit, push or merge is authorized.
