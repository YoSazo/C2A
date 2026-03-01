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

# Upgrade pip quietly
pip install -U pip >/dev/null

# === ENV VARS ===
export NVIDIA_API_KEY="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"
export C2A_LLM_PROVIDER="nvidia"
export C2A_LLM_MODEL="moonshotai/kimi-k2.5"

# Run app
python c2a_elegant_main.py
