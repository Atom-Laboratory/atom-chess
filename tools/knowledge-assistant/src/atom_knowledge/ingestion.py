"""Allowlisted discovery, contextual extraction, and atomic incremental ingestion."""
import ast
import csv
import gzip
from datetime import datetime, timezone
from hashlib import sha256
import io
import json
import math
import os
from pathlib import Path
import re
import subprocess
import sys
import uuid
import xml.etree.ElementTree as ET
import zipfile

from .providers import file_hash

PIPELINE = 3
TEXT = {".md", ".rst", ".txt", ".py", ".cpp", ".hpp", ".h", ".c", ".cc", ".ino", ".cmake", ".json", ".jsonl", ".csv", ".toml", ".yaml", ".yml", ".xml", ".xacro", ".urdf"}
CODE = {".py", ".cpp", ".hpp", ".h", ".c", ".cc", ".ino"}
DENY = {".git", ".venv", "venv", "env", "node_modules", "__pycache__", "build", "out", "bin", "lib", "install", "log", "logs", "cache", ".cache", ".atom-knowledge", "dist", "vendor", "third_party", "third-party", "assets", "media"}
SECRET_NAME = re.compile(r"(^\.env($|\.)|credential|secret|token|id_rsa|id_ed25519|\.pem$|\.key$)", re.I)
SECRET_TEXT = re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----|\b(?:gh[pousr]_[A-Za-z0-9]{20,}|AKIA[A-Z0-9]{16}|sk-[A-Za-z0-9]{24,})\b|(?:api_key|access_token|password)\s*[:=]\s*[\"'][^\"'\s]{12,}[\"']", re.I)


def digest(value):
    return sha256(value.encode()).hexdigest()


def allowed(path, explicit=False):
    parts = {p.lower() for p in Path(path).parts}
    return not (parts & DENY or (not explicit and parts & {"runs", "results", "sessions"}) or
                any(SECRET_NAME.search(p) for p in Path(path).parts))


def git_info(root):
    def run(*args):
        return subprocess.check_output(["git", "-C", str(root), *args], stderr=subprocess.DEVNULL).decode("utf-8", "replace").strip()
    try:
        return {"head": run("rev-parse", "HEAD"), "working_tree_status": run("status", "--porcelain"), "source": "working tree, including allowed untracked files"}
    except (OSError, subprocess.CalledProcessError):
        return {"head": None, "source": "filesystem without Git metadata"}


def discover(config):
    registry_path = config.source(config.registry)
    registry = json.loads(registry_path.read_text(encoding="utf-8")) if registry_path.exists() else {}
    found = {}
    def add(relative, metadata=None, explicit=False):
        p = config.source(relative)
        relative = p.relative_to(config.root).as_posix()
        if relative.startswith("docs/knowledge/"): return
        supported = p.suffix.lower() in TEXT | ({".pdf", ".docx"} if explicit else set())
        supported |= explicit and any(p.name.endswith(s+".gz") for s in (".json", ".jsonl", ".csv"))
        if not allowed(relative, explicit) or not supported:
            return
        if p.is_file() and not p.is_relative_to(config.data):
            found[relative] = metadata or {}
    # Git protects ordinary discovery from ignored build outputs and experiments.
    try:
        if not (config.root / ".git").exists(): raise FileNotFoundError("Root is a filesystem corpus")
        names = subprocess.check_output(["git", "-C", str(config.root), "ls-files", "-z", "--cached", "--others", "--exclude-standard"], stderr=subprocess.DEVNULL).decode().split("\0")
        for name in names:
            if name and any(name.casefold() == r.casefold() or name.casefold().startswith(r.rstrip("/").casefold() + "/") for r in config.roots):
                if not name.startswith("docs/knowledge/") and allowed(name): add(name)
    except (OSError, subprocess.CalledProcessError):
        for root in config.roots:
            base = config.source(root)
            if base.is_file(): add(root)
            elif base.exists():
                for directory, dirs, files in os.walk(base, followlinks=False):
                    dirs[:] = [d for d in dirs if allowed(str(Path(directory).relative_to(config.root) / d)) and not (Path(directory)/d).is_symlink() and not (Path(directory)/d).is_junction()]
                    for name in files:
                        if not (Path(directory)/name).is_symlink(): add(str((Path(directory)/name).relative_to(config.root)))
    for entry in registry.get("experiments", []):
        base = config.source(entry["path"])
        if not base.is_dir(): raise ValueError(f"Missing experiment directory: {entry['path']}")
        eid = entry.get("id", base.relative_to(config.root).as_posix())
        for name in entry.get("files", ["run.json", "report.json", "baseline.json", "failure.json", "progress.json", "episodes.jsonl", "ppo_updates.csv"]):
            candidate = config.source((base / name).relative_to(config.root))
            if not candidate.is_relative_to(base): raise ValueError("Experiment file escapes its directory")
            if not any(candidate.name.endswith(s) for s in (".json", ".jsonl", ".csv", ".json.gz", ".jsonl.gz", ".csv.gz")): raise ValueError("Only structured experiment files are allowed")
            if candidate.exists(): add(str(candidate.relative_to(config.root)), {"experiment_id": eid, "registration": entry}, True)
    for entry in registry.get("external", []):
        if not entry.get("url") or not entry.get("title"): raise ValueError("External sources require URL and title")
        if not config.source(entry["path"]).is_file(): raise ValueError("Missing registered external copy")
        add(entry["path"], {"external": entry}, True)
    return found, registry


