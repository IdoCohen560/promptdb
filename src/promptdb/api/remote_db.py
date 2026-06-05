"""Build a SQLAlchemy engine for a user-supplied connection string, with SSRF protection.

A public demo that connects to arbitrary hosts is an SSRF risk: a crafted string could point the
server at an internal service or a cloud metadata endpoint (169.254.169.254). So we allow only
cloud-reachable Postgres/MySQL, resolve the hostname, and reject any address in a private,
loopback, link-local, or reserved range. Writes are still blocked by the mutation validator;
users are told to connect with a read-only database user.
"""

import ipaddress
import socket
from urllib.parse import urlparse

from sqlalchemy import Engine, create_engine

ALLOWED_SCHEMES = {
    "postgresql", "postgres", "postgresql+psycopg2", "postgresql+psycopg",
    "mysql", "mysql+pymysql",
}


DEFAULT_PORTS = {"postgresql": 5432, "postgres": 5432, "mysql": 3306}
PROBE_TIMEOUT = 6.0


class UnsafeDatabaseURL(ValueError):
    """Raised when a connection string is disallowed or resolves to a non-public address."""


class DatabaseUnreachable(ConnectionError):
    """Raised when the host cannot be reached quickly (so the request fails fast, not in 60s)."""


def _assert_public_host(host: str | None) -> None:
    if not host:
        raise UnsafeDatabaseURL("missing host")
    try:
        infos = socket.getaddrinfo(host, None)
    except socket.gaierror:
        raise UnsafeDatabaseURL(f"cannot resolve host '{host}'")
    for info in infos:
        ip = ipaddress.ip_address(info[4][0])
        if (ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved
                or ip.is_multicast or ip.is_unspecified):
            raise UnsafeDatabaseURL("host resolves to a private or reserved address")


def _assert_reachable(host: str, port: int) -> None:
    """Fast TCP probe so an unreachable/filtered host fails in seconds, not on a 60s hang."""
    try:
        with socket.create_connection((host, port), timeout=PROBE_TIMEOUT):
            return
    except OSError as exc:
        raise DatabaseUnreachable(f"could not reach {host}:{port} ({exc})")


def safe_engine(url: str) -> Engine:
    """Validate a user connection string and return a short-lived read-oriented engine."""
    parsed = urlparse(url)
    scheme = parsed.scheme.lower()
    if scheme not in ALLOWED_SCHEMES:
        raise UnsafeDatabaseURL("only postgresql:// or mysql:// connection strings are allowed")
    _assert_public_host(parsed.hostname)
    port = parsed.port or DEFAULT_PORTS.get(scheme.split("+")[0], 5432)
    _assert_reachable(parsed.hostname, port)
    return create_engine(url, connect_args={"connect_timeout": 8}, pool_pre_ping=True)
