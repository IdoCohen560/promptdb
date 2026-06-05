"""P8g verification: OpenAI-compatible provider router (no network, no keys)."""

import os

from promptdb.agent.providers import PRESETS, make_llm, model_for


def test_openai_compatible_clients():
    llm = make_llm("openrouter", "meta-llama/llama-3.3-70b-instruct", api_key="sk-x")
    assert type(llm).__name__ == "ChatOpenAI"
    assert str(llm.openai_api_base) == PRESETS["openrouter"]
    assert llm.model_name == "meta-llama/llama-3.3-70b-instruct"


def test_custom_base_url():
    llm = make_llm(None, "any-model", api_key="k", base_url="https://my.host/v1")
    assert type(llm).__name__ == "ChatOpenAI"
    assert str(llm.openai_api_base) == "https://my.host/v1"


def test_demo_default_reads_env(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
    llm = make_llm()  # no provider → native Anthropic demo default
    assert type(llm).__name__ == "ChatAnthropic"


def test_model_for_defaults():
    assert model_for("anthropic", None).startswith("claude")
    assert model_for("openrouter", None)  # non-empty
    assert model_for("openai", "gpt-4o") == "gpt-4o"
