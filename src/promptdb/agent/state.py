"""Typed graph state for the PromptDB agent."""

from typing import Optional, TypedDict


class AgentState(TypedDict, total=False):
    question: str          # user's natural-language question
    schema: str            # introspected schema text
    sql: str               # generated SQL
    columns: list[str]     # result column names
    rows: list[list]       # result rows
    error: Optional[str]   # execution error, if any
    answer: str            # final natural-language answer
