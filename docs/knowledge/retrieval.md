# Retrieval and evidence semantics

FTS5 indexes paths, symbols and source text with Unicode tokenization and BM25.
Queries are tokenized and quoted before entering MATCH; SQL parameters carry
metadata values. Exact ADR/class/function/error identifiers receive an explicit
priority boost. Semantic search uses normalized 384-dimensional E5 vectors,
`query:`/`passage:` prefixes, and exact NumPy dot products. English and Portuguese
queries share this embedding space. Hybrid ranking sums `1/(60+rank)` from the
top 250 candidates per channel. An auditable Portuguese/English engineering
glossary adds a second query variant when terms match, preserving the original.
The same document vectors score both variants; the maximum score is used.
Literal adjacent concepts, rare lexical terms (1–10 matching chunks), symbol/path matches and explicit ADR intent add
deterministic relevance bonuses. Responses expose `query_variants`. These rules
were tuned on the small development dataset; there is no learned reranker.

Module, source type, experiment ID and UTC source-mtime filters apply before
candidate cutoffs. Returned duplicate chunk content is suppressed, although each
document keeps its provenance in storage. Exact vector scans are linear in corpus
size; they avoid a separate service but are not a large-scale ANN architecture.

Context assembly requires the current source hash to equal the indexed hash.
Questions naming exact identifiers only assemble chunks matching those identifiers;
unrelated fallback neighbors remain search diagnostics, not answer evidence.
It retains complete chunks and enforces a serialized-character budget. The
response includes file path, hash, chunk ID, line/page/paragraph locator and symbol.
The extracted answer quotes source assertions. Missing explicit identifiers
produce abstention; generic questions require lexical support plus a configurable
semantic relevance gate, or a stronger 0.90 semantic score without lexical support.
The gate is a heuristic, not a calibrated probability or proof of answerability.
It can both abstain unnecessarily and retrieve material that only partly answers
a question. Source inspection remains necessary for scientific conclusions.

Optional generation may select exact quotations and propose separately labeled
inferences with existing citation IDs. Invalid schema, nonexistent citations or
fabricated quotations fail closed. This protects the reported source text but
does not prove an inference, causal diagnosis or completeness. Hypotheses stay
source assertions even if repeated. Numeric queries should use the experiment
endpoint; it preserves observation identity and avoids model arithmetic.
