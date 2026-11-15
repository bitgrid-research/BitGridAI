"""BitaxeAdapter takes its host only from the caller or the environment."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from src.adapters.bitaxe_adapter import BitaxeAdapter


def test_missing_host_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("BITAXE_HOST", raising=False)
    with pytest.raises(ValueError, match="BITAXE_HOST"):
        BitaxeAdapter(ingest=MagicMock())


def test_host_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BITAXE_HOST", "bitaxe.local")
    assert "bitaxe.local" in BitaxeAdapter(ingest=MagicMock())._url
