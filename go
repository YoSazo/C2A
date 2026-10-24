#!/usr/bin/env bash
set -e

# Go to script directory (so it works from anywhere)
cd "$(dirname "$0")"

# Create venv if it doesn't exist
if [ ! -d ".venv" ]; then
  python -m venv .venv
fi

# Activate venv
source .venv/bin/activate

# Install core requirements if missing
if ! python -c "import requests, numpy" &>/dev/null; then
  echo "Core packages not found. Installing..."
  pip install -U pip
  pip install -r requirements.txt
fi

# === LLM CONFIG ===
# C2A is OpenAI-only. Provide the key via the environment, or via
# config/api_keys.json ({"openai_api_key": "sk-..."}) which is gitignored.
# Never hardcode a key in this file — it is tracked by git.
if [ -z "${OPENAI_API_KEY:-}" ] && [ ! -s config/api_keys.json ]; then
  echo "Error: no OpenAI key found."
  echo "  export OPENAI_API_KEY='sk-...'"
  echo "  or write config/api_keys.json with {\"openai_api_key\": \"sk-...\"}"
  exit 1
fi

# Optional: pick a model (defaults to gpt-4o)
# export C2A_LLM_MODEL="gpt-4o-mini"

# Run app
python C2A.py
