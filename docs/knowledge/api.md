# Read-only HTTP contract, version 1

Start from the repository root with `python -m atom_knowledge serve` using the
installed module environment. See its [README](../../tools/knowledge-assistant/README.md)
for exact setup, query commands, prerequisites, outputs and tests.

| Route | Method | Input | Output |
|---|---|---|---|
| `/health` | GET | None | `status`, `read_only`, embedding identity |
| `/inventory` | GET | None | Indexed document metadata and provenance |
| `/search` | POST (or GET) | `q`, optional `mode`, `k`, `filters` | Ranked chunks with citations and ranking diagnostics |
| `/ask` | POST (or GET) | Search fields plus `context_chars` | `status`, `facts`, `inferences`, `insufficient_evidence`, citations, observations |
| `/experiments` | GET | Optional `experiment`, `metric`, `limit`, `offset` | Numeric observations, total count and source metadata |

POST content type is `application/json`, maximum body size 16 KiB. Query length
is 1–4000 characters. `mode` is lexical, semantic or hybrid; `k` is 1–50.
Server defaults follow `serve --mode` and `--k`; lexical serving does not load
an embedding model. An explicit semantic request still requires that provider.
`filters` is an object with optional string fields `module`, `source_type`,
`experiment`, `after`, `before`; use POST for filters. `context_chars` is
256–100000, default 14000. Experiment page limit is 1–10000.

Responses are UTF-8 JSON. Status 400 means invalid input, 403 rejected browser
origin/Host, 404 unknown endpoint, 413 oversized input, 415 wrong content type,
503 unavailable provider. No CORS permission is emitted. Only localhost clients
with a local Host header are allowed. This reduces accidental exposure; there is
no multi-user authentication, TLS, availability guarantee or remote deployment
claim. Stop via Ctrl+C.

Future Playground integration should call this API from a separate backend
adapter, render source references and distinguish inference/absence. The answer
must never feed command dispatch, physical state commits or training control.
Do not add a direct bridge to motors or action APIs. No Playground files changed.
