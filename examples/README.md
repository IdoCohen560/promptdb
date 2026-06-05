# Examples

Runnable snippets. Install first: `pip install -e ".[providers]"` (from the repo root) and set
`ANTHROPIC_API_KEY` (or use `PROMPTDB_PROVIDER=ollama` for a local, free model).

| File | What it shows |
|---|---|
| [`quickstart.py`](quickstart.py) | Call the agent programmatically and read back SQL + answer + cost |
| [`byo_database.py`](byo_database.py) | Build a throwaway database and query it read-only (the own-DB path) |
| [`claude_desktop_config.json`](claude_desktop_config.json) | Wire the `promptdb-mcp` connector into Claude Desktop |

```bash
python examples/quickstart.py
python examples/byo_database.py
```
