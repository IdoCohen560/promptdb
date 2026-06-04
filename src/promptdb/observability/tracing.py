"""LangSmith tracing. LangChain auto-traces to LangSmith when LANGSMITH_TRACING=true and
LANGSMITH_API_KEY are set — no code change needed. These helpers just report status."""

import os


def tracing_enabled() -> bool:
    return os.environ.get("LANGSMITH_TRACING", "").lower() == "true" and bool(
        os.environ.get("LANGSMITH_API_KEY")
    )


def status() -> str:
    if tracing_enabled():
        return f"LangSmith tracing ON (project={os.environ.get('LANGSMITH_PROJECT', 'default')})"
    return "LangSmith tracing off — set LANGSMITH_API_KEY and LANGSMITH_TRACING=true to enable"
