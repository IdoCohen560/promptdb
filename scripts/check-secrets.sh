#!/usr/bin/env bash
# Pre-commit secret guard. Blocks committing a real .env or any known key pattern.
# Install: ln -sf ../../scripts/check-secrets.sh .git/hooks/pre-commit
set -euo pipefail

staged=$(git diff --cached --name-only --diff-filter=ACM || true)

# 1) Never commit a real .env (only .env.example is allowed)
if printf '%s\n' "$staged" | grep -E '(^|/)\.env($|\.)' | grep -vq '\.env\.example'; then
  echo "BLOCKED: attempting to commit a .env file. Secrets must never be committed."
  exit 1
fi

# 2) Scan staged additions for known secret patterns
patterns='sk-ant-[A-Za-z0-9_-]{20,}|sk-[A-Za-z0-9]{32,}|AKIA[0-9A-Z]{16}|rnd_[A-Za-z0-9]{20,}|re_[A-Za-z0-9]{20,}|ghp_[A-Za-z0-9]{36}|AIza[0-9A-Za-z_-]{35}|-----BEGIN [A-Z ]*PRIVATE KEY-----'
if git diff --cached -U0 --diff-filter=ACM | grep -E '^\+' | grep -EIn "$patterns"; then
  echo "BLOCKED: a secret-like string is staged (shown above). Remove it before committing."
  exit 1
fi

exit 0
