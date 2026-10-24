"""The shipped data must pass validation, and no LLM is needed for offline modes."""

import importlib
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def test_validate_data_passes():
    r = subprocess.run([sys.executable, str(ROOT / "tools" / "validate_data.py")],
                       capture_output=True, text=True, encoding="utf-8")
    assert r.returncode == 0, r.stdout + r.stderr


def test_every_pattern_has_ten_stories_and_sourced_examples():
    import json
    patterns = json.loads((ROOT / "data" / "patterns.json").read_text(encoding="utf-8"))
    drills = json.loads((ROOT / "data" / "drill_items.json").read_text(encoding="utf-8"))
    for p in patterns:
        assert p["real_examples"], p["id"]
        assert sum(d["pattern_id"] == p["id"] for d in drills) >= 10, p["id"]


def test_offline_modes_import_without_llm(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    for mod in ("c2a.drill", "c2a.select", "c2a.cases", "c2a.stats", "c2a.log", "c2a.cli"):
        importlib.import_module(mod)
