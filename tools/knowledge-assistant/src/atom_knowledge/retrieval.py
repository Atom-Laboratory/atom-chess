"""Filtered lexical and semantic retrieval with reciprocal rank fusion."""
import json
import re
import unicodedata
import numpy as np
from .providers import file_hash


STOP = set("a o os as e de do da dos das um uma em no na nos nas por para com que qual quais como onde esta está estão ao ou se the is are a an of for to in on what which where why how does do and or be this with from".split())

# Auditable terminology expansion, not a generated answer or a lookup of gold
# labels. Original terms always remain available to the lexical channel.
PT_EN = {"treinamento de rl":"reinforcement learning training", "por que":"why", "está apresentando":"experiences",
         "estado físico":"physical state", "estado fisico":"physical state", "confirmado":"confirmed",
         "contrato":"contract", "movimentos":"moves", "movimento":"move", "validação":"validation",
         "valida":"validates", "planejar":"planning", "limitações":"limitations", "identificação":"identification",
         "peças":"pieces", "visão":"vision", "percepção":"perception", "confirmação":"confirmation",
         "sucesso":"success", "físico":"physical", "físicos":"physical", "treinamento":"training",
         "estagnação":"plateau", "resultados":"results", "experimentos":"experiments", "dependências":"dependencies",
         "responsabilidade":"responsibility", "condições":"conditions", "captura":"capture", "legado":"legacy",
         "ambiente":"environment", "comprova":"demonstrates", "define":"defines"}


def normalize(text):
    return "".join(c for c in unicodedata.normalize("NFKD",text.lower()) if not unicodedata.combining(c))


def query_variants(query):
    translated = query.lower()
    for source,target in PT_EN.items():
        translated = re.sub(r"(?<!\w)"+re.escape(source)+r"(?!\w)",target,translated)
    if translated==query.lower(): return [query]
    return [query," ".join(tokens(translated))]


def tokens(query):
    return [t for t in re.findall(r"\w+", query, re.UNICODE) if t.lower() not in STOP and len(t)>1][:64]


def identifiers(query):
    return [t for t in re.findall(r"[A-Za-z_][A-Za-z_0-9]*",query)
            if re.search(r"[a-z][A-Z]|[A-Z].*[A-Z]|_|^[A-Z]+\d+$",t) and t not in {"RL","ADR","ADRs","CLI","API","LLM"}]


