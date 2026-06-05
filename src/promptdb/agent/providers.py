"""Multi-provider LLM router for bring-your-own-key support.

The default (demo) path uses Anthropic via the server's own key. A request may instead
supply its own provider + model + key, which is constructed here and injected into the
graph via LangGraph's `config.configurable` — so the key never enters graph state or traces.

Provider packages are imported lazily: the base install only needs langchain-anthropic;
`langchain-openai` / `langchain-ollama` are required only if those providers are actually used.
"""

import os

DEFAULT_PROVIDER = "anthropic"
DEFAULT_MODELS = {
    "anthropic": "claude-sonnet-4-6",
    "openai": "gpt-4o-mini",
    "ollama": "gemma2",
}
SUPPORTED = tuple(DEFAULT_MODELS)


def model_for(provider: str, model: str | None) -> str:
    return model or DEFAULT_MODELS.get(provider, DEFAULT_MODELS[DEFAULT_PROVIDER])


def make_llm(provider: str | None = None, model: str | None = None, api_key: str | None = None):
    """Build a LangChain chat model for the given provider. Falls back to env defaults.

    Returns the model client; the caller pairs it with `model_for(...)` for cost lookup.
    The api_key lives only inside the returned client object, never in graph state.
    """
    provider = (provider or os.environ.get("PROMPTDB_PROVIDER") or DEFAULT_PROVIDER).lower()
    model = model_for(provider, model)

    if provider == "anthropic":
        from langchain_anthropic import ChatAnthropic

        return ChatAnthropic(
            model=model, temperature=0, max_tokens=1024,
            api_key=api_key or os.environ.get("ANTHROPIC_API_KEY"),
        )
    if provider == "openai":
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=model, temperature=0, max_tokens=1024,
            api_key=api_key or os.environ.get("OPENAI_API_KEY"),
        )
    if provider == "ollama":
        from langchain_ollama import ChatOllama

        return ChatOllama(
            model=model, temperature=0,
            base_url=os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434"),
        )
    raise ValueError(f"Unknown provider '{provider}'. Supported: {', '.join(SUPPORTED)}")