def code_regions(text, suffix):
    """Return syntax boundaries and qualified symbols; never execute source."""
    regions = []
    if suffix == ".py":
        tree = ast.parse(text)
        def visit(node, parent=""):
            for child in ast.iter_child_nodes(node):
                if isinstance(child, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                    symbol = parent + "." + child.name if parent else child.name
                    start = min([child.lineno, *[d.lineno for d in child.decorator_list]])
                    regions.append((start, child.end_lineno, symbol))
                    visit(child, symbol)
                else: visit(child, parent)
        visit(tree)
    else:
        from tree_sitter import Language, Parser
        import tree_sitter_cpp
        parser = Parser(Language(tree_sitter_cpp.language()))
        data = text.encode()
        tree = parser.parse(data)
        def visit(node, parent=""):
            if node.type in {"function_definition", "class_specifier", "struct_specifier", "enum_specifier", "declaration", "field_declaration"}:
                name = node.child_by_field_name("name") or node.child_by_field_name("declarator")
                label = data[name.start_byte:name.end_byte].decode() if name else ""
                label = label.split("(")[0].strip()[:200]
                symbol = parent + "::" + label if parent and label else label or parent
                regions.append((node.start_point.row+1, node.end_point.row+1, symbol))
                if node.type == "function_definition": return  # Keep local declarations inside their function.
                if node.type in {"class_specifier", "struct_specifier"}: parent = symbol
            for child in node.named_children: visit(child, parent)
        visit(tree.root_node)
    return regions


def chunks_for_text(text, suffix, locator=None):
    lines = text.splitlines()
    if not lines: return []
    if suffix.lower() in {".md", ".rst"} and len(text)<=4500:
        excerpt="\n".join(lines)
        return [{"text":excerpt,"start_line":1,"end_line":len(lines),"symbol":"",
                 "locator":f"lines:1-{len(lines)}","content_hash":digest(excerpt)}]
    regions = code_regions(text, suffix) if suffix in CODE else []
    if suffix in CODE:
        # Definitions, methods and declarations are units. Large functions stay
        # intact; the embedding model's finite window is a documented limit.
        boundaries = {1, len(lines)+1}
        for start, end, _ in regions: boundaries.update((start, end+1))
        bounds = sorted(boundaries)
        spans = [(a, b-1) for a, b in zip(bounds, bounds[1:])]
    else:
        boundaries = {1, len(lines)+1}
        size = 0
        for index, line in enumerate(lines, 1):
            if re.match(r"^#{1,6} ", line) or (not line.strip() and size >= 1000):
                boundaries.add(index); size = 0
            size += len(line)+1
            if size > 2200:
                boundaries.add(index+1); size = 0
        bounds = sorted(boundaries)
        spans = [(a,b-1) for a,b in zip(bounds,bounds[1:])]
    output = []
    for start,end in spans:
        excerpt = "\n".join(lines[start-1:end])
        if not excerpt.strip(): continue
        symbols = sorted({name for a,b,name in regions if a <= start <= b and name})
        output.append({"text": excerpt, "start_line": start if locator is None else None,
                       "end_line": end if locator is None else None, "symbol": " / ".join(symbols),
                       "locator": locator or f"lines:{start}-{end}", "content_hash": digest(excerpt)})
    return output


def flatten(value, pointer=""):
    if isinstance(value, dict):
        for key, val in value.items():
            yield from flatten(val, pointer + "/" + str(key).replace("~", "~0").replace("/", "~1"))
    elif isinstance(value, list):
        for i, val in enumerate(value): yield from flatten(val, pointer + f"/{i}")
    else: yield pointer, value


def structured(text, suffix):
    rows, fields = [], {}
    if suffix == ".json":
        values = [(0, json.loads(text), "json:")]
    elif suffix == ".jsonl":
        values = [(i, json.loads(line), f"line:{i} json:") for i,line in enumerate(text.splitlines(),1) if line.strip()]
    elif suffix == ".csv":
        values = [(i, row, f"csv-record:{i} column:") for i,row in enumerate(csv.DictReader(io.StringIO(text)),1)]
    else: return rows, fields
    for record, value, prefix in values:
        for pointer, scalar in flatten(value):
            if record == 0: fields[pointer] = scalar
            if isinstance(scalar, bool) or scalar is None: continue
            try: number = float(scalar)
            except (ValueError, TypeError, OverflowError): continue
            if math.isfinite(number): rows.append((pointer, record, number, prefix+pointer))
    return rows, fields


def extract(config, relative, registration):
    path = config.source(relative)
    if path.stat().st_size > config.max_file_bytes: raise ValueError("file size limit exceeded")
    raw = path.read_bytes()
    suffix = path.suffix.lower()
    payload = raw
    if suffix == ".gz":
        suffix = Path(path.stem).suffix.lower()
        with gzip.GzipFile(fileobj=io.BytesIO(raw)) as stream:
            payload = stream.read(config.max_file_bytes+1)
        if len(payload)>config.max_file_bytes: raise ValueError("decompressed file size limit exceeded")
    if suffix == ".pdf":
        from pypdf import PdfReader
        reader = PdfReader(io.BytesIO(raw))
        chunks = []
        for i,page in enumerate(reader.pages,1): chunks.extend(chunks_for_text(page.extract_text() or "", ".txt", f"page:{i}"))
        if not chunks: raise ValueError("PDF has no extractable text; OCR is not implemented")
        text = "\n".join(c["text"] for c in chunks)
    elif suffix == ".docx":
        with zipfile.ZipFile(io.BytesIO(raw)) as archive:
            info = archive.getinfo("word/document.xml")
            if info.file_size > config.max_file_bytes*5: raise ValueError("DOCX expansion limit")
            document = ET.fromstring(archive.read(info))
        ns = {"w":"http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
        chunks = []
        for i,paragraph in enumerate(document.findall(".//w:p",ns),1):
            value = "".join(t.text or "" for t in paragraph.findall(".//w:t",ns))
            chunks.extend(chunks_for_text(value,".txt",f"paragraph:{i}"))
        text = "\n".join(c["text"] for c in chunks)
    else:
        text = payload.decode("utf-8-sig").replace("\r\n", "\n").replace("\r", "\n")
        if "\0" in text: raise ValueError("binary content")
        chunks = chunks_for_text(text,suffix)
    if SECRET_TEXT.search(text): raise ValueError("potential credential content; source excluded")
    metrics, fields = structured(text,suffix)
    if path.suffix.lower() == ".gz":
        for chunk in chunks:
            chunk["locator"] = "gzip:" + chunk["locator"]
            chunk["start_line"] = chunk["end_line"] = None
        metrics = [(m,r,v,"gzip:"+loc) for m,r,v,loc in metrics]
    metadata = dict(registration)
    if suffix in {".json", ".jsonl", ".csv"} and ("/evidence" in relative or "/runs/" in relative):
        metadata.setdefault("experiment_id", path.parent.relative_to(config.root).as_posix())
    if "experiment_id" in metadata: metadata["experiment_fields"] = fields
    kind = "external" if "external" in metadata else "experiment" if "experiment_id" in metadata else "code" if suffix in CODE else "adr" if "/adrs/" in relative.lower() else "configuration" if suffix in {".json", ".toml", ".yaml", ".yml", ".xml", ".xacro", ".urdf"} else "document"
    module = next((m for m in ("acvision", "acchess", "acmotion", "integration", "mujoco", "firmware", "hardware") if m in Path(relative).parts), "project")
    title = metadata.get("external", {}).get("title") or next((l.lstrip("# ") for l in text.splitlines() if l.startswith("# ")), path.name)
    updated = datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat()
    metadata["registration_hash"] = digest(json.dumps(registration, sort_keys=True))
    return {"source_id": digest(relative), "source_path": relative, "source_type": kind, "content_hash": sha256(raw).hexdigest(),
            "module": module, "title": title, "created_at": metadata.get("external",{}).get("date"), "updated_at": updated,
            "metadata": metadata, "chunks": chunks, "metrics": metrics}


def ingest(config, store, provider=None, full=False):
    candidates, registry = discover(config)
    excluded = {r[0] for r in store.db.execute("SELECT path FROM excluded")}
    identity = provider.identity if provider else None
    signature = {"pipeline": PIPELINE, "roots": config.roots, "max_file_bytes": config.max_file_bytes}
    if not full and store.get("pipeline") is not None and (store.get("embedding") != identity or store.get("pipeline") != signature):
        raise ValueError("Index identity changed; use index --full to regenerate all derived data")
    prior = {d["source_path"]: d for d in store.inventory()}
    seen, changed, skipped, unchanged = set(), [], [], 0
    for path, registration in sorted(candidates.items()):
        if path in excluded: continue
        old = prior.get(path)
        try:
            p = config.source(path)
            if p.stat().st_size > config.max_file_bytes: raise ValueError("file size limit exceeded")
            if not full and old and old["content_hash"] == file_hash(p) and old["metadata"].get("registration_hash") == digest(json.dumps(registration,sort_keys=True)):
                seen.add(path); unchanged += 1; continue
            doc = extract(config,path,registration)
            doc["document_version"] = (old["document_version"] + int(old["content_hash"] != doc["content_hash"])) if old else 1
            changed.append(doc); seen.add(path)
        except (UnicodeError, ValueError, SyntaxError, OSError, EOFError, csv.Error, ET.ParseError, zipfile.BadZipFile) as error:
            skipped.append({"source_path":path, "reason":str(error)})
    # Embeddings are calculated before the write transaction. Any provider error
    # leaves the last complete index intact. Reuse vectors for identical content.
    vector_cache = {}
    if provider and store.get("embedding") == identity:
        for row in store.db.execute("SELECT content_hash, vector FROM chunks WHERE vector IS NOT NULL"):
            vector_cache[row["content_hash"]] = row["vector"]
    pending = {}
    for doc in changed:
        for chunk in doc["chunks"]:
            pending.setdefault(chunk["content_hash"], chunk["text"])
    if provider:
        import numpy as np
        missing = [(h,t) for h,t in pending.items() if h not in vector_cache]
        print(f"Embedding {len(missing)} new unique chunks from {len(changed)} changed documents", file=sys.stderr, flush=True)
        for start in range(0,len(missing),64):
            batch = missing[start:start+64]
            vectors = provider.passages([t for _,t in batch])
            if vectors.shape != (len(batch),identity["dimension"]) or not np.isfinite(vectors).all(): raise ValueError("Invalid embeddings")
            for (h,_), vector in zip(batch,vectors):
                norm = np.linalg.norm(vector)
                if norm <= 0: raise ValueError("Zero embedding")
                vector_cache[h] = np.asarray(vector/norm, dtype=np.float32).tobytes()
            if start % 640 == 0 or start+64 >= len(missing):
                print(f"Embedded {min(start+64,len(missing))}/{len(missing)}", file=sys.stderr, flush=True)
    removed = sorted(set(prior)-seen)
    manifest = {"run_id": uuid.uuid4().hex, "created_at":datetime.now(timezone.utc).isoformat(), "git":git_info(config.root),
                "pipeline":signature, "embedding":identity, "registry":registry, "updated":len(changed), "unchanged":unchanged,
                "removed":removed, "skipped":skipped, "excluded":sorted(excluded)}
    with store.db:
        for path in removed: store.db.execute("DELETE FROM documents WHERE source_path=?",(path,))
        for doc in changed:
            store.db.execute("DELETE FROM documents WHERE source_id=?",(doc["source_id"],))
            keys = ["source_id","source_path","source_type","content_hash","document_version","module","title","created_at","updated_at"]
            store.db.execute("INSERT INTO documents VALUES (?,?,?,?,?,?,?,?,?,?)", [doc[k] for k in keys]+[json.dumps(doc["metadata"])])
            for i,c in enumerate(doc["chunks"]):
                cid = digest(f"{doc['source_id']}:{i}:{c['content_hash']}")
                store.db.execute("INSERT INTO chunks VALUES (?,?,?,?,?,?,?,?,?)",(cid,doc["source_id"],c["text"],c["content_hash"],c["start_line"],c["end_line"],c["symbol"],c["locator"],vector_cache.get(c["content_hash"])))
                store.db.execute("INSERT INTO lexical VALUES (?,?,?,?)",(cid,doc["source_path"],c["symbol"],c["text"]))
            if doc["metadata"].get("experiment_id"):
                for metric,record,value,locator in doc["metrics"]:
                    store.db.execute("INSERT INTO observations VALUES (?,?,?,?,?,?)",(doc["source_id"],doc["metadata"]["experiment_id"],metric,record,value,locator))
        store.put("embedding",identity); store.put("pipeline",signature)
        manifest["documents"] = [{k:d[k] for k in ("source_id","source_path","content_hash","document_version","updated_at")} for d in store.inventory()]
        store.put("manifest",manifest)
    folder = config.data / "manifests"; folder.mkdir(parents=True,exist_ok=True)
    (folder / (manifest["run_id"]+".json")).write_text(json.dumps(manifest,indent=2,ensure_ascii=False),encoding="utf-8")
    return {k:v for k,v in manifest.items() if k not in {"documents","git","registry","embedding"}} | {"documents":len(manifest["documents"])}
