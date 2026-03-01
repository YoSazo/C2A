#!/usr/bin/env python3
"""
Setup script for C2A-Cortex Integration
"""

import subprocess
import sys
import os
from pathlib import Path

def install_requirements():
    """Install only new required packages"""
    print("📦 Checking for missing packages...")
    
    # Only install sentence-transformers if missing
    try:
        import sentence_transformers
        print("✓ sentence-transformers already installed")
    except ImportError:
        print("📥 Installing sentence-transformers...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "sentence-transformers>=2.2.0"])
            print("✓ sentence-transformers installed")
        except subprocess.CalledProcessError:
            print("❌ Failed to install sentence-transformers")
            return False
    
    print("✓ All dependencies ready")
    return True

def check_ollama():
    """Check if Ollama is available"""
    print("🤖 Checking Ollama installation...")
    try:
        result = subprocess.run(["ollama", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print("✓ Ollama found")
            
            # Check if mistral model is available
            result = subprocess.run(["ollama", "list"], capture_output=True, text=True)
            if "mistral" in result.stdout:
                print("✓ Mistral model available")
            else:
                print("📥 Downloading Mistral model...")
                subprocess.run(["ollama", "pull", "mistral"])
                print("✓ Mistral model downloaded")
            return True
        else:
            print("❌ Ollama not found. Please install from https://ollama.ai")
            return False
    except FileNotFoundError:
        print("❌ Ollama not found. Please install from https://ollama.ai")
        return False

def create_directories():
    """Create necessary directories"""
    print("📁 Creating directories...")
    memory_dir = Path(__file__).parent / "memory_data"
    memory_dir.mkdir(exist_ok=True)
    print("✓ Memory directory created")

def main():
    """Main setup function"""
    print("🧠 C2A-Cortex Integration Setup")
    print("=" * 40)
    
    # Install requirements
    if not install_requirements():
        sys.exit(1)
    
    # Create directories
    create_directories()
    
    # Check Ollama
    ollama_ok = check_ollama()
    if not ollama_ok:
        print("\n⚠️  Ollama not found. You can still run the system with other LLM providers.")
    
    print("\n🎯 Setup Complete!")
    print("\nTo start training:")
    print("python c2a_cortex_integrated.py")
    print("\n🧠 Ready to turn constraints into advantages!")

if __name__ == "__main__":
    main()