"""One small OpenAI client over HTTPS (standard library only).

Configure with OPENAI_API_KEY and optionally C2A_MODEL (default gpt-4o) and
OPENAI_BASE_URL. Only `live` and `cases --check` use it.
"""

import json
import os
import re
import urllib.error
import urllib.request

DEFAULT_MODEL = "gpt-4o"
REASONING_PREFIXES = ("o1", "o3", "o4", "gpt-5")


class LLMError(RuntimeError):
    pass


def configured():
    return bool(os.environ.get("OPENAI_API_KEY", "").strip())


def require():
    if not configured():
        raise LLMError(
            "This mode needs an LLM. Set OPENAI_API_KEY (and optionally C2A_MODEL, "
            "default gpt-4o). Drill, select, cases, log and stats work without one.")


def model():
    return os.environ.get("C2A_MODEL") or DEFAULT_MODEL


def chat(messages, temperature=0.2, max_tokens=1500, json_mode=False):
    """messages: list of {"role", "content"}. Returns the reply text."""
    require()
    m = model()
    body = {"model": m, "messages": messages}
    if m.startswith(REASONING_PREFIXES):   # these reject temperature and rename the cap
        body["max_completion_tokens"] = max_tokens * 4
    else:
        body["temperature"] = temperature
        body["max_tokens"] = max_tokens
    if json_mode:
        body["response_format"] = {"type": "json_object"}
    base = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    req = urllib.request.Request(
        f"{base}/chat/completions", data=json.dumps(body).encode(),
        headers={"Authorization": f"Bearer {os.environ['OPENAI_API_KEY'].strip()}",
                 "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            data = json.load(r)
    except urllib.error.HTTPError as e:
        raise LLMError(f"OpenAI request failed: {e.code} {e.read()[:300]!r}") from e
    except urllib.error.URLError as e:
        raise LLMError(f"OpenAI request failed: {e.reason}") from e
    choices = data.get("choices") or []
    text = ((choices[0].get("message") or {}).get("content") or "") if choices else ""
    if not text.strip():
        raise LLMError(f"OpenAI returned no content: {str(data)[:300]}")
    return text


def chat_json(messages, **kw):
    """Like chat(), but parse the reply as one JSON object."""
    text = chat(messages, json_mode=True, **kw)
    m = re.search(r"\{.*\}", text, re.S)
    try:
        return json.loads(m.group(0) if m else text)
    except json.JSONDecodeError as e:
        raise LLMError(f"LLM did not return valid JSON: {text[:300]}") from e
