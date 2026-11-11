"""Explicit configuration with repository-relative, contained source paths."""
from dataclasses import dataclass, field
import json
import os
from pathlib import Path


@dataclass
class Config:
    root: Path
    data: Path
    roots: list[str] = field(default_factory=lambda: ["docs", "Software", "simulation", "firmware", "hardware", "README.md", "CMakeLists.txt"])
    registry: str = "knowledge/sources/registry.json"
    model: str = "intfloat/multilingual-e5-small"
    model_revision: str = "614241f622f53c4eeff9890bdc4f31cfecc418b3"
    threads: int = 2
    max_file_bytes: int = 2_000_000
    context_chars: int = 14000
    min_semantic_score: float = 0.82

    @classmethod
    def load(cls, root=None, data=None, path=None):
        root = Path(root or os.getenv("ATOM_KNOWLEDGE_ROOT", ".")).resolve()
        values = json.loads(Path(path).read_text(encoding="utf-8")) if path else {}
        return cls(root=root, data=Path(data or os.getenv("ATOM_KNOWLEDGE_DATA", root / ".atom-knowledge")).resolve(), **values)

    def source(self, relative):
        candidate = self.root / relative
        resolved = candidate.resolve()
        if not resolved.is_relative_to(self.root):
            raise ValueError(f"Source escapes repository: {relative}")
        # Reject links even when their current target happens to be contained.
        if any(p.is_symlink() or p.is_junction() for p in [candidate, *candidate.parents] if p != self.root and p.is_relative_to(self.root)):
            raise ValueError(f"Linked source is not allowed: {relative}")
        return resolved
