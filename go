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

# Upgrade pip and install core web app requirements if missing
if ! python3 -c "import numpy, anthropic, ollama" &>/dev/null; then
  echo "Core packages not found. Checking/upgrading pip..."
  pip install -U pip
  echo "Installing lightweight dependencies (numpy, anthropic, ollama)..."
  pip install numpy anthropic ollama
else
  echo "Core packages already installed. Skipping dependency installation."
fi

# === ENV VARS ===
# Require Anthropic key from shell/profile (do not hardcode secrets in repo)
if [ -z "${ANTHROPIC_API_KEY:-}" ]; then
  echo "Error: ANTHROPIC_API_KEY is not set."
  echo "Set it first, e.g.: export ANTHROPIC_API_KEY='sk-ant-api03-...'"
  exit 1
fi

export C2A_LLM_PROVIDER="anthropic"

# Run app
python C2A.py
