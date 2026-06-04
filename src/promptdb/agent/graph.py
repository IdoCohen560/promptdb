"""LangGraph state machine for the P1 happy path:
schema_retriever -> sql_writer -> sql_executor -> answer_synthesizer.

Self-correction loop, validator, and critic land in P2.
"""

import os
from functools import lru_cache

from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel, Field

from promptdb.agent.state import AgentState
from promptdb.db.connection import get_engine, get_schema_text, run_select

load_dotenv()


@lru_cache(maxsize=1)
def get_llm() -> ChatAnthropic:
    model = os.environ.get("PROMPTDB_MODEL", "claude-sonnet-4-6")
    return ChatAnthropic(model=model, temperature=0, max_tokens=1024)


class SQLQuery(BaseModel):
    """A single read-only SQLite SELECT query."""

    sql: str = Field(description="One read-only SQLite SELECT query that answers the question.")


def schema_retriever(state: AgentState) -> dict:
    return {"schema": get_schema_text(get_engine())}


def sql_writer(state: AgentState) -> dict:
    llm = get_llm().with_structured_output(SQLQuery)
    prompt = (
        "You are a SQLite expert. Using ONLY the schema below, write a single "
        "read-only SELECT query (SQLite dialect) that answers the question. "
        "Do not write anything but a SELECT.\n\n"
        f"Schema:\n{state['schema']}\n\n"
        f"Question: {state['question']}"
    )
    out = llm.invoke(prompt)
    return {"sql": out.sql}


def sql_executor(state: AgentState) -> dict:
    try:
        cols, rows = run_select(get_engine(), state["sql"])
        return {"columns": cols, "rows": rows, "error": None}
    except Exception as exc:  # noqa: BLE001 — surface any DB error to the agent
        return {"error": str(exc)}


def _render(columns: list[str], rows: list[list], limit: int = 30) -> str:
    head = " | ".join(columns)
    body = "\n".join(" | ".join(str(v) for v in r) for r in rows[:limit])
    return f"{head}\n{body}"


def answer_synthesizer(state: AgentState) -> dict:
    if state.get("error"):
        return {"answer": f"Could not answer — the query failed: {state['error']}"}
    preview = _render(state.get("columns", []), state.get("rows", []))
    prompt = (
        f"Question: {state['question']}\n"
        f"SQL used: {state['sql']}\n"
        f"Query result:\n{preview}\n\n"
        "Answer the question in 1-3 sentences using ONLY the result above."
    )
    resp = get_llm().invoke(prompt)
    return {"answer": resp.content if isinstance(resp.content, str) else str(resp.content)}


@lru_cache(maxsize=1)
def build_graph():
    g = StateGraph(AgentState)
    g.add_node("schema_retriever", schema_retriever)
    g.add_node("sql_writer", sql_writer)
    g.add_node("sql_executor", sql_executor)
    g.add_node("answer_synthesizer", answer_synthesizer)
    g.add_edge(START, "schema_retriever")
    g.add_edge("schema_retriever", "sql_writer")
    g.add_edge("sql_writer", "sql_executor")
    g.add_edge("sql_executor", "answer_synthesizer")
    g.add_edge("answer_synthesizer", END)
    return g.compile()
