#!/usr/bin/env python3
"""
llm_client.py
=============
The single LLM path for C2A. OpenAI only.

C2A used to fan out across Ollama, Anthropic and NVIDIA NIM. Three providers
meant three key-resolution paths, three response shapes, three failure modes,
and three chances for the training loop to break for reasons that had nothing
to do with training. There is now one.

Key resolution, in order:
    1. api_key= passed to the constructor
    2. OPENAI_API_KEY environment variable
    3. config/api_keys.json at the repo root, {"openai_api_key": "sk-..."}

That file is gitignored. Never commit a key.

Usage:
    from llm_client import LLMClient, create_client_from_env

    client = create_client_from_env()
    text = client.chat("Hello", system="Be brief.")
"""

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


DEFAULT_MODEL = "gpt-4o"
DEFAULT_BASE_URL = "https://api.openai.com/v1"

# Repo root is the parent of c2a_runtime/. Keys live at <root>/config/api_keys.json.
REPO_ROOT = Path(__file__).resolve().parent.parent
KEY_FILE_CANDIDATES = (
    REPO_ROOT / "config" / "api_keys.json",
    Path(__file__).resolve().parent / "config" / "api_keys.json",  # legacy location
)

# Models that take max_completion_tokens instead of max_tokens and reject
# a custom temperature. Matched by prefix.
REASONING_MODEL_PREFIXES = ("o1", "o3", "o4", "gpt-5")

# USD per 1M tokens. Used only for the running cost estimate; unknown models
# fall back to the generic entry rather than pretending to be free.
PRICING = {
    "gpt-4o":          {"input": 2.50, "output": 10.00},
    "gpt-4o-mini":     {"input": 0.15, "output": 0.60},
    "gpt-4.1":         {"input": 2.00, "output": 8.00},
    "gpt-4.1-mini":    {"input": 0.40, "output": 1.60},
    "gpt-4.1-nano":    {"input": 0.10, "output": 0.40},
    "o3":              {"input": 2.00, "output": 8.00},
    "o4-mini":         {"input": 1.10, "output": 4.40},
}
GENERIC_PRICING = {"input": 2.50, "output": 10.00}


class LLMError(RuntimeError):
    """Raised when the OpenAI call fails in a way the caller should surface."""


@dataclass
class LLMConfig:
    model: str = DEFAULT_MODEL
    api_key: Optional[str] = None
    base_url: str = DEFAULT_BASE_URL
    temperature: float = 0.8
    max_tokens: int = 2000
    timeout_seconds: float = 120.0
    session_costs: List[Dict[str, Any]] = field(default_factory=list)


