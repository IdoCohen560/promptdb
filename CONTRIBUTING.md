# Contributing

Thanks for your interest in PromptDB. This is a focused project; small, well-tested changes are
easiest to land.

## Development setup

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev,web,providers]"
cp .env.example .env                 # add ANTHROPIC_API_KEY
curl -sSL -o chinook.db "https://github.com/lerocha/chinook-database/raw/master/ChinookDatabase/DataSources/Chinook_Sqlite.sqlite"
pytest -q                            # should be green before you start
```

Frontend (optional):

```bash
cd frontend && npm install && npm run dev    # expects the API on http://localhost:8000
```

## Workflow

1. Branch from `master`.
2. Make the change. Keep modules under ~500 lines and match the surrounding style.
3. Add or update tests. Unit tests must not require network or an API key — mock the model
   (see `tests/test_guardrails.py` and `tests/test_limits.py`).
4. Run `pytest -q` and `ruff check .`. For the UI, `npm run build` must pass.
5. Open a PR with a clear description of what changed and why.

## What CI checks

- `pytest` runs on every push (`.github/workflows/test.yml`).
- The paid eval suite (`evals.yml`) runs on manual dispatch only, so PRs never spend tokens.

## Scope

PromptDB stays read-only and single-purpose. Changes that add write access to a database, or that
send user data to a third party beyond the chosen model provider, are out of scope. New SQL
dialects, providers, and evals are welcome.

By contributing you agree your contributions are licensed under the [MIT License](LICENSE).
