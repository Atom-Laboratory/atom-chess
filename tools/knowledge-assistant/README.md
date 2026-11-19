# ATOM Engineering Knowledge Assistant

Read-only engineering retrieval over the actual ATOM repository. This package
does not import simulation/control modules, execute indexed code, dispatch robot
commands, change chess state or start training. Developer documentation and the
[architecture decision](../../docs/adrs/K001-engineering-knowledge-assistant.md)
describe the supported boundary. The interactive Playground, legacy v3 pixel
training and P038 native camera-guided residual environment remain separate.

## Install from the repository root

Prerequisites: Python 3.12 (validated on Windows), Git, approximately 1.5 GB free
disk for the isolated environment, model cache and initial index, and internet
access for the first dependency/model download. CPU inference is sufficient;
there is no required paid service or GPU. SQLite must include FTS5. A fresh
environment avoids changing MuJoCo or RL dependencies.

```powershell
uv venv --python 3.12 tools/knowledge-assistant/.venv
$kp = '.\tools\knowledge-assistant\.venv\Scripts\python.exe'
uv pip install --python $kp -r tools/knowledge-assistant/requirements-windows-py312.lock
uv pip install --python $kp --no-deps -e tools/knowledge-assistant
& $kp -m atom_knowledge --help
```

Without uv, use `python -m venv tools/knowledge-assistant/.venv`, then that
environment's `python -m pip install -r ...` and `python -m pip install --no-deps
-e ...`. On Linux the interpreter is `tools/knowledge-assistant/.venv/bin/python`;
install `-e 'tools/knowledge-assistant[test,pdf]'` for platform-resolved packages.
The lock records the validated Windows environment, including optional PDF/test
dependencies. Python 3.14 is not the validated runtime.

The default encoder is the real `intfloat/multilingual-e5-small` ONNX model at
revision `614241f622f53c4eeff9890bdc4f31cfecc418b3`. Its first download is about
493 MB. Inference uses two CPU threads. Model hashes and dependency identity are
persisted in the manifest; cached operation requires no network. No fallback
silently replaces this model with test vectors. FastEmbed 0.7.4 does not register
E5-small itself: the adapter explicitly registers mean pooling and normalization,
loads the pinned official ONNX files, and adds E5's query/passage prefixes.

## Build and maintain the knowledge index

All commands below run from the repository root. Initial indexing can take
several minutes on CPU; progress is written to stderr and the final JSON to stdout.

```powershell
& $kp -m atom_knowledge index
& $kp -m atom_knowledge update
& $kp -m atom_knowledge integrity --sources
& $kp -m atom_knowledge inventory
& $kp -m atom_knowledge index --full
```

Expected outputs: `.atom-knowledge/index.sqlite3`, cached models, and an immutable
JSON manifest per ingestion under `.atom-knowledge/manifests/`. An unchanged
update reports `updated: 0`, no removals and no duplicates. `integrity` reports
`ok: true`; `--sources` also detects moved/changed source bytes. Exit codes:
0 success, 1 failed integrity, 2 configuration/provider error. A full reindex
re-extracts every source; identical chunk vectors may be reused only when the
entire embedding identity matches. It preserves source files and old manifests.

```powershell
& $kp -m atom_knowledge remove docs/adrs/P014-validate-engine-moves-before-planning.md
& $kp -m atom_knowledge restore docs/adrs/P014-validate-engine-moves-before-planning.md
& $kp -m atom_knowledge update
```

These administrative commands only change the derived index and persistent
exclusion list. They do not delete repository files. `restore` enables subsequent
ingestion. They are intentionally absent from the HTTP API.

For lexical-only diagnosis without downloading a model, create a separate store:

```powershell
& $kp -m atom_knowledge --data .atom-knowledge/lexical index --lexical-only
& $kp -m atom_knowledge --data .atom-knowledge/lexical search P014 --mode lexical
```

This mode is explicitly not semantic RAG. Semantic/hybrid queries fail if their
model identity is absent or differs from the stored vectors. Do not mix indexes.

## Query source evidence

```powershell
& $kp -m atom_knowledge search 'Qual ADR define o contrato de estado físico confirmado?'
& $kp -m atom_knowledge search P014 --mode lexical
& $kp -m atom_knowledge search 'confirmação de estado físico' --mode semantic
& $kp -m atom_knowledge ask 'Onde planEngineTurn valida movimentos do Stockfish antes de planejar?'
& $kp -m atom_knowledge ask 'Quais limitações de identificação de peças tem a visão acvision?' --module acvision
& $kp -m atom_knowledge ask 'O que foi decidido no ADR P9999?'
```

`ask` now prints readable text by default, with model synthesis, exact quotations
and references separated. Use `ask ... --format json` for the full machine-readable
response. The HTTP API remains JSON. Search JSON includes path, original line range, symbol, content hash, document
version and ranking diagnostics. Ask JSON includes exact source assertions in
`facts`, separate `inferences`, and citation records. The default is an extractive
evidence report, not a claim to have written a complete explanation. A missing
identifier, insufficient retrieval score, stale source or empty context produces
`insufficient_evidence: true`. In particular, `BoardState` must not silently become
`PhysicalBoardState`. Sources can contain stale or hypothetical assertions;
quoted text remains an assertion by that source.

Filters: `--module`, `--source-type`, `--experiment`, `--after`, `--before`.
Dates filter source-file UTC mtime, **not** experiment event time. Use ISO-8601 UTC
timestamps. `--k` defaults to 5 (maximum 50). `ask --context-chars` limits the
serialized source context (default 14000 characters). Whole chunks that exceed
the remaining budget are omitted; no fabricated truncated line range is returned.
This is a character budget, not a tokenizer-specific LLM token count.

## Query numerical observations

```powershell
& $kp -m atom_knowledge experiments --experiment docs/camera-rl/evidence-p038 --metric /baseline/success_rate
& $kp -m atom_knowledge experiments --metric /trained_steps --limit 100
& $kp -m atom_knowledge experiments --experiment docs/camera-rl/evidence-p038 --limit 100 --offset 100
```

Expected: numeric values from SQLite with source path/hash, experiment ID, record
number, JSON pointer/CSV record locator, and associated source fields containing
configuration, seed and checkpoint identity when supplied. Null/missing fields
remain unknown. Booleans do not become numeric success rates. No success rate is
averaged across incompatible configurations, seeds or evaluation protocols.
`total`, `limit` and `offset` support bounded curve/history inspection. Identical
metric paths from different source files remain separate observations, enabling
comparison without inventing aggregates. Natural-language answers attach these
records when retrieved documents identify an experiment.

## Register sources deliberately

See [source registry instructions](../../knowledge/README.md). Default discovery
uses Git-tracked plus nonignored untracked files under the configured roots.
It excludes runs, build/dependency folders, secrets, caches, binary checkpoints,
CAD assets, and this assistant's evaluation/docs to avoid answer leakage.
Ignored experiment directories require explicit inclusion. External documents
are local copies with URL/title/author/date metadata; ingestion never scrapes URLs.
Born-digital PDF extraction is optional; scans require a separately reviewed OCR
workflow. DOCX extraction preserves paragraph identifiers, not visual page layout.

## Local LLM synthesis (no paid API)

The supported Windows setup uses portable Ollama 0.40.16 and `qwen3:4b`
(approximately 2.5 GB, Apache 2.0 model license). There is no required account,
subscription or per-token charge for local inference. Electricity, disk, RAM and
GPU/CPU use remain real costs. Internet access is needed for initial downloads;
cached inference sends prompts only to loopback. Cloud models are not configured.
References: [Ollama Windows](https://ollama.com/download/windows),
[Qwen3 4B model and license](https://ollama.com/library/qwen3:4b).

Prerequisites: the Python installation and index above, Windows PowerShell,
several GB of free disk, and enough RAM for the model. The validation host has
32 GB RAM and an RTX 5070 Ti with 16 GB VRAM. CPU execution is possible but slower.
The LLM competes with training for hardware; the adapter unloads it after each
request (`keep_alive: 0`). It does not start or stop training.

From the repository root, install the official portable runtime once:

```powershell
New-Item -ItemType Directory -Force .atom-knowledge | Out-Null
curl.exe -L --fail https://github.com/ollama/ollama/releases/download/v0.40.16/ollama-windows-amd64.zip -o .atom-knowledge/ollama-runtime.zip
Expand-Archive -LiteralPath .atom-knowledge/ollama-runtime.zip -DestinationPath .atom-knowledge/ollama-runtime
& ./tools/knowledge-assistant/start-local-llm.ps1 -Pull
```

Expected: runtime under `.atom-knowledge/ollama-runtime`, model blobs under
`.atom-knowledge/ollama-models`, server logs and an endpoint at
`http://127.0.0.1:11434`. The launcher starts a hidden local server with cloud
disabled. GPU discovery on a cold start may take several minutes; readiness is
polled for up to approximately five minutes, and generation allows 300 seconds.
If a server already exists, it reuses that server without changing its
settings/model directory. `-Pull` explicitly downloads the selected model; it
does not run on subsequent starts unless requested. No startup/login task is
installed. After reboot, run the launcher without `-Pull`.

