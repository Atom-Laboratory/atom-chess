"""Quoted evidence is distinct from optional, explicitly labeled inference."""
from .retrieval import identifiers


def validate_generation(value, context):
    if not isinstance(value,dict) or set(value)!={"facts","inferences","insufficient_evidence"}: raise ValueError("Invalid generation schema")
    if type(value["insufficient_evidence"]) is not bool or not isinstance(value["facts"],list) or not isinstance(value["inferences"],list): raise ValueError("Invalid generation types")
    citations = {c["citation"]:c for c in context}
    if len(value["facts"])+len(value["inferences"])>30: raise ValueError("Too many generated claims")
    for fact in value["facts"]:
        if not isinstance(fact,dict) or set(fact)!={"citation","quote"}: raise ValueError("Facts must be source excerpts")
        if not isinstance(fact["citation"],str) or not isinstance(fact["quote"],str) or not fact["quote"].strip() or fact["citation"] not in citations or fact["quote"] not in citations[fact["citation"]]["text"]:
            raise ValueError("Unverifiable quotation or citation")
    for inference in value["inferences"]:
        if not isinstance(inference,dict) or set(inference)!={"text","citations"} or not isinstance(inference["text"],str) or not isinstance(inference["citations"],list) or not inference["citations"] or any(not isinstance(c,str) or c not in citations for c in inference["citations"]):
            raise ValueError("Inference lacks valid citations")
    if not value["facts"]: value["insufficient_evidence"] = True
    return value


def ask(retriever, question, mode="hybrid", k=5, filters=None, context_chars=None, generator=None):
    results = retriever.search(question,mode,k,filters)
    exact = identifiers(question)
    scoped = [r for r in results if not exact or set(exact)<=set(r["exact_identifiers"])]
    context = retriever.context(scoped,context_chars)
    found = set(t for r in results for t in r["exact_identifiers"])
    missing = [t for t in exact if t not in found]
    # Scores are relevance gates, not proof that the requested answer exists.
    relevant = any(((r["semantic_score"] or 0)>=retriever.config.min_semantic_score and r["lexical_rank"] is not None)
                  or (r["semantic_score"] or 0)>=.90 or (exact and set(exact)<=set(r["exact_identifiers"])) for r in results)
    if mode=="lexical": relevant = bool(results) and not missing
    unsupported = not context or bool(missing) or not relevant
    answer = {"facts":[],"inferences":[],"insufficient_evidence":True}
    status = "insufficient_evidence"
    generation_error = None
    if not unsupported:
        if generator:
            try:
                answer = validate_generation(generator.generate(question,context),context)
                status = "generated" if not answer["insufficient_evidence"] else status
            except (ValueError,KeyError,TypeError) as error:
                generation_error = str(error)
        else:
            answer = {"facts":[{"citation":c["citation"],"quote":c["text"]} for c in context],
                      "inferences":[],"insufficient_evidence":False}
            status = "retrieved_evidence"
    # Quantitative questions use the numeric endpoint, never an invented summary.
    experimental = {r["metadata"].get("experiment_id") for r in scoped if not unsupported and r["metadata"].get("experiment_id")}
    observations = [retriever.store.observations(experiment=e,limit=100) for e in sorted(experimental)][:3]
    return {"question":question, "status":status, **answer, "citations":context, "missing_identifiers":missing,
            "experiments":observations, "generation_error":generation_error,
            "provider":generator.identity if generator else {"provider":"extractive"},
            "notice":"Facts are exact source assertions, not independently established truth. Retrieval alone does not establish a complete answer or causal explanation; inferences require review.",
            "retrieval":[{key:r[key] for key in ("chunk_id","source_path","score","semantic_score","lexical_rank")} for r in results]}
