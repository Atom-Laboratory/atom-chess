"""Transactional metadata, FTS, float32 vectors, and experiment observations."""
import json
from pathlib import Path
import sqlite3

SCHEMA = """
CREATE TABLE IF NOT EXISTS meta(key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS excluded(path TEXT PRIMARY KEY);
CREATE TABLE IF NOT EXISTS documents(
 source_id TEXT PRIMARY KEY, source_path TEXT UNIQUE NOT NULL, source_type TEXT NOT NULL,
 content_hash TEXT NOT NULL, document_version INTEGER NOT NULL, module TEXT NOT NULL,
 title TEXT NOT NULL, created_at TEXT, updated_at TEXT NOT NULL, metadata TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS chunks(
 chunk_id TEXT PRIMARY KEY, source_id TEXT NOT NULL REFERENCES documents ON DELETE CASCADE,
 text TEXT NOT NULL, content_hash TEXT NOT NULL, start_line INTEGER, end_line INTEGER,
 symbol TEXT NOT NULL, locator TEXT NOT NULL, vector BLOB);
CREATE INDEX IF NOT EXISTS chunks_source ON chunks(source_id);
CREATE VIRTUAL TABLE IF NOT EXISTS lexical USING fts5(chunk_id UNINDEXED, path, symbol, text, tokenize='unicode61 remove_diacritics 2');
CREATE TRIGGER IF NOT EXISTS delete_chunk AFTER DELETE ON chunks BEGIN
 DELETE FROM lexical WHERE chunk_id=old.chunk_id;
END;
CREATE TABLE IF NOT EXISTS observations(
 source_id TEXT NOT NULL REFERENCES documents ON DELETE CASCADE,
 experiment_id TEXT NOT NULL, metric TEXT NOT NULL, record INTEGER NOT NULL,
 value REAL NOT NULL, locator TEXT NOT NULL,
 PRIMARY KEY(source_id, metric, record));
CREATE INDEX IF NOT EXISTS metric_lookup ON observations(experiment_id, metric);
"""


class Store:
    def __init__(self, path, readonly=False):
        path = Path(path)
        if readonly:
            self.db = sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            self.db = sqlite3.connect(path)
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA foreign_keys=ON")
        self.db.execute("PRAGMA busy_timeout=30000")
        if not readonly:
            self.db.executescript(SCHEMA)

    def close(self):
        self.db.close()

    def get(self, key, default=None):
        row = self.db.execute("SELECT value FROM meta WHERE key=?", (key,)).fetchone()
        return json.loads(row[0]) if row else default

    def put(self, key, value):
        self.db.execute("INSERT OR REPLACE INTO meta VALUES (?,?)", (key, json.dumps(value, sort_keys=True)))

    def inventory(self):
        return [dict(r) | {"metadata": json.loads(r["metadata"])} for r in self.db.execute("SELECT * FROM documents ORDER BY source_path")]

    def remove(self, path, restore=False):
        with self.db:
            if restore:
                self.db.execute("DELETE FROM excluded WHERE path=?", (path,))
            else:
                self.db.execute("INSERT OR IGNORE INTO excluded VALUES (?)", (path,))
                self.db.execute("DELETE FROM documents WHERE source_path=?", (path,))

    def observations(self, experiment=None, metric=None, limit=1000, offset=0):
        clauses, args = [], []
        if experiment is not None:
            clauses.append("o.experiment_id=?"); args.append(experiment)
        if metric is not None:
            clauses.append("o.metric=?"); args.append(metric)
        where = " WHERE " + " AND ".join(clauses) if clauses else ""
        query = "SELECT o.*, d.source_path, d.content_hash, d.updated_at FROM observations o JOIN documents d USING(source_id)" + where
        total = self.db.execute("SELECT count(*) FROM (" + query + ")", args).fetchone()[0]
        rows = [dict(r) for r in self.db.execute(query + " ORDER BY d.updated_at DESC, o.source_id, o.record, o.metric LIMIT ? OFFSET ?", [*args, limit, offset])]
        # Group metadata is sourced from all registered files of this experiment.
        experiments = {}
        for doc in self.inventory():
            meta = doc["metadata"]
            eid = meta.get("experiment_id")
            if eid and (experiment is None or eid == experiment):
                experiments.setdefault(eid, []).append({"source_path": doc["source_path"], "content_hash": doc["content_hash"],
                                                       "updated_at": doc["updated_at"], "fields": meta.get("experiment_fields", {})})
        return {"observations": rows, "total": total, "limit": limit, "offset": offset, "experiments": experiments,
                "caution": "Values are reported observations, not comparable outcomes by default. Missing seed/config/checkpoint is unknown; updated_at is file mtime, not experiment chronology."}

    def integrity(self):
        errors = []
        if self.db.execute("PRAGMA integrity_check").fetchone()[0] != "ok": errors.append("sqlite integrity")
        if self.db.execute("PRAGMA foreign_key_check").fetchall(): errors.append("foreign keys")
        missing = self.db.execute("SELECT chunk_id FROM chunks EXCEPT SELECT chunk_id FROM lexical").fetchall()
        extra = self.db.execute("SELECT chunk_id FROM lexical EXCEPT SELECT chunk_id FROM chunks").fetchall()
        duplicate = self.db.execute("SELECT chunk_id FROM lexical GROUP BY chunk_id HAVING count(*)<>1").fetchall()
        if missing or extra or duplicate: errors.append("lexical/chunk mismatch")
        import numpy as np
        from hashlib import sha256
        identity = self.get("embedding")
        for row in self.db.execute("SELECT * FROM chunks"):
            if sha256(row["text"].encode()).hexdigest() != row["content_hash"]: errors.append("chunk hash: " + row["chunk_id"])
            if identity:
                v = np.frombuffer(row["vector"] or b"", dtype=np.float32)
                if len(v) != identity["dimension"] or not np.isfinite(v).all() or abs(np.linalg.norm(v)-1) > .01:
                    errors.append("vector: " + row["chunk_id"])
        return {"ok": not errors, "errors": errors, "documents": self.db.execute("SELECT count(*) FROM documents").fetchone()[0],
                "chunks": self.db.execute("SELECT count(*) FROM chunks").fetchone()[0], "numeric_observations": self.db.execute("SELECT count(*) FROM observations").fetchone()[0]}
