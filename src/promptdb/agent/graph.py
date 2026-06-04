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

from promptdb.agent.guardrails import validate_sql
from promptdb.agent.state import AgentState
from promptdb.db.connection import get_engine, get_schema_text, run_select
from promptdb.observability.cost import cost_usd

load_dotenv()

MAX_ATTEMPTS = 3


@lru_cache(maxsize=1)
def get_llm() -> ChatAnthropic:
    model = os.environ.get("PROMPTDB_MODEL", "claude-sonnet-4-6")
    return ChatAnthropic(model=model, temperature=0, max_tokens=1024)


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


def schema_retriever(state: AgentState) -> dict:
    return {"schema": get_schema_text(get_engine())}


def sql_writer(state: AgentState) -> dict:
    llm = get_llm().with_structured_output(SQLQuery, include_raw=True)
    prompt = build_sql_prompt(
        state["schema"], state["question"], state.get("sql"), state.get("error")
    )
    out = llm.invoke(prompt)
    usage = getattr(out["raw"], "usage_metadata", None) or {}
    return {
        "sql": out["parsed"].sql,
        "attempts": state.get("attempts", 0) + 1,
        "error": None,
        "cost_usd": state.get("cost_usd", 0.0) + cost_usd(usage, get_llm().model),
    }


def sql_validator(state: AgentState) -> dict:
    return {"error": validate_sql(state["sql"])}


def sql_executor(state: AgentState) -> dict:
    try:
        cols, rows = run_select(get_engine(), state["sql"])
        return {"columns": cols, "rows": rows, "error": None}
    except Exception as exc:  # noqa: BLE001 — surface any DB error to the agent for retry
        return {"error": str(exc)}


def _render(columns: list[str], rows: list[list], limit: int = 30) -> str:
    head = " | ".join(columns)
    body = "\n".join(" | ".join(str(v) for v in r) for r in rows[:limit])
    return f"{head}\n{body}"


def answer_synthesizer(state: AgentState) -> dict:
    if state.get("error"):
        return {
            "answer": f"Could not answer after {state.get('attempts', 0)} attempts. "
            f"Last error: {state['error']}"
        }
    preview = _render(state.get("columns", []), state.get("rows", []))
    prompt = (
        f"Question: {state['question']}\n"
        f"SQL used: {state['sql']}\n"
        f"Query result:\n{preview}\n\n"
        "Answer the question in 1-3 sentences using ONLY the result above."
    )
    resp = get_llm().invoke(prompt)
    usage = getattr(resp, "usage_metadata", None) or {}
    answer = resp.content if isinstance(resp.content, str) else str(resp.content)
    return {"answer": answer, "cost_usd": state.get("cost_usd", 0.0) + cost_usd(usage, get_llm().model)}


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
