"""
LLM Client Abstraction Layer

Supports:
- Local models via Ollama (default)
- Anthropic Claude API (when API key provided)

Usage:
    # Local (default)
    client = LLMClient()
    
    # With Anthropic API
    client = LLMClient(provider="anthropic", api_key="your-key")
    
    # Or set environment variable
    # export ANTHROPIC_API_KEY="your-key"
    client = LLMClient(provider="anthropic")
"""

import os
import json
from typing import Optional, Dict, List, Any
from dataclasses import dataclass
from enum import Enum


class LLMProvider(Enum):
    LOCAL = "local"           # Ollama
    ANTHROPIC = "anthropic"   # Claude API
    NVIDIA = "nvidia"         # NVIDIA NIM (OpenAI-compatible)


@dataclass
class LLMConfig:
    """Configuration for LLM client"""
    provider: LLMProvider = LLMProvider.LOCAL
    
    # Local model settings (Ollama)
    local_model: str = "qwen2.5:32b"
    
    # Anthropic settings
    anthropic_model: str = "claude-3-5-sonnet-20241022"  # Default to Sonnet (best value)
    anthropic_api_key: Optional[str] = None

    # NVIDIA NIM (OpenAI-compatible) settings
    # Base URL from NVIDIA docs/model card.
    nvidia_base_url: str = "https://integrate.api.nvidia.com/v1"
    nvidia_model: str = "moonshotai/kimi-k2.5"
    nvidia_api_key: Optional[str] = None

    # You can upgrade to Opus for maximum quality:
    # anthropic_model: str = "claude-3-opus-20240229"
    
    # Generation settings
    max_tokens: int = 4096
    temperature: float = 0.7


