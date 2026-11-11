# Ingestion and provenance

Default roots: docs, Software/software, simulation, firmware, hardware, root
README and CMakeLists. Git-tracked and nonignored untracked paths are discovered;
case-insensitive root matching handles the repository's mixed Git spelling while
the source path retains the filesystem's spelling. Build/dependency directories,
environments, caches, runs/results/sessions, secret-like names and credential-like
content are excluded. Allowlists and pattern checks reduce accidental exposure;
they are not a universal secret/PII detector. Review external inputs before adding
them. CAD, images, archives and binary checkpoints are not embedded as text.

Python uses `ast`, C/C++ uses tree-sitter C++, Markdown uses headings and paragraph
boundaries. Short Markdown documents (up to 4500 characters) stay whole so an ADR's
title cannot become detached from its decision. Methods retain qualified symbols. Oversized function bodies remain
whole to preserve meaning; E5's 512-token window may truncate their embedding,
but lexical search and line references retain the complete body. C++ parse recovery
does not implement compiler semantic analysis or macro expansion. PDF citations
refer to pages and DOCX citations to paragraphs; they do not invent source lines.
UTF-8 text line numbering survives CRLF normalization.

SHA-256 identifies raw source bytes and normalized chunk text separately.
Documents carry source ID/path/type, content hash, per-source version, module,
title, updated UTC mtime and optional creation/publication date. Chunks add ID,
symbol, original line span or extraction locator. External source metadata is
preserved intact. Model revision and actual ONNX/tokenizer hashes are recorded.
Git HEAD describes a base, not the complete dirty checkout; each manifest also
records working-tree status and per-file hashes.

Incremental ingestion compares source and registration hashes. Identical chunks
reuse vectors under the same model identity. Modified documents replace their
chunks/FTS/observations in one transaction. Deleted, excluded or rejected files
lose their old rows, avoiding stale secret content. Full reindex rebuilds extraction
and indexes; a changed provider/pipeline identity requires it. A manifest reports
skips instead of concealing unsupported/oversized input.

Numeric JSON/JSONL/CSV leaves are stored by experiment, metric path, record and
original locator. No untrusted Python object deserialization is used. The original
flat metadata retains seeds, configs, checkpoint paths/hashes and missing values.
JSONL record numbers are physical lines; CSV locators are logical data records,
so embedded newlines do not produce incorrect line claims. Gzip is accepted only
for explicitly registered structured experiment files with bounded expansion.

Files changing during an active experiment are not a consistent experiment
snapshot. Prefer completed report exports. Citation assembly rehashes sources
and omits stale chunks; `integrity --sources` identifies files needing update.
