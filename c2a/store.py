"""Load and save the JSON files under data/. Personal files are gitignored."""

import json
import os
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def data_dir() -> Path:
    return Path(os.environ.get("C2A_DATA_DIR") or ROOT / "data")


def load(name, default=None):
    path = data_dir() / name
    if not path.exists():
        return default
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save(name, obj):
    path = data_dir() / name
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)
    os.replace(tmp, path)


def by_id(name):
    return {x["id"]: x for x in load(name, [])}


def progress():
    p = load("progress.json") or {}
    for key in ("attempts", "load_tests", "select", "cases"):
        p.setdefault(key, [])
    p.setdefault("patterns", {})
    p.setdefault("version", 1)
    return p


def save_progress(p):
    save("progress.json", p)


def append(name, record):
    items = load(name, [])
    items.append(record)
    save(name, items)


def now():
    return time.time()