```powershell
& ./tools/knowledge-assistant/start-local-llm.ps1
$kp = '.\tools\knowledge-assistant\.venv\Scripts\python.exe'
& $kp -m atom_knowledge ask 'O que determina P014?' --generator ollama --llm-model qwen3:4b
& $kp -m atom_knowledge ask 'O que determina P014?' --generator ollama --llm-model qwen3:4b --format json
& $kp -m atom_knowledge serve --generator ollama --llm-model qwen3:4b
```

Expected: a Portuguese synthesis labeled as model interpretation, short verbatim
source excerpts and paths/lines. Missing identifiers should abstain. The adapter
uses a source-constrained JSON schema, explicit answer instructions and an 8192-token runtime context, temperature zero and disabled thinking for
bounded JSON output. Only `--generator ollama` invokes the LLM; the default remains
extractive. No API keys or system-wide environment settings are written.

Check readiness with `Invoke-RestMethod http://127.0.0.1:11434/api/tags`. If the
model is missing, rerun the launcher with `-Pull`; if connection fails, inspect
the new server log and whether another process owns port 11434. The server stays
running after a query, while model memory is released. To stop this task's server,
identify the process whose executable is this repository's portable `ollama.exe`
and stop only that process. Do not stop unrelated training/Python processes.

Validation: `& $kp -m pytest tools/knowledge-assistant/tests -q` tests readable
formatting, JSON compatibility, adapter contracts and isolation. The separate
[local LLM validation record](../../docs/knowledge/local-llm-validation.json)
records real model identity, queries and citation validation results. A small
smoke test does not prove broad synthesis correctness. Invalid model JSON or
invented quotations fail closed; inferences still require human review.

