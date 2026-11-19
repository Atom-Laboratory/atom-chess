"""Artifact ownership resolved independently of the terminal directory."""
from pathlib import Path
import uuid

MODULE_ROOT = Path(__file__).resolve().parents[2]

def new_run(area):
    """Return a fresh, uncreated run path within an explicit module area."""
    owner = (MODULE_ROOT / area).resolve()
    if not owner.is_relative_to(MODULE_ROOT.resolve()):
        raise ValueError("Artifact owner must be inside the MuJoCo module")
    return owner / uuid.uuid4().hex
