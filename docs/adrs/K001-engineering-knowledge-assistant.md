# K001 — Local engineering knowledge assistant

Date: 2026-11-10. Status: accepted for the read-only knowledge increment.

## Context

The [audit](../knowledge/audit.md) found C++ modules and independent Python
simulation packages, mixed English/Portuguese documentation, structured local
experiments, and no existing RAG service. Preserve those module boundaries.

## Options and decision

| Area | Options considered | Decision and tradeoff |
|---|---|---|
| RAG framework | LangChain, LlamaIndex, small explicit pipeline | Explicit Python interfaces: fewer dependencies, inspectable provenance; adapters and evaluation are maintained here |
| Embeddings | English BGE, multilingual E5-small, multilingual MiniLM, paid embeddings | FastEmbed E5-small: local CPU inference, Portuguese/English retrieval, 384 dimensions; not a specialized code model, so exact symbols also use lexical search |
| Vector storage | Qdrant service/local mode, FAISS, SQLite blobs + NumPy | SQLite plus exact normalized dot products: one transactional store, no daemon or ANN tuning; linear scan is a documented scale limit |
| Lexical | SQLite FTS5/BM25, BM25 in Python, OpenSearch | FTS5: persistent, shipped with supported Python, weighted paths/symbols, Unicode tokenizer; explicit technical-token handling complements it |
| Generation | Ollama, hosted LLM, extractive evidence | Extractive default requires no LLM; optional Ollama adapter behind a protocol. No mandatory paid provider; semantic fidelity of synthesis needs separate evaluation |
| Extraction | pypdf, PyMuPDF, document services | UTF-8 text/AST/tree-sitter locally, optional pypdf for born-digital PDF, stdlib DOCX paragraph extraction; no OCR or layout reconstruction claims |
| API/CLI | FastAPI/Typer, stdlib HTTP/argparse | stdlib for this single-user, loopback-only read API; explicit JSON schema and request limits; replace adapter for authenticated remote deployment |
| Reranking | Cross encoder, fusion only | Reciprocal-rank fusion initially; add a model only after measured quality/latency benefit |

E5 requires `query:` and `passage:` prefixes, including non-English text.
Pin dependency resolution and record hashes of the actual downloaded model files
in the index identity. Never substitute fake/hash embeddings if model loading
fails. Lexical-only indexing remains an explicit diagnostic mode.

## Contracts

Source discovery is allowlisted and rejects links escaping the repository.
Each document records path, SHA-256, version, module, timestamps and source type;
chunks retain symbols and original line/page/paragraph references. Incremental
updates, deletes, lexical rows, vectors and numeric rows commit together. The
embedding/pipeline identity must match before mixing vectors. Explicit removal
persists an exclusion until restored. Full reindex changes only derived storage.

Numeric observations are queried in SQLite by experiment, metric and record,
with the original JSON pointer/CSV row and configuration/seed/checkpoint evidence.
Missing fields remain missing. No automatic causal diagnosis or incomparable
success-rate aggregation is allowed.

Retrieved text never becomes instructions or executable code. Generation has
no tools. The HTTP surface only searches, reads inventory, asks, and reads
experiment observations. No robot, training or source mutation API exists.
Synthesis must attach valid context citations, quote-backed evidence, and
separately labeled inference; validation cannot prove an inference is true.

## References consulted

- [FastEmbed](https://qdrant.tech/documentation/fastembed/): local ONNX embedding runtime.
- [E5 model card](https://huggingface.co/intfloat/multilingual-e5-small): multilingual model, prefix convention and context limit.
- [SQLite FTS5](https://sqlite.org/fts5.html): BM25 and persistent lexical indexing.
- [Ollama generate API](https://docs.ollama.com/api/generate): local structured generation.
- [pypdf extraction](https://pypdf.readthedocs.io/en/stable/user/extract-text.html): extraction and scanned-PDF limitations.

These references informed implementation choices; they are not silently added
to the project knowledge corpus. External sources require explicit registration.
