"""Paths and loading for the local HumanEval datasets."""

import gzip
import json
from pathlib import Path

PACKAGE_DIR = Path(__file__).resolve().parent
DATA_DIR = PACKAGE_DIR.parent / "data"
HUMANEVAL_FILE = DATA_DIR / "humaneval" / "HumanEval.jsonl.gz"
HUMANEVALPLUS_FILE = DATA_DIR / "humanevalplus" / "HumanEvalPlus-OriginFmt.jsonl.gz"


def read_tasks(path: Path) -> dict[str, dict]:
    if not path.exists():
        raise FileNotFoundError(f"{path} not found. Run ./scripts/download_data.sh first.")
    with gzip.open(path, "rt") as file:
        return {row["task_id"]: row for row in map(json.loads, file)}
