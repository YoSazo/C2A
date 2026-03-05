#!/usr/bin/env python3
"""Setup script for C2A Elegant."""

import subprocess
import sys
from pathlib import Path


def install_requirements() -> bool:
    """Install missing runtime dependencies."""
    print("[INFO] Checking for missing packages...")

    try:
        import sentence_transformers  # noqa: F401
        print("[OK] sentence-transformers already installed")
    except ImportError:
        print("[INFO] Installing sentence-transformers...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "sentence-transformers>=2.2.0"])
            print("[OK] sentence-transformers installed")
        except subprocess.CalledProcessError:
            print("[FAIL] Failed to install sentence-transformers")
            return False

    print("[OK] Dependency check complete")
    return True


def check_ollama() -> bool:
    """Check whether Ollama is installed and has at least one preferred model."""
    print("[INFO] Checking Ollama installation...")
    try:
        result = subprocess.run(["ollama", "--version"], capture_output=True, text=True)
        if result.returncode != 0:
            print("[FAIL] Ollama not found. Install from https://ollama.ai")
            return False

        print("[OK] Ollama found")
        result = subprocess.run(["ollama", "list"], capture_output=True, text=True)
        if "qwen2.5" in result.stdout or "mistral" in result.stdout:
            print("[OK] Found an installed local model")
            return True

        print("[INFO] No preferred model found. Pulling qwen2.5:14b...")
        subprocess.run(["ollama", "pull", "qwen2.5:14b"])
        print("[OK] Model pull attempted")
        return True
    except FileNotFoundError:
        print("[FAIL] Ollama not found. Install from https://ollama.ai")
        return False


def create_directories() -> None:
    """Create required directories."""
    print("[INFO] Creating directories...")
    memory_dir = Path(__file__).parent / "memory_data"
    memory_dir.mkdir(exist_ok=True)
    print("[OK] Memory directory ready")


def main() -> None:
    """Main setup function."""
    print("C2A Elegant Setup")
    print("=" * 40)

    if not install_requirements():
        sys.exit(1)

    create_directories()

    ollama_ok = check_ollama()
    if not ollama_ok:
        print("\n[WARN] Ollama unavailable. You can still use cloud providers.")

    print("\n[OK] Setup complete")
    print("Run: python C2A.py")


if __name__ == "__main__":
    main()