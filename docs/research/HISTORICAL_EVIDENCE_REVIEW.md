# Historical evidence review and scope

Date: 2026-11-21. This review preserves earlier reports and distinguishes their
claims from raw measurements. It does not replace or edit the local untracked
Antigravity report copies. Current measured results are indexed in
[RESEARCH_INDEX.md](RESEARCH_INDEX.md).

## Inventory versus scientific verification

The point-in-time read-only inventory at commit `3c94488` covered 1,629 files,
93 Markdown documents, 55 simulation ADRs, 703 parsed JSON files and 436 checkpoint
archives. Its recorded scope is [historical-inventory-scope.json](historical-inventory-scope.json).
All inventoried Markdown bytes and JSON metadata were read for structural
extraction; raw logs/CSVs were hashed, not exhaustively reviewed, and historical
checkpoint metadata was inspected without executing pickle/tensors. No parse
error or concurrent file change was reported in that snapshot. These inventory
counts are not a claim that every experimental conclusion was independently
reproduced. The original detailed inventory remains in local read-only audit
artifacts; the tracked scope explicitly records this limitation.

The current [ADR catalog](ADR_CATALOG.md) and [machine-readable hashes](adr-catalog.json)
cover tracked ADR documents across core software, project and simulation folders.
Explicit statuses are copied without inferring acceptance. Original duplicate IDs
are preserved by filename. Untracked draft S037/S038 documents are excluded from
the published catalog until their owners add them.

## Recomputed historical reach metrics

The earlier local `ATOM_CHESS_MUJOCO_RL_REPORT.md` contains a useful architectural
narrative but several numerical/reporting assumptions need qualification. The
raw source report identities and per-seed values are preserved in
[historical-reach-metrics.json](historical-reach-metrics.json).

| Historical group | Reach successes | Median best pad distance | Mean complete-episode return |
| --- | --- | --- | --- |
| BC baseline, seeds 910000–910007 | 7/8 | 17.070843 mm | +4.462890 |
| PPO after BC, same seeds | 7/8 | 17.291576 mm | +4.424944 |
| PPO independent seeds 920000–920007 | 5/8 | 17.274573 mm | -10.751543 |

The independent group's mean is negative, rather than the +10.80 in the local
report. Its distance rounds to 17.27 mm. Seed 910003's post-PPO return is
-62.576122, rather than -.64. A +17.25 peak successful-episode return must not
be compared with a complete evaluation mean. Identical paired success counts
and a slightly larger post-PPO median distance do not establish a PPO advantage
over the BC baseline. These are reach results: the raw records do not mark them
as bilateral grasps or lifts.

The local report declares Windows 11 and SB3 2.7.1, whereas the measured current
host is Windows 10 Pro 19045 with SB3 2.9.2. Treat those as different environment
claims unless a matching historical environment artifact establishes the earlier
versions. Do not use the older narrative to overwrite measured current metadata.

Slip was observed, but a friction-only causal explanation was not established.
The later controlled solver/controller experiments are separately documented in
S050–S055 and EXP-0001/0004. Bounded reset/upper-head search failures likewise do
not prove universal mechanical infeasibility. Historical closed-gap prose must
be checked against the compiled model; EXP-0004's model audit measured .09556 mm
at the nominal closed command, distinct from older 3.096 mm prose.

## Implications for the current research

Keep reach, physical grasp, held lift, placement, isolated scenes and occupied
boards separate. Current EXP-0008 parameter-policy results are not a retroactive
correction of old trajectory-policy rewards or a replacement for their records.
Raw values, model/source identities, failure stages and physical evaluation
criteria take precedence over unsupported summary statements. Broader log-line
review and independent reproduction remain distinct future tasks.
