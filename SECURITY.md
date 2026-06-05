# Security

PromptDB is built to be safe to point at a real database and safe to expose as a public demo.
This document explains the guarantees and the threat model.

## Read-only by design

A generated query passes three independent gates before it touches data:

1. **Statement validation** — only a single `SELECT` or `WITH` statement is allowed. Stacked
   statements and any mutation keyword (`INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`, `CREATE`,
   `REPLACE`, `TRUNCATE`, `GRANT`, …) are rejected before execution.
2. **Read-only connection** — SQLite is opened in `mode=ro`; a `DROP`/`UPDATE` raises at the
   driver even if validation were bypassed. For other engines, run the connector as a read-only
   database user (see [docs/CONNECTOR.md](docs/CONNECTOR.md)).
3. **Resource limits** — a statement timeout and a row cap bound how much a single query can do.

The agent has no tool that can modify data. The worst a prompt-injected or buggy query can do is
read within the limits above.

## Data residency

For your own database, the agent runs **where the data lives** (the local connector), not in the
cloud. Only the **schema** and **your own query results** are sent to the model. Database
credentials and full table contents never leave your machine. PromptDB does not ask you to upload
a database file or paste a production connection string into a hosted website, and the public demo
server never receives your data.

## API keys

- **Demo path** uses the server's own key, protected by a per-IP free-query cap and a global daily
  spend ceiling. When either is reached, the demo path is disabled until reset.
- **Bring-your-own-key** requests carry the key only in the request body. It is constructed into
  the model client and is **never written to graph state, logs, or LangSmith traces**. It is not
  persisted server-side.
- Never commit a key. `.env` is gitignored; deploy secrets live in the host's environment.

## Reporting a vulnerability

Open a private report via GitHub Security Advisories on the repository, or email the maintainer.
Please do not file public issues for security problems. Expect an initial response within a few days.
