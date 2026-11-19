# Engineering knowledge assistant — delivery and validation

This report records the initial extractive baseline. The subsequent local Ollama
setup, readable CLI format and real-model smoke results are documented in the
[module README](../../tools/knowledge-assistant/README.md) and
[local LLM validation](local-llm-validation.json). Statements below about an
unevaluated Ollama model describe the initial baseline only.

Validated locally on **2026-11-10** (America/Sao_Paulo). The pre-implementation
[audit](audit.md) started at Git HEAD `1997dd60bdb1738afb3cccba973d64087b7117ef`.
Concurrent unrelated repository work advanced HEAD to
`59ac5ecaba3d08f26e8816e5daa11e35a6c84cc5` before final ingestion. This task did
not commit, push, merge, stage unrelated work, change training, or modify CAD.
The evaluated working-tree corpus is identified by per-file hashes in ingestion
manifest `2143d692ba2e42ea97606fde7d4127bc`, rather than by HEAD alone.
Further source edits are detected by `integrity --sources` and suppressed during
citation assembly until `update` refreshes their entries.

## Implemented architecture and decisions

An isolated Python package exposes CLI and loopback HTTP queries over one SQLite
store. FTS5/BM25 supplies lexical retrieval; pinned multilingual E5-small ONNX
embeddings supply semantic retrieval. Hybrid retrieval uses reciprocal-rank
fusion, explicit engineering terminology expansion and deterministic relevance
bonuses. Short ADRs remain whole, Python/C++ chunks retain syntax boundaries and
symbols, and citations retain original lines or extraction locators.

SQLite stores document metadata, float32 vectors, FTS entries and structured
numeric observations transactionally. Provider interfaces separate embedding
and generation from ingestion/retrieval. The default answer returns exact source
assertions with references. Optional Ollama synthesis can add separately labeled
inferences, but fabricated quotation/citation IDs fail validation.

[K001](../adrs/K001-engineering-knowledge-assistant.md) compares RAG frameworks,
embedding models, vector stores, lexical search, LLM providers, document
extraction and API/CLI options. The implementation adds no distributed services,
mandatory paid provider, robot library dependency or learned reranker.

## Files and integration boundary

```text
tools/knowledge-assistant/
  pyproject.toml, requirements-windows-py312.lock, README.md
  src/atom_knowledge/
    config.py, providers.py, storage.py, ingestion.py
    retrieval.py, generation.py, evaluation.py, api.py, cli.py
  tests/test_pipeline.py
knowledge/
  config.example.json, sources/registry.json
  datasets/engineering-v1.json, README.md
docs/knowledge/
  audit.md, architecture.md, ingestion.md, retrieval.md, api.md
  evaluation.md, validation.json, delivery-report.md
docs/adrs/K001-engineering-knowledge-assistant.md
```

Only `.gitignore` and the documentation index were updated outside these new
paths. Generated indexes, model caches, evaluation runs and the new Python
environment are ignored. Existing simulation environments and code remain
independent. The API has no mutation or execution endpoint and opens SQLite
read-only. It cannot send ESP32 commands, change motor settings, move pieces,
commit chess state, rewrite checkpoints or manage training. No Playground
integration was installed; its future read adapter is documented.

## Sources actually indexed

The evaluated corpus contains **568 documents, 4,477 chunks and 4,781 numeric
observations**. Source types: 88 ADRs, 241 code files, 43 configurations, 154 other
documents and 42 experiment files. Module counts: acchess 35, acmotion 33,
acvision 38, integration 12, MuJoCo 191, firmware 3, hardware documentation 8,
and project/cross-module sources 248.

After evaluation, a final incremental refresh absorbed continuing unrelated source
edits. The delivered live index contains **569 documents, 4,480 chunks and 4,781
numeric observations**, under manifest `e69c86bbb66d4ea884c12240ad0cc892`.
Its final integrity and current-source checks passed with no stale sources. The
ranking table below deliberately retains the separately identified 568-document
evaluation snapshot rather than implying that ongoing edits were frozen.

