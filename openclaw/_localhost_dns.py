"""Process-local resolver shim for `*.localhost` hostnames.

Phase 5 puts each pilot subsite on a `<slug>.localhost` subdomain of the local
Docker multisite. RFC 6761 reserves the whole `.localhost` TLD for loopback,
but Windows' resolver stack (used by Python's `socket.getaddrinfo`) does not
auto-resolve subdomains — curl and browsers short-circuit them, Python does
not. The system hosts file would fix it but requires admin.

We monkey-patch `socket.getaddrinfo` inside this Python process so any
`*.localhost` lookup resolves to 127.0.0.1. Non-`.localhost` hostnames pass
through unchanged. Idempotent (installs once even if imported repeatedly).
"""

from __future__ import annotations

import socket

_LOOPBACK = "127.0.0.1"
_installed = False


def _matches_localhost(host: str) -> bool:
    if not host:
        return False
    host = host.lower().rstrip(".")
    return host == "localhost" or host.endswith(".localhost")


def install() -> None:
    """Install the resolver shim. Safe to call multiple times."""
    global _installed
    if _installed:
        return
    original = socket.getaddrinfo

    def patched(host, port, *args, **kwargs):
        if isinstance(host, str) and _matches_localhost(host):
            return original(_LOOPBACK, port, *args, **kwargs)
        return original(host, port, *args, **kwargs)

    socket.getaddrinfo = patched  # type: ignore[assignment]
    _installed = True


# Auto-install on import so any module that imports openclaw.* gets the shim.
install()
