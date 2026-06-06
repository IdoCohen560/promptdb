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
read within the limits above. On the public demo, a 4th gate applies: a **table allowlist** and a
**credential-column guard** (`agent/guardrails.validate_credentials`) keep columns like `password_hash`
out of any result, and block `SELECT *` on tables that hold one so a wildcard can't leak it.

## Connecting a database

Two paths, by where the data lives:

- **Private / local DB** (laptop, VPC) — run the local connector; the agent runs **where the data lives**.
  Only the schema and your own results reach the model; credentials and rows never leave your machine.
  PromptDB never asks you to upload a database file.
- **Cloud-reachable DB** — you may paste a **read-only** Postgres/MySQL connection string into the hosted
  demo. The server validates it and rejects any host that resolves to a private, loopback, link-local, or
  reserved/metadata address (**SSRF protection**, `api/remote_db.py`); unreachable hosts fail fast. Use a
  read-only database user — queries are SELECT-only, but a read-only login is the real guarantee. The
  string is used per request and not stored. Model `base_url`s for custom providers are guarded the same way.

## API keys

- **Demo path** uses the server's own key, protected by a **per-browser** free-query cap (a client id sent
  as `X-Client-Id`, so users behind a shared IP each get their own quota) and a global daily spend ceiling.
  Behind a proxy, the API trusts forwarded headers so rate limiting sees the real client IP.
- **Bring-your-own-key** requests carry the key only in the request body. It is constructed into the model
  client and is **never written to graph state, logs, or LangSmith traces**, and is not persisted server-side.
- Never commit a key. `.env` is gitignored; deploy secrets live in the host's environment.

## Reporting a vulnerability

Open a private report via GitHub Security Advisories on the repository, or email the maintainer.
Please do not file public issues for security problems. Expect an initial response within a few days.