Three canonical-v6 archived runs were explicitly registered: initial training,
independent held-out evaluation and warm-start. Their run/report/baseline and PPO
curve files are read through bounded gzip extraction. Existing published evidence
JSON is also indexed. Binary policies and CAD assets are not parsed as text.
**No external document was downloaded into the corpus.** External PDF/DOCX/text
copies can be explicitly registered with URL, title, authors and date.

One source was deliberately skipped because it exceeds the 2 MB default limit:
`simulation/mujoco/docs/reorganization-audit-2026-11-06/inventory.json`.
This is a historical reorganization inventory, not a silently accepted omission.
Its path and reason appear in every relevant manifest.

## Reproduce installation and execution

All commands run from the repository root in Windows PowerShell:

```powershell
uv venv --python 3.12 tools/knowledge-assistant/.venv
$kp = '.\tools\knowledge-assistant\.venv\Scripts\python.exe'
uv pip install --python $kp -r tools/knowledge-assistant/requirements-windows-py312.lock
uv pip install --python $kp --no-deps -e tools/knowledge-assistant
& $kp -m atom_knowledge index
& $kp -m atom_knowledge update
& $kp -m atom_knowledge integrity --sources
& $kp -m atom_knowledge ask 'O que determina P014?'
& $kp -m atom_knowledge serve --port 8765
```

Reuse the installed environment instead of recreating it on this checkout.
See the [module README](../../tools/knowledge-assistant/README.md) for portable
installation, filters, full reindex, exclusions/restoration, optional Ollama,
source registration, expected outputs and test commands. The API contract is
documented in [api.md](api.md). No model service must run for extractive answers.

## Working queries and traceable evidence

The final examples are recorded under
`.atom-knowledge/evaluations/current-checkout-20261110/examples.json`.

| Query | Verified source behavior |
|---|---|
| `O que determina P014?` | Returns `docs/adrs/P014-validate-engine-moves-before-planning.md`, lines 1–25, containing the validated-move-before-planning decision |
| `Onde planEngineTurn valida movimentos do Stockfish antes de planejar?` | Returns `Software/integration/src/engine_turn_planner.cpp`, lines 8–21; the function calls `validateUci` before `planTasks` |
| `What is the responsibility of PhysicalBoardState?` | Returns `simulation/mujoco/src/atom_mujoco/physical_state.py`, lines 120–125, including the single-owner store and externally verified snapshot contract |
| `O que foi decidido no ADR P9999?` | Returns `insufficient_evidence`, no invented fact or supporting citation |
| `Qual é a responsabilidade da classe BoardState?` | Abstains on the missing exact identifier instead of substituting another class |

The response records source hash and chunk identity as well as the path/range.
Current source bytes are checked before citation assembly. A source assertion
is not promoted to independently established physical truth. Inference is a
separate field. The structured experiment interface avoids model arithmetic:

```powershell
& $kp -m atom_knowledge experiments --metric /evaluation/success_rate
& $kp -m atom_knowledge experiments --experiment canonical-v6-training --metric /evaluation/success_rate
```

Directly checking the three canonical source archives against SQLite produced:

| Registered experiment | Reported success rate | Evaluation seeds | Training seed |
|---|---:|---|---:|
| canonical-v6-training | 0.0 | 910000, 910001 | 7 |
| canonical-v6-heldout-eval | 0.0 | 920000, 920001 | 7 |
| canonical-v6-warm-start | 0.0 | 910000, 910001 | 7 |

Each observation retains its original report hash, configuration hash, checkpoint
SHA-256 and `gzip:json:/evaluation/success_rate` locator in
[validation.json](validation.json). These are tiny, different evaluations; their
matching percentages do not establish equal policies, generalization or the cause
of a learning plateau. No new robotics experiment was run to produce these values.

## Evaluation results

Sixteen development questions include twelve answerable cases and four absence
cases. Labels were checked against actual source quotations. Evaluation files
are excluded from ingestion. All modes below use the same corpus and real pinned
E5 model, with implementation hashes and runtime/configuration recorded.

| Mode | K | Source Recall@K | Evidence-quote Recall@K | Labeled Precision@K | MRR |
|---|---:|---:|---:|---:|---:|
| Lexical | 5 | 91.7% | 83.3% | 25.0% | 0.7083 |
| Semantic | 5 | 50.0% | 50.0% | 10.0% | 0.2986 |
| Hybrid, default | 5 | 91.7% | 91.7% | 25.0% | 0.8194 |
| Hybrid, expanded candidates | 10 | 100.0% | 100.0% | 18.3% | 0.8333 |

