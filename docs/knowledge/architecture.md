# Engineering knowledge architecture

Read the [pre-implementation audit](audit.md), [K001](../adrs/K001-engineering-knowledge-assistant.md)
and [operational README](../../tools/knowledge-assistant/README.md).

```text
argparse CLI / loopback read-only HTTP
                  |
        retrieval + context assembly
          /                   \
 SQLite FTS5 BM25       E5 query embedding
          \                   /
         reciprocal-rank fusion
         exact identifier priority
                  |
        current-source hash check
                  |
   quote-only answer / optional Ollama
      facts + inferences + citations

Git allowlist / explicit registry -> extraction -> contextual chunks
                   -> E5 passage embeddings -> one SQLite transaction
                   -> numeric experiment observations -> immutable manifest
```

`config.py` owns source containment and environment settings. `providers.py`
defines embedding/generator protocols and concrete local adapters. `ingestion.py`
owns discovery, syntax-aware boundaries, hashes and incremental writes.
`storage.py` owns persistence and numeric observation queries. `retrieval.py`
owns filters, lexical/vector ranking, deduplication and context size.
`generation.py` validates cited quotations and labels inference. `api.py` and
`cli.py` expose these operations. `evaluation.py` verifies labels and records
retrieved evidence. None imports ATOM simulation, motion, chess or firmware code.

SQLite is the authoritative store for documents, chunks, FTS and float32 vectors.
Changes commit atomically after successful embedding; a provider failure retains
the previous complete index. Manifests are also stored transactionally in SQLite;
JSON exports are a convenience copy created after commit. Reindexing preserves
source bytes and previous manifest exports. Exclusions survive full reindex.

Queries open SQLite read-only. The API has no endpoint for indexing, file deletion,
code execution or device access. Generation never receives tools. Source content
is serialized as untrusted data. Prompt instructions alone are not a security
boundary: limited capabilities, immutable source assertions and citation validation
are the concrete boundary. External LLM calls are not configured by default.
