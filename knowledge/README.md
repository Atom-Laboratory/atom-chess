# Knowledge configuration and evaluation sources

Runtime and test commands are documented in the
[assistant README](../tools/knowledge-assistant/README.md). This directory stores
reviewable configuration, deliberate source registrations and human-reviewed
evaluation labels, not generated vectors or checkpoints.

`sources/registry.json` registers the three reviewed, archived canonical-v6
training/evaluation/warm-start directories present in this checkout. It includes
their run/report/baseline and PPO-curve files, not checkpoints. No external URL is
registered automatically. Default repository discovery already includes
allowed documentation, C++/Python code, tests, configs and published evidence JSON.
The registry adds ignored experiment data or external documents without modifying
the source. Paths must be repository-relative and contained; symlinks/junctions,
secrets and binary checkpoint ingestion are rejected.

Example registry entries (replace paths with existing files; these are not claims
that an example run or manual exists):

```json
{
  "experiments": [
    {
      "id": "my-reviewed-run",
      "path": "simulation/mujoco/training/autonomous-manipulation/runs/EXISTING_RUN",
      "files": ["run.json", "report.json", "ppo_updates.csv"]
    }
  ],
  "external": [
    {
      "path": "knowledge/sources/local/manual.pdf",
      "url": "https://publisher.example/manual",
      "title": "Component manual",
      "authors": ["Manufacturer"],
      "date": "2026-01-01",
      "accessed_at": "2026-11-10",
      "license": "Record the actual reuse conditions"
    }
  ]
}
```

Obtain the document through an approved source and retain its original copy.
`knowledge/sources/local/` is ignored by Git. The URL is provenance only: the
assistant never downloads it, follows links or runs scraping. PDF files require
the `pdf` optional dependency. Markdown, plain text and DOCX are supported too.
Registered experiment files support JSON, JSONL, CSV and gzip-compressed versions;
decompression is bounded by `max_file_bytes`. Files beyond the configured limit
are explicitly reported as skipped. Do not split an active run in place; register
a stable exported snapshot or choose a reviewed size limit in another config.

Run `update` after changing the registry. Removed registrations stop participating
in discovery and their index rows are removed (unless ordinary discovery also
includes the same source). Removing a source using the CLI creates a persistent
exclusion; `restore` and `update` re-enable it.

`datasets/engineering-v1.json` records questions and exact evidence quotations
from actual repository files. Absence labels state their audit basis. Keep it
outside ingestion; never use expected answers as retrieval content. Extend the
set with independently checked questions before treating its metrics as a broad
quality estimate.
