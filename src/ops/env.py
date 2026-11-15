"""Required settings from the environment (.env), never as code defaults.

Hosts, IPs and credentials do not belong in git; a missing value is a clear
error instead of a silent fallback to a device address.
"""

from __future__ import annotations

import os


def require_env(name: str) -> str:
    """Value of ``name`` from the environment; ValueError if unset or empty."""
    value = os.getenv(name)
    if not value:
        raise ValueError(f"{name} is not set: add it to .env")
    return value
