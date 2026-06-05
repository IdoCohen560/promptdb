"""P2 verification: read-only guardrails + the self-correction loop (no LLM required)."""

from langgraph.graph import END, START, StateGraph

from promptdb.agent import graph as G
from promptdb.agent.guardrails import validate_credentials, validate_sql, validate_table_access
from promptdb.agent.state import AgentState


def test_credential_guard():
    cols, stars = {"password_hash"}, {"users"}
    assert validate_credentials("SELECT id, email FROM users", cols, stars) is None       # non-credential cols ok
    assert validate_credentials("SELECT password_hash FROM users", cols, stars) is not None
    assert validate_credentials("SELECT u.password_hash FROM users u", cols, stars) is not None
    assert validate_credentials("SELECT * FROM users", cols, stars) is not None            # star could leak it
    assert validate_credentials("SELECT * FROM news_articles", cols, stars) is None        # star fine elsewhere
    assert validate_credentials("SELECT COUNT(*) FROM users", cols, stars) is None          # count(*) is not a wildcard
    assert validate_credentials("SELECT 1", set(), set()) is None


def test_denied_table_access_blocked():
    denied = {"users", "user_locations"}
    assert validate_table_access("SELECT * FROM zone_risk_cache", denied) is None
    assert validate_table_access("SELECT email FROM users", denied) is not None
    assert validate_table_access("SELECT z.id FROM zone z JOIN user_locations ul ON z.id=ul.zone_id", denied) is not None
    # case-insensitive + schema-qualified
    assert validate_table_access("SELECT * FROM public.USERS", denied) is not None
    # no denylist → allow anything
    assert validate_table_access("SELECT * FROM users", set()) is None


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