class LLMClient:
    """OpenAI chat client. One provider, one response shape."""

    def __init__(
        self,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        provider: Optional[str] = None,
    ):
        """
        model:    OpenAI model id. Defaults to DEFAULT_MODEL or C2A_LLM_MODEL.
        api_key:  Overrides env and config file.
        base_url: Overrides the API host (for a proxy or compatible gateway).
        provider: Accepted only for backwards compatibility. Anything other
                  than "openai" is a hard error rather than a silent fallback.
        """
        if provider is not None and str(provider).lower() not in ("openai", ""):
            raise LLMError(
                f"C2A is OpenAI-only; provider={provider!r} is no longer supported. "
                "Drop the provider argument, or set C2A_LLM_MODEL to choose a model."
            )

        self.config = LLMConfig(
            model=model or os.environ.get("C2A_LLM_MODEL") or DEFAULT_MODEL,
            base_url=base_url or os.environ.get("C2A_OPENAI_BASE_URL") or DEFAULT_BASE_URL,
        )
        self.config.base_url = self.config.base_url.rstrip("/")

        self.config.api_key = api_key or self._resolve_api_key()
        if not self.config.api_key:
            raise LLMError(
                "OpenAI API key not found. Do one of:\n"
                "  1. export OPENAI_API_KEY='sk-...'\n"
                f"  2. create {KEY_FILE_CANDIDATES[0]} with "
                '{"openai_api_key": "sk-..."}\n'
                "  3. pass api_key= to LLMClient()"
            )

        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self._models_cache: Optional[List[str]] = None

        print(f"[OK] LLM Client initialized: OpenAI ({self.config.model})")

    # ── model property (callers assign to .model directly) ───────────────────

    @property
    def model(self) -> str:
        return self.config.model

    @model.setter
    def model(self, value: str) -> None:
        if value:
            self.config.model = value

    # ── key resolution ───────────────────────────────────────────────────────

    @staticmethod
    def _resolve_api_key() -> Optional[str]:
        env_key = os.environ.get("OPENAI_API_KEY")
        if env_key:
            return env_key.strip()

        for path in KEY_FILE_CANDIDATES:
            if not path.exists():
                continue
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                key = (data.get("openai_api_key") or "").strip()
                if key:
                    return key
            except Exception:
                continue
        return None

    # ── chat ─────────────────────────────────────────────────────────────────

    def _is_reasoning_model(self) -> bool:
        return self.config.model.startswith(REASONING_MODEL_PREFIXES)

    def chat(
        self,
        prompt: str,
        system: Optional[str] = None,
        history: Optional[List[Dict]] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """Send one turn and return the assistant text."""
        try:
            import requests
        except ImportError as e:
            raise LLMError("requests not installed. Run: pip install requests") from e

        messages: List[Dict[str, str]] = []
        if system:
            messages.append({"role": "system", "content": system})
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": prompt})

        payload: Dict[str, Any] = {"model": self.config.model, "messages": messages}
        limit = max_tokens if max_tokens is not None else self.config.max_tokens

        if self._is_reasoning_model():
            # Reasoning models reject temperature and rename the token cap.
            payload["max_completion_tokens"] = limit
        else:
            payload["temperature"] = (
                temperature if temperature is not None else self.config.temperature
            )
            payload["max_tokens"] = limit

        resp = requests.post(
            f"{self.config.base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=self.config.timeout_seconds,
        )

        if resp.status_code != 200:
            raise LLMError(
                f"OpenAI request failed: {resp.status_code} {resp.text[:400]}"
            )

        data = resp.json()
        choices = data.get("choices") or []
        if not choices:
            raise LLMError(f"OpenAI returned no choices: {str(data)[:400]}")

        content = (choices[0].get("message") or {}).get("content") or ""

        usage = data.get("usage") or {}
        self.total_input_tokens += int(usage.get("prompt_tokens") or 0)
        self.total_output_tokens += int(usage.get("completion_tokens") or 0)

        if not content.strip():
            finish = choices[0].get("finish_reason")
            raise LLMError(
                f"OpenAI returned empty content (finish_reason={finish!r}). "
                "If this is a reasoning model, raise max_tokens."
            )
        return content

    # ── model listing (drives the UI picker) ─────────────────────────────────

    def list_models(self) -> List[str]:
        """
        Chat-capable model ids available to this key, newest-looking first.
        Falls back to the configured model if the listing call fails, so the
        picker is never empty.
        """
        if self._models_cache is not None:
            return self._models_cache

        models: List[str] = []
        try:
            import requests

            resp = requests.get(
                f"{self.config.base_url}/models",
                headers={"Authorization": f"Bearer {self.config.api_key}"},
                timeout=15,
            )
            if resp.status_code == 200:
                for item in resp.json().get("data", []):
                    mid = item.get("id", "")
                    if mid.startswith(("gpt-", "o1", "o3", "o4", "chatgpt-")):
                        models.append(mid)
        except Exception:
            pass

        models = sorted(set(models))
        if not models:
            models = [self.config.model]
        self._models_cache = models
        return models

    # ── cost ─────────────────────────────────────────────────────────────────

    def get_cost_estimate(self) -> Dict[str, Any]:
        rates = PRICING.get(self.config.model, GENERIC_PRICING)
        input_cost = (self.total_input_tokens / 1_000_000) * rates["input"]
        output_cost = (self.total_output_tokens / 1_000_000) * rates["output"]
        total = input_cost + output_cost
        return {
            "provider": "openai",
            "model": self.config.model,
            "input_tokens": self.total_input_tokens,
            "output_tokens": self.total_output_tokens,
            "input_cost": round(input_cost, 4),
            "output_cost": round(output_cost, 4),
            "total_cost": round(total, 4),
            "total_cost_formatted": f"${total:.4f}",
            "estimated": self.config.model not in PRICING,
        }

    def reset_cost_tracking(self) -> None:
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.config.session_costs = []


def create_client_from_env() -> LLMClient:
    """Build the client from environment. C2A_LLM_MODEL overrides the model."""
    return LLMClient(model=os.environ.get("C2A_LLM_MODEL"))


if __name__ == "__main__":
    try:
        client = LLMClient()
    except LLMError as exc:
        print(f"[FAIL] {exc}")
        raise SystemExit(1)

    print(f"Available models: {', '.join(client.list_models()[:12])}")
    print(client.chat("Reply with exactly: OpenAI path is live."))
    print(f"Cost: {client.get_cost_estimate()['total_cost_formatted']}")
