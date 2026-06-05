"""Call the PromptDB agent programmatically.

Run from the repo root (with chinook.db present and ANTHROPIC_API_KEY set):
    python examples/quickstart.py
"""

from promptdb.agent.graph import build_graph


def ask(question: str) -> None:
    result = build_graph().invoke({"question": question})
    print(f"Q: {question}")
    print(f"SQL: {result.get('sql')}")
    print(f"Answer: {result.get('answer')}")
    print(f"Cost: ${result.get('cost_usd', 0):.5f}\n")


if __name__ == "__main__":
    ask("which 3 genres have the most tracks?")
    ask("how many customers are from Canada?")