Prerequisites: a separately installed local Ollama server and an available model.
No LLM weights are bundled or downloaded automatically by this package.

```powershell
$env:ATOM_KNOWLEDGE_LLM_MODEL = 'your-installed-model'
& $kp -m atom_knowledge ask 'O que determina P014?' --generator ollama
```

The adapter calls the local `/api/chat` endpoint with a fixed system policy
and untrusted source data. Facts must be exact substrings of cited context;
unknown citations and fabricated quotations fail closed. Interpretations stay in
`inferences`. Structural validation does not establish semantic entailment or
protect against every malicious document. There are no tools the model can call.
The default retrieval evaluation does not require Ollama. The historical delivery
report describes the extractive baseline; local-llm-validation.json records the
subsequent real-model smoke test separately from ranking metrics.

## HTTP and future Playground integration

```powershell
& $kp -m atom_knowledge serve --port 8765
```

From another terminal:

```powershell
Invoke-RestMethod http://127.0.0.1:8765/health
Invoke-RestMethod -Uri http://127.0.0.1:8765/ask -Method Post -ContentType application/json -Body '{"q":"P014","k":5}'
Invoke-RestMethod 'http://127.0.0.1:8765/experiments?metric=%2Fbaseline%2Fsuccess_rate'
```

Expected: JSON health, source-grounded answer and numeric observations. Ctrl+C
stops the API. It binds only to loopback, opens SQLite read-only, rejects browser
Origin requests and does not expose mutations. It is a single-user development
adapter, not a production authenticated service. See the [HTTP contract](../../docs/knowledge/api.md).
The future Playground can call this contract through its backend and render
citations separately from controls. No Playground integration is installed here.

## Tests and evaluation

```powershell
& $kp -m pytest tools/knowledge-assistant/tests -q
$evaluation = '.atom-knowledge/evaluations/' + [guid]::NewGuid().ToString('N')
& $kp -m atom_knowledge evaluate --output $evaluation
```

Expected: passing tests; fresh `results.json` and `summary.json` containing queries,
ranked evidence, expected sources, source/model identities, Recall@K, labeled-source
Precision@K, MRR, citation correctness, mechanical quotation fidelity and abstention.
Test embeddings are explicit test doubles and never counted as semantic validation.
The evaluation uses real E5 embeddings. Existing output directories are rejected.
See [evaluation limits and recorded results](../../docs/knowledge/evaluation.md).

Configuration: pass `--config knowledge/config.example.json` before the command.
Global `--root`/`ATOM_KNOWLEDGE_ROOT` and `--data`/`ATOM_KNOWLEDGE_DATA` select
repository and derived-data locations. `ATOM_KNOWLEDGE_OLLAMA_URL` and
`ATOM_KNOWLEDGE_LLM_MODEL` configure optional generation. Never store keys in
source registry files. No `.env` files are loaded.
