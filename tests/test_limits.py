"""P8b verification: demo spend/usage caps (no LLM, no network)."""

import json

import pytest

from promptdb.api import limits


@pytest.fixture
def caps(tmp_path, monkeypatch):
    """Isolated state file + small caps so the limits are easy to exercise."""
    monkeypatch.setattr(limits, "STATE_FILE", tmp_path / "usage.json")
    monkeypatch.setattr(limits, "DEMO_QUERIES_PER_IP", 3)
    monkeypatch.setattr(limits, "DAILY_SPEND_CAP", 0.10)
    return limits


def test_free_queries_then_blocked(caps):
    ip = "1.2.3.4"
    for i in range(3):
        ok, _ = caps.check_demo_allowed(ip)
        assert ok, f"query {i} should be free"
        caps.record_demo_usage(ip, 0.001)
    ok, msg = caps.check_demo_allowed(ip)
    assert not ok and "free demo queries" in msg


def test_per_ip_isolated(caps):
    for _ in range(3):
        caps.record_demo_usage("a", 0.001)
    assert not caps.check_demo_allowed("a")[0]      # a is exhausted
    assert caps.check_demo_allowed("b")[0]          # b is unaffected


def test_global_daily_spend_cap(caps):
    caps.record_demo_usage("9.9.9.9", 0.20)         # one pricey query blows the $0.10 cap
    ok, msg = caps.check_demo_allowed("someone-else")
    assert not ok and "budget" in msg.lower()       # cap is global, not per-IP


def test_daily_reset(caps):
    caps.STATE_FILE.write_text(json.dumps({"date": "2000-01-01", "spend": 99.0, "ips": {"x": 100}}))
    assert caps.check_demo_allowed("x")[0]           # stale day resets on load
    assert caps.demo_status("x")["daily_spend_usd"] == 0.0


def test_status_shape(caps):
    s = caps.demo_status("z")
    assert s["free_queries_left"] == 3
    assert s["demo_open"] is True
    assert s["ip_queries_limit"] == 3
