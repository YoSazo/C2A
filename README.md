# C2A — Constraint-to-Advantage Training

Cognitive training system that turns constraints into advantages, with memory-enhanced coaching and a terminal UI.

## Quick start

```bash
pip install -r requirements.txt
python setup.py          # optional: check deps and Ollama
python c2a_elegant_main.py
```

## What’s in the repo

| Path | Purpose |
|------|--------|
| `c2a_elegant_main.py` | **Main entry** — training flow, memory, RLM, lessons |
| `elegant_ui.py` | Terminal UI (colors, prompts, layout) |
| `c2a_desktop.py` | Optional desktop integration (Waybar, borders, wallpaper) |
| `constraint_archetypes.py` | Five constraint archetypes (scarcity, velocity, etc.) |
| `llm_scenario_engine.py` | LLM-generated scenarios |
| `llm_transmutation_judge.py` | Scoring and feedback |
| `llm_client.py` | LLM backend (Ollama, Anthropic, OpenAI, etc.) |
| `rlm_engine.py` | RLM analysis and safe execution |
| `active_lesson.py` | Active lesson and growth-edge tracking |
| `ai_researcher.py` | Session notes and research observations |
| `extras/` | Legacy/optional: Cortex flow, physics game, PDF ingestion, tests |

## Requirements

- **Python 3.10+**
- **Ollama** (recommended): [ollama.ai](https://ollama.ai), then e.g. `ollama pull mistral`
- See `requirements.txt` for pip packages; `requirements_elegant.txt` and `requirements-updated.txt` are legacy variants.

## Commands

- `python c2a_elegant_main.py` — start training
- `python extras/test_elegant.py` — run component tests

*“The essence of intelligence is turning constraints into advantages.”*
