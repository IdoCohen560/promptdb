"""LangGraph state machine for PromptDB.

Flow: schema_retriever -> sql_writer -> sql_validator -> sql_executor -> answer_synthesizer,
with a self-correction loop: a validation or execution error routes back to sql_writer
(with the error in context) until it succeeds or MAX_ATTEMPTS is reached.
"""

import os
from functools import lru_cache

from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel, Field

from promptdb.agent.guardrails import validate_sql, validate_table_access
from promptdb.agent.state import AgentState
from promptdb.db.connection import get_engine, get_schema_text, run_select
from promptdb.observability.cost import cost_usd

load_dotenv()

MAX_ATTEMPTS = 3


@lru_cache(maxsize=1)
def get_llm() -> ChatAnthropic:
    model = os.environ.get("PROMPTDB_MODEL", "claude-sonnet-4-6")
    return ChatAnthropic(model=model, temperature=0, max_tokens=1024)


def _engine_for(config):
    """Resolve the database engine: a per-request engine injected via config (a connected
    user database), else the server's default engine."""
    cfg = (config or {}).get("configurable", {}) if config else {}
    return cfg.get("engine") or get_engine()


def _llm_for(config) -> tuple[object, str]:
    """Resolve the model for this run: a per-request client injected via
    `config.configurable` (BYO key/provider), else the default Anthropic client.
    Returns (llm, model_name) — model_name drives cost lookup."""
    cfg = (config or {}).get("configurable", {}) if config else {}
    llm = cfg.get("llm")
    if llm is not None:
        return llm, cfg.get("model_name", "unknown")
    default = get_llm()
    return default, default.model


def _unwrap_structured(out) -> tuple[object, dict]:
    """Normalize `.with_structured_output(..., include_raw=True)` across providers.
    Returns (parsed_model_or_None, usage_metadata_dict)."""
    if isinstance(out, dict):  # include_raw=True path (Anthropic, OpenAI)
        parsed, raw = out.get("parsed"), out.get("raw")
        usage = getattr(raw, "usage_metadata", None) or {} if raw is not None else {}
        return parsed, usage
    return out, getattr(out, "usage_metadata", None) or {}  # provider returned the model directly


class SQLQuery(BaseModel):
    """A single read-only SQLite SELECT query."""

    sql: str = Field(description="One read-only SQLite SELECT query that answers the question.")


def build_sql_prompt(
    schema: str, question: str, prev_sql: str | None = None, error: str | None = None
) -> str:
    """Shared SQL-generation prompt — used by the agent AND the eval harness so evals
    measure the real agent. Requests minimal projection (only the columns asked for)."""
    prompt = (
        "You are a SQLite expert. Using ONLY the schema below, write a single "
        "read-only SELECT query (SQLite dialect) that answers the question. "
        "Do not write anything but a SELECT.\n\n"
        f"Schema:\n{schema}\n\n"
        f"Question: {question}"
    )
    if error and prev_sql:
        prompt += (
            f"\n\nYour previous attempt failed.\n"
            f"Previous SQL:\n{prev_sql}\n"
            f"Error:\n{error}\n"
            "Write a corrected query."
        )
    return prompt


def schema_retriever(state: AgentState, config=None) -> dict:
    return {"schema": get_schema_text(_engine_for(config))}


def sql_writer(state: AgentState, config=None) -> dict:
    llm, model_name = _llm_for(config)
    structured = llm.with_structured_output(SQLQuery, include_raw=True)
    prompt = build_sql_prompt(
        state["schema"], state["question"], state.get("sql"), state.get("error")
    )
    parsed, usage = _unwrap_structured(structured.invoke(prompt))
    attempts = state.get("attempts", 0) + 1
    cost = state.get("cost_usd", 0.0) + cost_usd(usage, model_name)
    if parsed is None:  # weaker models may fail to produce valid structured output
        return {"attempts": attempts, "error": "model returned no valid SQL", "cost_usd": cost}
    return {"sql": parsed.sql, "attempts": attempts, "error": None, "cost_usd": cost}


def sql_validator(state: AgentState, config=None) -> dict:
    err = validate_sql(state["sql"])
    if not err:
        denied = ((config or {}).get("configurable", {}) if config else {}).get("denied_tables")
        if denied:
            err = validate_table_access(state["sql"], denied)
    return {"error": err}


def sql_executor(state: AgentState, config=None) -> dict:
    try:
        cols, rows = run_select(_engine_for(config), state["sql"])
        return {"columns": cols, "rows": rows, "error": None}
    except Exception as exc:  # noqa: BLE001 — surface any DB error to the agent for retry
        return {"error": str(exc)}


def _render(columns: list[str], rows: list[list], limit: int = 30) -> str:
    head = " | ".join(columns)
    body = "\n".join(" | ".join(str(v) for v in r) for r in rows[:limit])
    return f"{head}\n{body}"


def answer_synthesizer(state: AgentState, config=None) -> dict:
    if state.get("error"):
        return {
            "answer": f"Could not answer after {state.get('attempts', 0)} attempts. "
            f"Last error: {state['error']}"
        }
    llm, model_name = _llm_for(config)
    preview = _render(state.get("columns", []), state.get("rows", []))
    prompt = (
        f"Question: {state['question']}\n"
        f"SQL used: {state['sql']}\n"
        f"Query result:\n{preview}\n\n"
        "Answer the question in 1-3 sentences using ONLY the result above."
    )
    resp = llm.invoke(prompt)
    usage = getattr(resp, "usage_metadata", None) or {}
    answer = resp.content if isinstance(resp.content, str) else str(resp.content)
    return {"answer": answer, "cost_usd": state.get("cost_usd", 0.0) + cost_usd(usage, model_name)}


def route_after_validate(state: AgentState) -> str:
    if not state.get("error"):
        return "sql_executor"
    return "sql_writer" if state.get("attempts", 0) < MAX_ATTEMPTS else "answer_synthesizer"


def route_after_execute(state: AgentState) -> str:
    if not state.get("error"):
        return "answer_synthesizer"
    return "sql_writer" if state.get("attempts", 0) < MAX_ATTEMPTS else "answer_synthesizer"


@lru_cache(maxsize=1)
def build_graph():
    g = StateGraph(AgentState)
    g.add_node("schema_retriever", schema_retriever)
    g.add_node("sql_writer", sql_writer)
    g.add_node("sql_validator", sql_validator)
    g.add_node("sql_executor", sql_executor)
    g.add_node("answer_synthesizer", answer_synthesizer)
    g.add_edge(START, "schema_retriever")
    g.add_edge("schema_retriever", "sql_writer")
    g.add_edge("sql_writer", "sql_validator")
    g.add_conditional_edges(
        "sql_validator", route_after_validate, ["sql_executor", "sql_writer", "answer_synthesizer"]
    )
    g.add_conditional_edges(
        "sql_executor", route_after_execute, ["sql_writer", "answer_synthesizer"]
    )
    g.add_edge("answer_synthesizer", END)
    return g.compile()
