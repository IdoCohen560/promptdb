"""P2 verification: read-only guardrails + the self-correction loop (no LLM required)."""

from langgraph.graph import END, START, StateGraph

from promptdb.agent import graph as G
from promptdb.agent.guardrails import validate_sql
from promptdb.agent.state import AgentState


def test_validator_allows_select_and_with():
    assert validate_sql("SELECT * FROM Artist") is None
    assert validate_sql("WITH x AS (SELECT 1) SELECT * FROM x") is None
    # \b boundary: a column like last_update must not trip the mutation scan
    assert validate_sql("SELECT last_update FROM t") is None


def test_validator_blocks_mutations_and_stacking():
    assert validate_sql("DELETE FROM Customer") is not None
    assert validate_sql("DROP TABLE Artist") is not None
    assert validate_sql("UPDATE Track SET Name='x'") is not None
    assert validate_sql("INSERT INTO Artist VALUES (1,'x')") is not None
    assert validate_sql("SELECT 1; DROP TABLE Artist") is not None  # stacked statements
    assert validate_sql("") is not None


def test_self_correction_recovers_from_bad_query():
    """First generated query errors; the loop feeds the error back and the retry succeeds."""
    calls = {"n": 0}

    def fake_writer(state):
        calls["n"] += 1
        sql = "SELECT * FROM NoSuchTable" if calls["n"] == 1 else "SELECT Name FROM Artist LIMIT 3"
        return {"sql": sql, "attempts": state.get("attempts", 0) + 1, "error": None}

    def route_validate(state):
        if not state.get("error"):
            return "sql_executor"
        return "sql_writer" if state.get("attempts", 0) < G.MAX_ATTEMPTS else END

    def route_execute(state):
        if not state.get("error"):
            return END
        return "sql_writer" if state.get("attempts", 0) < G.MAX_ATTEMPTS else END

    g = StateGraph(AgentState)
    g.add_node("sql_writer", fake_writer)
    g.add_node("sql_validator", G.sql_validator)
    g.add_node("sql_executor", G.sql_executor)
    g.add_edge(START, "sql_writer")
    g.add_edge("sql_writer", "sql_validator")
    g.add_conditional_edges("sql_validator", route_validate, ["sql_executor", "sql_writer", END])
    g.add_conditional_edges("sql_executor", route_execute, ["sql_writer", END])
    compiled = g.compile()

    result = compiled.invoke({"question": "names of artists"})

    assert calls["n"] == 2, "writer should have been called twice (fail then recover)"
    assert result.get("attempts") == 2
    assert result.get("rows"), "recovered query should return rows"
    assert result.get("error") is None
