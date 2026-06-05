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


class UnsafeDatabaseURL(ValueError):
    """Raised when a connection string is disallowed or resolves to a non-public address."""


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


def safe_engine(url: str) -> Engine:
    """Validate a user connection string and return a short-lived read-oriented engine."""
    parsed = urlparse(url)
    if parsed.scheme.lower() not in ALLOWED_SCHEMES:
        raise UnsafeDatabaseURL("only postgresql:// or mysql:// connection strings are allowed")
    _assert_public_host(parsed.hostname)
    return create_engine(url, connect_args={"connect_timeout": 8}, pool_pre_ping=True)
