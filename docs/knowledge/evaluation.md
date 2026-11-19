# Evaluation protocol

The initial dataset is [engineering-v1.json](../../knowledge/datasets/engineering-v1.json).
It contains real architecture, contract, ADR, code, experiment, numeric and
identifier queries plus explicit absence cases. Each positive label includes an
exact quotation checked against its original source before scoring. Negative
labels record their audit basis. Dataset files and assistant reports are excluded
from retrieval. No generated answer is used as ground truth.

Run from the repository root after installation and indexing:

```powershell
$kp = '.\tools\knowledge-assistant\.venv\Scripts\python.exe'
$evaluation = '.atom-knowledge/evaluations/' + [guid]::NewGuid().ToString('N')
& $kp -m atom_knowledge evaluate --output $evaluation --k 5 --mode hybrid
```

Repeat with `--mode lexical` or `--mode semantic` and a **new** output directory
for ablations. Outputs preserve the complete ingestion manifest, model hashes,
dataset hash, all questions, ranked source excerpts, expected sources, generated
extractive answers and per-question metrics. Large generated reports remain in
ignored data directories. A compact measured delivery record is maintained in
[validation.json](validation.json) and [delivery report](delivery-report.md).

- Recall@K: fraction of labeled source documents retrieved for each answerable
  question, averaged over answerable questions.
- Evidence-quote Recall@K: fraction of labels whose actual quoted evidence occurs
  in retrieved chunks, guarding against counting a title-only hit as sufficient.
- Labeled Precision@K: retrieved chunks whose path is labeled relevant divided by
  K. These relevance labels are not exhaustive; this is a conservative labeled
  precision, not a claim that all other chunks are irrelevant.
- MRR: reciprocal rank of the first labeled source, averaged over answerable cases.
- Citation correctness: current raw file SHA-256 and exact original line-span text.
- Extractive quote fidelity: every returned quotation is contained in its cited
  context. This is mechanical provenance, not semantic correctness/completeness.
- Unsupported fact rate: fraction of quotations failing that mechanical check.
- Insufficient-evidence rate: proportion of all cases returning abstention.
- Unanswerable abstention rate: correct abstentions on labeled negative questions.
- Numeric lookup correctness: exact structured value and source identity for
  numeric labels. Missing data never counts as zero.

This is a development set, not an independent held-out benchmark. It is too small
to claim broad recall, reliable absence recognition or calibrated confidence.
Changing thresholds after inspecting it is tuning, not independent validation.
LLM inference entailment, causal conclusions and contradiction handling require
human review and a separate generation evaluation. The Ollama adapter's HTTP
contract tests do not establish any real LLM's answer quality.

Relevant automated tests cover source mutations/deletions, idempotence, restart,
model mismatch and atomic failure, exact identifiers, metadata filters, content
deduplication, current citation checks, syntax boundaries, source exclusions,
registered compressed metrics, numerical provenance, strict citation validation,
HTTP isolation and the local LLM request contract. Fixture vectors are used only
in isolated unit tests; corpus evaluation uses the actual E5 ONNX encoder.
