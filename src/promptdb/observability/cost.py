"""Token cost estimation. Prices are USD per million tokens (Anthropic list prices;
override via PROMPTDB_PRICE_IN / PROMPTDB_PRICE_OUT)."""

import os

# (input, output) USD per million tokens. List prices — adjust if they change.
PRICES = {
    "claude-sonnet-4-6": (3.0, 15.0),
    "claude-haiku-4-5": (1.0, 5.0),
    "claude-opus-4": (15.0, 75.0),
    "gpt-4o-mini": (0.15, 0.6),
    "gpt-4o": (2.5, 10.0),
    "gpt-4.1-mini": (0.4, 1.6),
    "gpt-4.1": (2.0, 8.0),
}

# Locally-served models (Ollama) cost nothing — match on common family names.
LOCAL_PREFIXES = ("gemma", "llama", "mistral", "qwen", "phi", "deepseek", "ollama/")


def price_for(model: str) -> tuple[float, float]:
    m = model.lower()
    if any(m.startswith(p) for p in LOCAL_PREFIXES):
        return (0.0, 0.0)
    for key, p in PRICES.items():
        if model.startswith(key):
            return p
    return (
        float(os.environ.get("PROMPTDB_PRICE_IN", "3.0")),
        float(os.environ.get("PROMPTDB_PRICE_OUT", "15.0")),
    )


def cost_usd(usage: dict, model: str) -> float:
    """USD cost from a usage_metadata dict with input_tokens / output_tokens."""
    pin, pout = price_for(model)
    return usage.get("input_tokens", 0) / 1e6 * pin + usage.get("output_tokens", 0) / 1e6 * pout
