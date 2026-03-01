#!/usr/bin/env python3
"""
RLM Configuration - Adjust based on your hardware

Your Setup: RTX 3060 (12GB), Ryzen 5 5600X, 32GB RAM
- Can run up to ~32B parameter models
- RLM analysis can use simpler approaches
"""

# Model options based on hardware
RLM_CONFIGS = {
    "high_end": {
        # 40GB+ VRAM, strong CPU
        "model": "qwen2.5-coder:32b",
        "use_code_generation": True,
        "max_context": 10_000_000,
        "description": "Full RLM with code generation"
    },
    
    "mid_range": {
        # 12-24GB VRAM (YOUR SETUP)
        "model": "qwen2.5:32b",
        "use_code_generation": False,  # Use simpler prompts instead
        "max_context": 1_000_000,
        "description": "Simplified RLM - no code generation, direct analysis"
    },
    
    "low_end": {
        # 8GB VRAM or less
        "model": "qwen2.5:7b",
        "use_code_generation": False,
        "max_context": 100_000,
        "description": "Basic analysis only"
    },
    
    "cpu_only": {
        # No GPU
        "model": "qwen2.5:7b",
        "use_code_generation": False,
        "max_context": 50_000,
        "description": "CPU inference - slow but works"
    }
}

# Auto-detect or manually set
RECOMMENDED_CONFIG = "mid_range"  # For your RTX 3060 setup

def get_rlm_config(config_name: str = RECOMMENDED_CONFIG):
    """Get RLM configuration"""
    return RLM_CONFIGS[config_name]

def can_use_rlm(config_name: str = RECOMMENDED_CONFIG) -> bool:
    """Check if RLM features are available"""
    config = RLM_CONFIGS[config_name]
    return config["use_code_generation"] or config["max_context"] >= 100_000