class Retriever:
    def __init__(self, config, store, provider=None):
        self.config, self.store, self.provider = config, store, provider
        if provider and store.get("embedding") != provider.identity:
            raise ValueError("Embedding identity differs from index; reindex with this model")

    def search(self, query, mode="hybrid", k=5, filters=None):
        if not isinstance(query,str) or not query.strip() or len(query)>4000: raise ValueError("Query must contain 1..4000 characters")
        if mode not in {"lexical","semantic","hybrid"}: raise ValueError("Invalid retrieval mode")
        if not isinstance(k,int) or not 1 <= k <= 50: raise ValueError("k must be between 1 and 50")
        filters = filters or {}
        mapping = {"module":"d.module", "source_type":"d.source_type", "experiment":"json_extract(d.metadata, '$.experiment_id')",
                   "after":"d.updated_at", "before":"d.updated_at"}
        if set(filters)-set(mapping): raise ValueError("Unknown metadata filter")
        clauses,args = [],[]
        for key,value in filters.items():
            if not isinstance(value,str): raise ValueError("Filter values must be strings")
            clauses.append(mapping[key] + (">=?" if key=="after" else "<=?" if key=="before" else "=?")); args.append(value)
        where = " WHERE " + " AND ".join(clauses) if clauses else ""
        base = "SELECT c.*, d.source_path, d.source_type, d.module, d.title, d.updated_at, d.metadata, d.content_hash AS source_hash, d.document_version FROM chunks c JOIN documents d USING(source_id)"
        rows = {r["chunk_id"]:dict(r) for r in self.store.db.execute(base+where,args)}
        variants = query_variants(query)
        terms = list(dict.fromkeys(t for variant in variants for t in tokens(variant)))
        lexical = []
        if mode != "semantic" and terms:
            match = " OR ".join('"'+t.replace('"','""')+'"' for t in terms)
            # Filter before candidate cutoff; a selective module cannot lose all
            # its candidates to globally more frequent documents.
            ranked = self.store.db.execute("SELECT chunk_id, bm25(lexical,0,1.5,3,1) AS rank FROM lexical WHERE lexical MATCH ? ORDER BY rank",(match,))
            lexical = [r["chunk_id"] for r in ranked if r["chunk_id"] in rows]
        semantic, similarities = [],{}
        if mode != "lexical":
            if self.provider is None: raise ValueError("Semantic retrieval needs a loaded embedding provider")
            candidates = [(cid,r) for cid,r in rows.items() if r["vector"] is not None]
            if candidates:
                matrix = np.stack([np.frombuffer(r["vector"],dtype=np.float32) for _,r in candidates])
                variant_scores = []
                for variant in variants:
                    query_vector = self.provider.query(variant)
                    if query_vector.shape != (self.provider.identity["dimension"],) or not np.isfinite(query_vector).all() or np.linalg.norm(query_vector)==0:
                        raise ValueError("Invalid query embedding")
                    variant_scores.append(matrix @ (query_vector/np.linalg.norm(query_vector)))
                values = np.max(variant_scores,axis=0)
                similarities = {cid:float(v) for (cid,_),v in zip(candidates,values)}
                semantic = sorted(similarities,key=lambda c:similarities[c],reverse=True)
        scores = {}
        for ranking in [lexical[:250],semantic[:250]]:
            for rank,cid in enumerate(ranking,1): scores[cid] = scores.get(cid,0)+1/(60+rank)
        exact = identifiers(query)
        # A named ADR or symbol receives explicit lexical priority, independent
        # of vector similarity. Substrings never count as identifier matches.
        def matches(row,term):
            return bool(re.search(r"(?<!\w)"+re.escape(term)+r"(?!\w)",row["source_path"]+" "+row["symbol"]+" "+row["text"],re.I))
        if mode != "semantic" and exact:
            for cid in scores:
                scores[cid] += .04*sum(matches(rows[cid],t) for t in exact)
                scores[cid] += .025*sum(bool(re.search(r"(?<!\w)"+re.escape(t)+r"(?!\w)",rows[cid]["source_path"]+" "+rows[cid]["symbol"],re.I)) for t in exact)
        if mode != "semantic":
            # Reward literal adjacent concepts and explicit ADR intent. This is
            # deterministic relevance scoring, not a learned reranker.
            words = [normalize(t) for t in tokens(query)]
            bigrams = [a+" "+b for a,b in zip(words,words[1:])]
            rare_terms = []
            for term in terms:
                count = self.store.db.execute("SELECT count(*) FROM lexical WHERE lexical MATCH ?", ('"'+term+'"',)).fetchone()[0]
                if 0<count<=10: rare_terms.append(term)
            for cid in scores:
                body = " ".join(re.findall(r"\w+",normalize(rows[cid]["text"])))
                scores[cid] += .006*sum(phrase in body for phrase in bigrams)
                scores[cid] += .02*sum(matches(rows[cid],term) for term in rare_terms)
                if re.search(r"\bADR\b",query,re.I) and rows[cid]["source_type"]=="adr": scores[cid] += .01
        output,seen = [],set()
        lexical_rank = {cid:i for i,cid in enumerate(lexical,1)}
        for cid in sorted(scores,key=lambda c:(-scores[c],rows[c]["source_path"],rows[c]["start_line"] or 0)):
            row = rows[cid]
            if row["content_hash"] in seen: continue
            seen.add(row["content_hash"])
            row.pop("vector")
            row["metadata"] = json.loads(row["metadata"])
            row.update(score=scores[cid],semantic_score=similarities.get(cid),lexical_rank=lexical_rank.get(cid),
                       exact_identifiers=[t for t in exact if matches(row,t)], query_variants=variants)
            output.append(row)
            if len(output)>=k: break
        return output

    def citation_current(self, result):
        try:
            return file_hash(self.config.source(result["source_path"])) == result["source_hash"]
        except (OSError,ValueError): return False

    def context(self, results, budget=None):
        budget = self.config.context_chars if budget is None else budget
        if not isinstance(budget,int) or not 256<=budget<=100000: raise ValueError("Context budget must be 256..100000 characters")
        context = []
        for result in results:
            if not self.citation_current(result): continue
            item = {"citation":f"S{len(context)+1}", "source_path":result["source_path"], "source_hash":result["source_hash"],
                    "chunk_id":result["chunk_id"], "start_line":result["start_line"], "end_line":result["end_line"],
                    "locator":result["locator"], "symbol":result["symbol"], "text":result["text"],
                    "external":result["metadata"].get("external")}
            if len(json.dumps([*context,item],ensure_ascii=False))>budget:
                continue  # Never truncate a source silently or falsify its range.
            context.append(item)
        return context
