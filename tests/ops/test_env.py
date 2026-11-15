"""require_env: hosts come from .env, a missing value is an error."""

from __future__ import annotations

import pytest

from src.ops.env import require_env


def test_missing_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("BG_TEST_HOST", raising=False)
    with pytest.raises(ValueError, match="BG_TEST_HOST"):
        require_env("BG_TEST_HOST")


def test_empty_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BG_TEST_HOST", "")
    with pytest.raises(ValueError):
        require_env("BG_TEST_HOST")


def test_value_returned(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BG_TEST_HOST", "miner.local")
    assert require_env("BG_TEST_HOST") == "miner.local"
