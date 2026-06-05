"""Cost protection for the public demo path (queries that run on the server's own key).

Two backstops, reset daily:
  - per-IP free-query count (default 5) — the visitor's free trial before they must BYO key
  - global daily spend ceiling (USD) — caps total exposure on the server key across all visitors

BYO-key requests skip all of this (the visitor pays) and are governed only by the upstream
per-IP rate limit. State is a single JSON file so counts survive restarts — correct on one
persistent instance (Render); a multi-instance/serverless host would swap this for a shared store.
"""

import json
import os
import threading
from datetime import date
from pathlib import Path

STATE_FILE = Path(os.environ.get("PROMPTDB_USAGE_FILE", ".promptdb_usage.json"))
DAILY_SPEND_CAP = float(os.environ.get("PROMPTDB_DAILY_SPEND_USD", "1.0"))
DEMO_QUERIES_PER_IP = int(os.environ.get("PROMPTDB_DEMO_QUERIES_PER_IP", "5"))

_lock = threading.Lock()


def _load() -> dict:
    today = date.today().isoformat()
    try:
        d = json.loads(STATE_FILE.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        d = {}
    if d.get("date") != today:  # new day → reset
        d = {"date": today, "spend": 0.0, "ips": {}}
    d.setdefault("spend", 0.0)
    d.setdefault("ips", {})
    return d


def _save(d: dict) -> None:
    STATE_FILE.write_text(json.dumps(d))


def check_demo_allowed(ip: str) -> tuple[bool, str]:
    """May this IP run a query on the server key right now? Call before running."""
    with _lock:
        d = _load()
        if d["spend"] >= DAILY_SPEND_CAP:
            return False, "The demo's daily budget is used up. Add your own API key to keep going."
        if d["ips"].get(ip, 0) >= DEMO_QUERIES_PER_IP:
            return False, (
                f"You've used your {DEMO_QUERIES_PER_IP} free demo queries. "
                "Add your own API key (Anthropic, OpenAI, or local Ollama) to keep going."
            )
        return True, ""


def record_demo_usage(ip: str, cost: float) -> None:
    """Record a completed demo query's cost + increment the IP's count."""
    with _lock:
        d = _load()
        d["spend"] += float(cost or 0.0)
        d["ips"][ip] = d["ips"].get(ip, 0) + 1
        _save(d)


def demo_status(ip: str) -> dict:
    """Snapshot for the UI: how much of the budget / free quota remains."""
    with _lock:
        d = _load()
        used = d["ips"].get(ip, 0)
        return {
            "daily_spend_usd": round(d["spend"], 4),
            "daily_cap_usd": DAILY_SPEND_CAP,
            "ip_queries_used": used,
            "ip_queries_limit": DEMO_QUERIES_PER_IP,
            "free_queries_left": max(0, DEMO_QUERIES_PER_IP - used),
            "demo_open": d["spend"] < DAILY_SPEND_CAP,
        }
