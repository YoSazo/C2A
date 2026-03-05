# C2A - Constraint-to-Advantage Training

Cognitive training system that turns constraints into advantages, with memory-enhanced coaching and a desktop app.

## Quick start

```bash
pip install -r requirements.txt
python setup.py
python C2A.py
```

## Project layout

| Path | Purpose |
|------|--------|
| `C2A.py` | Stable launcher entry (web backend) |
| `c2a_runtime/` | Core runtime files that actually power C2A |
| `c2a_runtime/C2A.py` | Main runtime server implementation |
| `ui/c2a_training.html` | Active Training Grounds UI |
| `ui/inspiration/` | Inspiration/reference UI files |
| `src-tauri/` | Tauri desktop wrapper |
| `extras/` | Optional scripts and smoke tests |
| `docs/` | Conversation/history notes |

If you want one folder to point another LLM at, use: `c2a_runtime/`.

## Requirements

- Python 3.10+
- Ollama (recommended): [ollama.ai](https://ollama.ai)
- A local model such as `qwen2.5:14b` or `mistral`

## Commands

- `python C2A.py` - start C2A Training Grounds (default)
- `python extras/test_elegant.py` - run smoke tests
- `npm run tauri:dev` - run desktop app
- `npm run tauri:build` - build installers

## Desktop app (Tauri)

Prerequisites:
- Python 3.10+ (with `py` launcher)
- Node.js 18+
- Rust toolchain (`rustup`, `cargo`, `rustc`)
- Microsoft C++ Build Tools (for Rust on Windows)

Installer output:
- `src-tauri/target/release/bundle/msi/*.msi`
- `src-tauri/target/release/bundle/nsis/*.exe`

"The essence of intelligence is turning constraints into advantages."
