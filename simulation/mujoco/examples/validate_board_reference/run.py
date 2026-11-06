"""Directory entry point preserving the original example module location."""
from pathlib import Path
import runpy
import sys

if __name__ == "__main__":
    source = Path(__file__).resolve().parents[1] / 'validate_board_reference.py'
    sys.path.insert(0, str(source.parent))
    runpy.run_path(str(source), run_name="__main__")
