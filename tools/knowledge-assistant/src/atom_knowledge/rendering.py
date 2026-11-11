"""Readable CLI output; API and explicit JSON retain full provenance."""


def render_answer(answer):
    if answer["insufficient_evidence"]:
        lines = ["Evidências insuficientes para concluir."]
        if answer.get("missing_identifiers"):
            lines.append("Identificadores não encontrados: " + ", ".join(answer["missing_identifiers"]))
        if answer.get("generation_error"):
            lines.append("A síntese não passou pela validação: " + answer["generation_error"])
        return "\n".join(lines)
    lines = []
    if answer["inferences"]:
        lines.append("Síntese do modelo — confira as fontes:")
        for item in answer["inferences"]:
            lines.append(item["text"] + " [" + ", ".join(item["citations"]) + "]")
    lines.append("\nTrechos das fontes:")
    for fact in answer["facts"]:
        lines.append("[" + fact["citation"] + "] " + fact["quote"])
    lines.append("\nReferências:")
    used = {f["citation"] for f in answer["facts"]} | {c for i in answer["inferences"] for c in i["citations"]}
    for c in answer["citations"]:
        if c["citation"] in used:
            lines.append(f"[{c['citation']}] {c['source_path']} ({c['locator']})")
    return "\n\n".join(lines)
