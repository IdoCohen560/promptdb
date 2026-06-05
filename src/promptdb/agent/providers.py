"""Multi-provider LLM router.

Any OpenAI-compatible endpoint plugs in via base_url + api_key + model — that is how we reach
"all models, including open source": OpenRouter (one key, hundreds of models), OpenAI, vLLM,
llama.cpp, and local Ollama all expose an OpenAI-style /v1 API. Native Anthropic is kept as the
demo default (the server key). Provider packages are imported lazily.
"""

import json
import os
import urllib.request

DEFAULT_PROVIDER = "anthropic"
ANTHROPIC_DEFAULT = "claude-sonnet-4-6"
OPENAI_COMPAT_DEFAULT = "gpt-4o-mini"

# OpenAI-compatible base URLs by preset name. "custom" supplies its own base_url.
PRESETS = {
    "openrouter": "https://openrouter.ai/api/v1",
    "openai": "https://api.openai.com/v1",
    "ollama": "http://localhost:11434/v1",  # local only — reachable from the connector, not a hosted server
}


def model_for(provider: str | None, model: str | None) -> str:
    if model:
        return model
    return ANTHROPIC_DEFAULT if (provider or "").lower() == "anthropic" else OPENAI_COMPAT_DEFAULT


def make_llm(
    provider: str | None = None,
    model: str | None = None,
    api_key: str | None = None,
    base_url: str | None = None,
):
    """Build a chat model. base_url (or a non-anthropic preset) → OpenAI-compatible client;
    otherwise native Anthropic. The api_key lives only inside the returned client."""
    provider = (provider or os.environ.get("PROMPTDB_PROVIDER") or DEFAULT_PROVIDER).lower()
    resolved_base = base_url or PRESETS.get(provider)

    if provider == "anthropic" and not base_url:
        from langchain_anthropic import ChatAnthropic

        key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        kw = {"api_key": key} if key else {}  # else let ChatAnthropic read the env itself
        return ChatAnthropic(model=model or ANTHROPIC_DEFAULT, temperature=0, max_tokens=1024, **kw)
    if resolved_base:
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=model or OPENAI_COMPAT_DEFAULT, temperature=0, max_tokens=1024,
            api_key=api_key or "none", base_url=resolved_base,
        )
    raise ValueError(f"Unknown provider '{provider}' and no base_url given")


def list_models(base_url: str, api_key: str | None = None, timeout: float = 8.0) -> list[str]:
    """Fetch the model catalog from an OpenAI-compatible endpoint's /models route."""
    url = base_url.rstrip("/") + "/models"
    req = urllib.request.Request(url)
    if api_key:
        req.add_header("Authorization", f"Bearer {api_key}")
    with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310 — host is SSRF-checked upstream
        data = json.loads(resp.read())
    items = data.get("data", []) if isinstance(data, dict) else data
    return sorted({m["id"] for m in items if isinstance(m, dict) and m.get("id")})