class LLMClient:
    """
    Unified LLM client supporting local and cloud models.
    
    ═══════════════════════════════════════════════════════════════
    SETUP INSTRUCTIONS FOR ANTHROPIC API:
    ═══════════════════════════════════════════════════════════════
    
    1. Go to: https://console.anthropic.com
    2. Create account and add payment method
    3. Go to API Keys section
    4. Create new API key
    5. Either:
       a) Set environment variable:
          export ANTHROPIC_API_KEY="sk-ant-api03-..."
          
       b) Or pass directly:
          client = LLMClient(provider="anthropic", api_key="sk-ant-api03-...")
          
       c) Or create config file at: C2A/config/api_keys.json (or alongside this script in config/api_keys.json)
          {"anthropic_api_key": "sk-ant-api03-..."}
    
    PRICING (as of Jan 2025):
    - Claude 3.5 Sonnet: $3/1M input, $15/1M output (~$30 for Level 100)
    - Claude 3 Opus:     $15/1M input, $75/1M output (~$150 for Level 100)
    ═══════════════════════════════════════════════════════════════
    """
    
    def __init__(
        self,
        provider: str = "local",
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        config: Optional[LLMConfig] = None
    ):
        """
        Initialize LLM client.
        
        Args:
            provider: "local" for Ollama, "anthropic" for Claude API, "nvidia" for NVIDIA NIM
            model: Override default model for the provider
            api_key: API key for cloud providers (or use env var)
            config: Full LLMConfig object (overrides other params)
        """
        if config:
            self.config = config
        else:
            self.config = LLMConfig(
                provider=LLMProvider(provider),
                anthropic_api_key=api_key if provider == "anthropic" else None,
                nvidia_api_key=api_key if provider == "nvidia" else None
            )
            if model:
                if provider == "local":
                    self.config.local_model = model
                elif provider == "anthropic":
                    self.config.anthropic_model = model
                elif provider == "nvidia":
                    self.config.nvidia_model = model
        
        # Initialize the appropriate client
        self._init_client()
        
        # Token tracking for cost estimation
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.session_costs = []
    
    def _init_client(self):
        """Initialize the underlying LLM client"""
        
        if self.config.provider == LLMProvider.LOCAL:
            self._init_local()
        elif self.config.provider == LLMProvider.ANTHROPIC:
            self._init_anthropic()
        elif self.config.provider == LLMProvider.NVIDIA:
            self._init_nvidia()
    
    def _init_local(self):
        """Initialize Ollama client"""
        try:
            import ollama
            self.client = ollama
            self.model = self.config.local_model
            print(f"✓ LLM Client initialized: Ollama ({self.model})")
        except ImportError:
            raise ImportError("Ollama not installed. Run: pip install ollama")
    
    def _init_anthropic(self):
        """Initialize Anthropic client"""
        try:
            import anthropic
        except ImportError:
            raise ImportError("Anthropic not installed. Run: pip install anthropic")
        
        # Try to get API key from multiple sources
        api_key = self._get_anthropic_key()
        
        if not api_key:
            raise ValueError(
                "Anthropic API key not found. Please either:\n"
                "1. Set ANTHROPIC_API_KEY environment variable\n"
                "2. Pass api_key parameter to LLMClient\n"
                "3. Create config/api_keys.json with {'anthropic_api_key': 'your-key'}"
            )
        
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = self.config.anthropic_model
        print(f"✓ LLM Client initialized: Anthropic ({self.model})")
    
    def _get_anthropic_key(self) -> Optional[str]:
        """Get Anthropic API key from various sources"""
        
        # 1. Direct config
        if self.config.anthropic_api_key:
            return self.config.anthropic_api_key
        
        # 2. Environment variable
        env_key = os.environ.get("ANTHROPIC_API_KEY")
        if env_key:
            return env_key
        
        # 3. Config file
        config_path = os.path.join(os.path.dirname(__file__), "config", "api_keys.json")
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    config_data = json.load(f)
                    return config_data.get("anthropic_api_key")
            except:
                pass
        
        return None

    def _init_nvidia(self):
        """Initialize NVIDIA NIM (OpenAI-compatible HTTP API)"""
        api_key = self._get_nvidia_key()
        if not api_key:
            raise ValueError(
                "NVIDIA API key not found. Please either:\n"
                "1. Set NVIDIA_API_KEY environment variable\n"
                "2. Pass api_key parameter to LLMClient(provider='nvidia', api_key=...)\n"
                "3. Create config/api_keys.json with {'nvidia_api_key': 'your-key'}"
            )

        # Stored for request headers
        self._nvidia_api_key = api_key
        self._nvidia_base_url = self.config.nvidia_base_url.rstrip("/")
        self.model = self.config.nvidia_model
        self.client = None  # HTTP via requests
        print(f"✓ LLM Client initialized: NVIDIA NIM ({self.model})")

    def _get_nvidia_key(self) -> Optional[str]:
        """Get NVIDIA API key from various sources"""

        # 1. Direct config
        if self.config.nvidia_api_key:
            return self.config.nvidia_api_key

        # 2. Environment variable
        env_key = os.environ.get("NVIDIA_API_KEY")
        if env_key:
            return env_key

        # 3. Config file
        config_path = os.path.join(os.path.dirname(__file__), "config", "api_keys.json")
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    config_data = json.load(f)
                    return config_data.get("nvidia_api_key")
            except Exception:
                pass

        return None

    def chat(
        self,
        prompt: str,
        system: Optional[str] = None,
        history: Optional[List[Dict]] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        Send a chat message and get response.
        
        Args:
            prompt: The user message
            system: Optional system prompt
            history: Optional conversation history
            temperature: Override default temperature
            max_tokens: Override default max_tokens
            
        Returns:
            The assistant's response text
        """
        if self.config.provider == LLMProvider.LOCAL:
            return self._chat_local(prompt, system, history, temperature)
        elif self.config.provider == LLMProvider.ANTHROPIC:
            return self._chat_anthropic(prompt, system, history, temperature, max_tokens)
        elif self.config.provider == LLMProvider.NVIDIA:
            return self._chat_nvidia(prompt, system, history, temperature, max_tokens)
        else:
            raise ValueError(f"Unsupported provider: {self.config.provider}")
    
    def _chat_local(
        self,
        prompt: str,
        system: Optional[str] = None,
        history: Optional[List[Dict]] = None,
        temperature: Optional[float] = None
    ) -> str:
        """Chat via Ollama"""
        
        messages = []
        
        if system:
            messages.append({"role": "system", "content": system})
        
        if history:
            messages.extend(history)
        
        messages.append({"role": "user", "content": prompt})
        
        options = {}
        if temperature is not None:
            options["temperature"] = temperature
        
        response = self.client.chat(
            model=self.model,
            messages=messages,
            options=options if options else None
        )
        
        return response["message"]["content"]
    
    def _chat_nvidia(
        self,
        prompt: str,
        system: Optional[str] = None,
        history: Optional[List[Dict]] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> str:
        """Chat via NVIDIA NIM (OpenAI-compatible endpoint)"""

        try:
            import requests
        except ImportError as e:
            raise ImportError("requests not installed. Run: pip install requests") from e

        messages: List[Dict[str, str]] = []
        if system:
            messages.append({"role": "system", "content": system})
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": prompt})

        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature if temperature is not None else self.config.temperature,
        }
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens

        url = f"{self._nvidia_base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self._nvidia_api_key}",
            "Content-Type": "application/json",
        }

        resp = requests.post(url, headers=headers, json=payload, timeout=120)
        try:
            resp.raise_for_status()
        except Exception as e:
            # Try to include response body for debugging
            raise RuntimeError(f"NVIDIA NIM request failed: {resp.status_code} {resp.text[:500]}") from e

        data = resp.json()
        choice0 = (data.get("choices") or [{}])[0] or {}
        msg = choice0.get("message") or {}

        # Most OpenAI-compatible models put final text here
        content = msg.get("content")

        # Some NIM-served models may return null content and instead provide
        # text in reasoning_content / reasoning fields.
        if not content:
            content = msg.get("reasoning_content") or msg.get("reasoning")

        # If still empty, fail with a helpful error
        if not content:
            raise RuntimeError(
                "Unexpected NVIDIA NIM response shape (no content/reasoning fields): "
                f"{str(data)[:500]}"
            )

        # Token usage (if provided)
        usage = data.get("usage") or {}
        self.total_input_tokens += int(usage.get("prompt_tokens") or 0)
        self.total_output_tokens += int(usage.get("completion_tokens") or 0)

        return content

    def _chat_anthropic(
        self,
        prompt: str,
        system: Optional[str] = None,
        history: Optional[List[Dict]] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> str:
        """Chat via Anthropic API"""
        
        messages = []
        
        if history:
            messages.extend(history)
        
        messages.append({"role": "user", "content": prompt})
        
        kwargs = {
            "model": self.model,
            "max_tokens": max_tokens or self.config.max_tokens,
            "messages": messages
        }
        
        if system:
            kwargs["system"] = system
        
        if temperature is not None:
            kwargs["temperature"] = temperature
        
        response = self.client.messages.create(**kwargs)
        
        # Track tokens for cost estimation
        self.total_input_tokens += response.usage.input_tokens
        self.total_output_tokens += response.usage.output_tokens
        
        return response.content[0].text
    
    def get_cost_estimate(self) -> Dict[str, Any]:
        """Get estimated cost based on token usage (Anthropic only)"""
        
        if self.config.provider == LLMProvider.LOCAL:
            return {
                "provider": "local",
                "cost": 0.0,
                "note": "Local models are free"
            }
        
        if self.config.provider == LLMProvider.NVIDIA:
            return {
                "provider": "nvidia",
                "model": self.model,
                "input_tokens": self.total_input_tokens,
                "output_tokens": self.total_output_tokens,
                "note": "Pricing varies by model/NIM plan; see NVIDIA console for exact costs."
            }

        # Anthropic pricing (as of Jan 2025)
        pricing = {
            "claude-3-5-sonnet-20241022": {"input": 3.0, "output": 15.0},
            "claude-3-opus-20240229": {"input": 15.0, "output": 75.0},
            "claude-3-sonnet-20240229": {"input": 3.0, "output": 15.0},
            "claude-3-haiku-20240307": {"input": 0.25, "output": 1.25},
        }
        
        model_pricing = pricing.get(self.model, {"input": 3.0, "output": 15.0})
        
        input_cost = (self.total_input_tokens / 1_000_000) * model_pricing["input"]
        output_cost = (self.total_output_tokens / 1_000_000) * model_pricing["output"]
        total_cost = input_cost + output_cost
        
        return {
            "provider": "anthropic",
            "model": self.model,
            "input_tokens": self.total_input_tokens,
            "output_tokens": self.total_output_tokens,
            "input_cost": round(input_cost, 4),
            "output_cost": round(output_cost, 4),
            "total_cost": round(total_cost, 4),
            "total_cost_formatted": f"${total_cost:.2f}"
        }
    
    def reset_cost_tracking(self):
        """Reset token counters"""
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.session_costs = []


def create_client_from_env() -> LLMClient:
    """Create LLM client based on environment.

    Priority:
    1) If NVIDIA_API_KEY set: NVIDIA NIM
    2) Else if ANTHROPIC_API_KEY set: Anthropic
    3) Else: local Ollama

    Optional overrides:
    - C2A_LLM_PROVIDER: force provider (local|anthropic|nvidia)
    - C2A_LLM_MODEL: override model name for chosen provider
    """

    forced_provider = os.environ.get("C2A_LLM_PROVIDER")
    forced_model = os.environ.get("C2A_LLM_MODEL")

    if forced_provider:
        return LLMClient(provider=forced_provider, model=forced_model)

    if os.environ.get("NVIDIA_API_KEY"):
        return LLMClient(provider="nvidia", model=forced_model)
    if os.environ.get("ANTHROPIC_API_KEY"):
        return LLMClient(provider="anthropic", model=forced_model)

    return LLMClient(provider="local", model=forced_model)


# ═══════════════════════════════════════════════════════════════
# QUICK START
# ═══════════════════════════════════════════════════════════════
#
# FOR LOCAL (FREE):
#   client = LLMClient()
#   response = client.chat("Hello!")
#
# FOR ANTHROPIC (PAID, BETTER):
#   export ANTHROPIC_API_KEY="sk-ant-api03-..."
#   client = LLMClient(provider="anthropic")
#   response = client.chat("Hello!")
#
# FOR OPUS (MAXIMUM QUALITY):
#   client = LLMClient(provider="anthropic", model="claude-3-opus-20240229")
#
# ═══════════════════════════════════════════════════════════════


if __name__ == "__main__":
    # Test the client
    print("Testing LLM Client...\n")
    
    # Test local
    try:
        client = LLMClient(provider="local")
        response = client.chat("Say 'Hello from Ollama!' in exactly those words.")
        print(f"Local response: {response[:100]}...")
        print(f"Cost: {client.get_cost_estimate()}\n")
    except Exception as e:
        print(f"Local test failed: {e}\n")
    
    # Test Anthropic (if key available)
    if os.environ.get("ANTHROPIC_API_KEY"):
        try:
            client = LLMClient(provider="anthropic")
            response = client.chat("Say 'Hello from Claude!' in exactly those words.")
            print(f"Anthropic response: {response[:100]}...")
            print(f"Cost: {client.get_cost_estimate()}\n")
        except Exception as e:
            print(f"Anthropic test failed: {e}\n")
    else:
        print("Skipping Anthropic test (no API key set)")
        print("To enable: export ANTHROPIC_API_KEY='your-key'")
