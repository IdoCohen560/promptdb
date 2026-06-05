"""P8f verification: SSRF guards on user-supplied connection strings (no network egress)."""

import pytest

from promptdb.api.remote_db import UnsafeDatabaseURL, _assert_public_host, safe_engine


@pytest.mark.parametrize("url", [
    "sqlite:///some.db",                              # disallowed scheme (no remote file access)
    "file:///etc/passwd",                             # disallowed scheme
    "postgresql://u:p@localhost:5432/db",             # loopback
    "postgresql://u:p@127.0.0.1/db",                  # loopback
    "postgresql://u:p@10.0.0.5/db",                   # private
    "mysql+pymysql://u:p@192.168.1.10/db",            # private
    "postgresql://u:p@169.254.169.254/db",            # cloud metadata / link-local
])
def test_unsafe_urls_blocked(url):
    with pytest.raises(UnsafeDatabaseURL):
        safe_engine(url)


def test_public_host_allowed():
    # a public host passes the SSRF gate (reachability is probed separately in safe_engine,
    # which needs a live host, so we assert the allow-path here without opening a socket)
    assert _assert_public_host("example.com") is None
