"""Reproducible labeled-source ranking and mechanical evidence validation."""
from datetime import datetime, timezone
import json
import platform
from pathlib import Path
from statistics import mean
from .generation import ask
from .providers import file_hash


def evaluate(retriever, dataset, output, k=5, mode="hybrid"):
    retriever.store.db.execute("SAVEPOINT evaluation_snapshot")
    try:
        return _evaluate(retriever,dataset,output,k,mode)
    finally:
        retriever.store.db.execute("RELEASE evaluation_snapshot")


def _evaluate(retriever, dataset, output, k=5, mode="hybrid"):
    dataset, output = Path(dataset), Path(output)
    if output.exists(): raise ValueError("Evaluation output must be a fresh directory")
    questions = json.loads(dataset.read_text(encoding="utf-8"))
    cases, recalls, precisions, rr, absence, citations_ok, fidelity, numeric_checks, evidence_recalls = [], [], [], [], [], [], [], [], []
    for case in questions:
        gold = case["evidence"]
        for evidence in gold:
            source = retriever.config.source(evidence["path"]).read_text(encoding="utf-8-sig")
            if evidence["quote"] not in source:
                raise ValueError(f"Ground truth changed for {case['id']}: {evidence['path']}")
        results = retriever.search(case["question"],mode,k,case.get("filters"))
        answer = ask(retriever,case["question"],mode,k,case.get("filters"))
        numeric_correct = None
        if "numeric" in case:
            label = case["numeric"]
            measurements = retriever.store.observations(label["experiment"],label["metric"])["observations"]
            numeric_correct = any(o["source_path"]==label["source_path"] and o["value"]==label["value"] for o in measurements)
            numeric_checks.append(numeric_correct)
        expected = {e["path"].casefold() for e in gold}
        actual = [r["source_path"].casefold() for r in results]
        recall = len(expected & set(actual))/len(expected) if expected else None
        evidence_recall = sum(any(r["source_path"].casefold()==e["path"].casefold() and e["quote"] in r["text"] for r in results) for e in gold)/len(gold) if gold else None
        precision = sum(path in expected for path in actual)/k if expected else None
        rank = next((i for i,p in enumerate(actual,1) if p in expected),None)
        if expected:
            recalls.append(recall); precisions.append(precision); rr.append(1/rank if rank else 0); evidence_recalls.append(evidence_recall)
        else: absence.append(answer["insufficient_evidence"])
        for c in answer["citations"]:
            source_path = retriever.config.source(c["source_path"])
            valid = file_hash(source_path)==c["source_hash"]
            if c["start_line"] is not None:
                text = "\n".join(source_path.read_text(encoding="utf-8-sig").splitlines()[c["start_line"]-1:c["end_line"]])
                valid &= c["text"]==text
            citations_ok.append(valid)
        by_id = {c["citation"]:c for c in answer["citations"]}
        fidelity.extend(f["citation"] in by_id and f["quote"] in by_id[f["citation"]]["text"] for f in answer["facts"])
        cases.append({**case,"results":[{k:v for k,v in r.items() if k!="metadata"} for r in results],
                      "answer":answer,"recall_at_k":recall,"labeled_precision_at_k":precision,"reciprocal_rank":1/rank if rank else 0,
                      "numeric_correct":numeric_correct,"evidence_quote_recall_at_k":evidence_recall})
    summary = {"questions":len(cases),"answerable":len(recalls),"unanswerable":len(absence),"k":k,"mode":mode,
               "recall_at_k":mean(recalls) if recalls else None,"labeled_precision_at_k":mean(precisions) if precisions else None,
               "evidence_quote_recall_at_k":mean(evidence_recalls) if evidence_recalls else None,
               "mrr":mean(rr) if rr else None,"citation_correctness":mean(citations_ok) if citations_ok else None,
               "extractive_quote_fidelity":mean(fidelity) if fidelity else None,
               "unanswerable_abstention_rate":mean(absence) if absence else None,
               "insufficient_evidence_rate":mean(c["answer"]["insufficient_evidence"] for c in cases),
               "unsupported_fact_rate":1-mean(fidelity) if fidelity else None,
               "numeric_lookup_correctness":mean(numeric_checks) if numeric_checks else None,
               "limitations":"Small development set; relevance labels are not exhaustive. Precision is a labeled-source lower bound. Quote fidelity is mechanical, not semantic answer entailment. No LLM synthesis score is inferred."}
    report = {"created_at":datetime.now(timezone.utc).isoformat(),"dataset_sha256":file_hash(dataset),
              "implementation_sha256":{p.name:file_hash(p) for p in sorted(Path(__file__).parent.glob("*.py"))},
              "python":platform.python_version(), "platform":platform.platform(),
              "retrieval_config":{"context_chars":retriever.config.context_chars,"min_semantic_score":retriever.config.min_semantic_score},
              "manifest":retriever.store.get("manifest"),"summary":summary,"cases":cases}
    output.mkdir(parents=True)
    (output/"results.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    (output/"summary.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")
    return summary
