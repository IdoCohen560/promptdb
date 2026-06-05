"""Typed graph state for the PromptDB agent."""

from typing import Optional, TypedDict


class AgentState(TypedDict, total=False):
    question: str          # user's natural-language question
    schema: str            # introspected schema text
    sql: str               # generated SQL
    attempts: int          # number of sql_writer attempts so far
    columns: list[str]     # result column names
    rows: list[list]       # result rows
    error: Optional[str]   # validation or execution error, if any
    hint: dict             # on an empty result, the filtered column's real values (for a 'did you mean')
    answer: str            # final natural-language answer
    cost_usd: float        # cumulative LLM cost for this query
