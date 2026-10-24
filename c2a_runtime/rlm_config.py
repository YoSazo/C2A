#!/usr/bin/env python3
"""
RLM Configuration — analysis depth tiers.

C2A runs on OpenAI only. These tiers trade cost against analysis depth;
they no longer describe local hardware. Override the model anywhere with
the C2A_LLM_MODEL environment variable.
"""

from llm_client import DEFAULT_MODEL

RLM_CONFIGS = {
    "max": {
        "model": "gpt-4o",
        "use_code_generation": True,
        "max_context": 128_000,
        "description": "Full RLM with code generation. Highest cost.",
    },
    "balanced": {
        "model": DEFAULT_MODEL,
        "use_code_generation": False,
        "max_context": 128_000,
        "description": "Direct analysis, no code generation. Default.",
    },
    "cheap": {
        "model": "gpt-4o-mini",
        "use_code_generation": False,
        "max_context": 128_000,
        "description": "Basic analysis only. Lowest cost.",
    },
}

RECOMMENDED_CONFIG = "balanced"


def get_rlm_config(config_name: str = RECOMMENDED_CONFIG):
    """Get RLM configuration."""
    return RLM_CONFIGS.get(config_name, RLM_CONFIGS[RECOMMENDED_CONFIG])


def can_use_rlm(config_name: str = RECOMMENDED_CONFIG) -> bool:
    """Check if RLM features are available."""
    config = get_rlm_config(config_name)
    return config["use_code_generation"] or config["max_context"] >= 100_000