Citation correctness and mechanical extractive quotation fidelity were 100% in
these runs. All four labeled absence cases abstained, including the unrelated
recipe question. The numeric ground-truth lookup passed. Hybrid abstained on
4/16 cases; semantic-only mode abstained on 9/16. The default hybrid miss at K=5
was the specifically labeled `docs/architecture.md` source, ranked sixth for the
vision/logical-state boundary question. `--k 10` retrieves that labeled evidence.

The initial evaluation exposed incomplete C++ discovery, title-only ADR chunks,
weak Portuguese/English matching and an irrelevant answer to an unrelated query.
Those issues drove corrections before this final measurement. This dataset was
used for development and tuning; **it is not a held-out benchmark**. Labels are
not exhaustive, so precision counts only labeled sources. Mechanical quotation
fidelity does not measure semantic entailment or answer completeness. Semantic-only
results are materially weaker than hybrid retrieval on this small technical set.

Full queries, candidates, expected sources, answers and manifests are in fresh
subdirectories of `.atom-knowledge/evaluations/current-checkout-20261110/`.
The compact versionable record is [validation.json](validation.json).

## Verification performed

- Seventeen automated tests passed, covering incremental update/deletion,
  idempotence, restart persistence, tombstones/restoration, full rebuild,
  provider failure atomicity, identity mismatch, syntax/line fidelity, filtering,
  deduplication, secret exclusions, external metadata, gzip metrics, unsupported
  identifiers, context limits, citations, API isolation and Ollama HTTP contract.
- Real-corpus idempotence check: **0 updated, 564 unchanged, 0 removed**.
  A later concurrent-work refresh updated 7 sources (including four new files)
  and retained 561 unchanged sources, producing the 568-source evaluated snapshot.
- SQLite, FTS membership, foreign keys, chunk hashes, normalized vector dimensions
  and current source hashes passed integrity checks.
- Real-index HTTP smoke exercised health, a cited P014 answer, a canonical numeric
  lookup and rejection of a nonexistent movement endpoint. The temporary server
  was shut down after verification.
- Three canonical numeric results were independently compared with their source
  archives; seeds/configuration/checkpoint identities were retained.
- Whitespace/diff checks passed. Existing robot/simulation suites were not rerun:
  their implementations were not changed and the new package imports none of them.
- Dependency verification found all 38 installed packages compatible. The final
  automated suite completed with 17 passes in 2.53 seconds.

The sandbox changed during execution and initially denied pytest temporary-file
access. Tests were subsequently rerun successfully with a fresh temporary
directory and appropriate execution permission; permission failures are not
counted as passing application tests.

## Limitations, infrastructure and next steps

CPU-only local retrieval has no per-query service charge. Initial installation
needs package downloads plus approximately 493 MB of official model files;
Windows caching may duplicate model data when symlinks are unavailable. Indexing
this corpus takes minutes, and exact vector scans scale linearly. Pinning and
file hashes support reproducibility; they do not guarantee identical floating-point
results across all ONNX runtimes or hardware.
The measured local footprint before the final small refresh was 146.5 MiB for
the isolated environment, 469.6 MiB for model files and 32.4 MiB for SQLite.

Ollama is integrated and its HTTP contract is tested, but **no real local LLM model
was installed or evaluated**. The delivered, exercised answer path is extractive.
External metadata registration is tested with local fixtures, not a downloaded
scientific-paper corpus. PDF support is text extraction without OCR; DOCX support
does not reconstruct visual layout. Oversized function embeddings may truncate at
E5's 512-token window even though source text and lexical references remain whole.
Secret-pattern exclusions are not a universal secret/PII detector. Review inputs.

Next steps: collect an independent labeled set, improve multilingual/code retrieval
against it, assess reranking only if it improves measured quality, evaluate a
chosen local LLM's inference fidelity, and register additional reviewed external
sources. A future Playground integration should render the read-only API's
evidence panel separately from all action controls. Remote/multi-user deployment
requires a separate authenticated server design.
