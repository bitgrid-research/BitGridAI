"""
Unit-Tests für ConfigLoader und rules_to_engine_config.

Abgedeckt:
  ConfigLoader.load()        — Datei lesen, SHA256-Version
  ConfigLoader.hot_reload()  — Erfolg, Fehler bei ungültigem YAML, Version ändert sich
  rules_to_engine_config()   — leeres Dict (Defaults), partielle Overrides, null-Wert
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest
import yaml

from src.ops.config_loader import ConfigLoader, rules_to_engine_config
from src.core.rule_engine import RuleEngineConfig

# ---------------------------------------------------------------------------
# ConfigLoader.load()
# ---------------------------------------------------------------------------


class TestLoad:
    def test_load_returns_dict(self, tmp_path: Path) -> None:
        f = tmp_path / "rules.yaml"
        f.write_text("rules:\n  r1:\n    surplus_min_kw: 2.0\n", encoding="utf-8")

        loader = ConfigLoader(f)
        data = loader.load()

        assert isinstance(data, dict)
        assert data["rules"]["r1"]["surplus_min_kw"] == 2.0

    def test_load_sets_version(self, tmp_path: Path) -> None:
        f = tmp_path / "rules.yaml"
        content = "rules: {}\n"
        f.write_text(content, encoding="utf-8")

        loader = ConfigLoader(f)
        loader.load()

        expected = hashlib.sha256(content.encode()).hexdigest()[:12]
        assert loader.version == expected

    def test_load_empty_file_returns_empty_dict(self, tmp_path: Path) -> None:
        f = tmp_path / "rules.yaml"
        f.write_text("", encoding="utf-8")

        loader = ConfigLoader(f)
        data = loader.load()
        assert data == {}

    def test_load_missing_file_raises(self, tmp_path: Path) -> None:
        loader = ConfigLoader(tmp_path / "nonexistent.yaml")
        with pytest.raises(FileNotFoundError):
            loader.load()


# ---------------------------------------------------------------------------
# ConfigLoader.hot_reload()
# ---------------------------------------------------------------------------


class TestHotReload:
    def test_hot_reload_success_updates_data(self, tmp_path: Path) -> None:
        f = tmp_path / "rules.yaml"
        f.write_text("rules:\n  r1:\n    surplus_min_kw: 1.5\n", encoding="utf-8")
        loader = ConfigLoader(f)
        loader.load()

        f.write_text("rules:\n  r1:\n    surplus_min_kw: 3.0\n", encoding="utf-8")
        result = loader.hot_reload()

        assert result.success is True
        assert result.errors == []
        assert loader.data["rules"]["r1"]["surplus_min_kw"] == 3.0

    def test_hot_reload_version_changes_on_new_content(self, tmp_path: Path) -> None:
        f = tmp_path / "rules.yaml"
        f.write_text("rules: {}\n", encoding="utf-8")
        loader = ConfigLoader(f)
        loader.load()
        old_version = loader.version

        f.write_text("rules:\n  r1:\n    surplus_min_kw: 9.9\n", encoding="utf-8")
        loader.hot_reload()

        assert loader.version != old_version

    def test_hot_reload_missing_file_returns_failure(self, tmp_path: Path) -> None:
        f = tmp_path / "rules.yaml"
        f.write_text("rules: {}\n", encoding="utf-8")
        loader = ConfigLoader(f)
        loader.load()
        old_version = loader.version

        f.unlink()  # Datei löschen
        result = loader.hot_reload()

        assert result.success is False
        assert len(result.errors) > 0
        # Alte Version bleibt erhalten
        assert loader.version == old_version

    def test_hot_reload_invalid_yaml_returns_failure(self, tmp_path: Path) -> None:
        f = tmp_path / "rules.yaml"
        f.write_text("rules: {}\n", encoding="utf-8")
        loader = ConfigLoader(f)
        loader.load()

        f.write_text(": invalid: [yaml\n", encoding="utf-8")
        result = loader.hot_reload()

        assert result.success is False
        assert len(result.errors) > 0

    def test_hot_reload_preserves_old_data_on_failure(self, tmp_path: Path) -> None:
        f = tmp_path / "rules.yaml"
        f.write_text("rules:\n  r1:\n    surplus_min_kw: 1.5\n", encoding="utf-8")
        loader = ConfigLoader(f)
        loader.load()

        f.unlink()
        loader.hot_reload()

        # Alte Daten noch vorhanden
        assert loader.data["rules"]["r1"]["surplus_min_kw"] == 1.5

    def test_hot_reload_result_has_timestamp(self, tmp_path: Path) -> None:
        f = tmp_path / "rules.yaml"
        f.write_text("rules: {}\n", encoding="utf-8")
        loader = ConfigLoader(f)
        loader.load()

        result = loader.hot_reload()
        assert result.timestamp is not None


# ---------------------------------------------------------------------------
# rules_to_engine_config()
# ---------------------------------------------------------------------------


class TestRulesToEngineConfig:
    def test_empty_dict_returns_all_defaults(self) -> None:
        cfg = rules_to_engine_config({})
        defaults = RuleEngineConfig()

        assert cfg.surplus_min_kw == defaults.surplus_min_kw
        assert cfg.price_max_ct_kwh == defaults.price_max_ct_kwh
        assert cfg.soc_soft_min_pct == defaults.soc_soft_min_pct
        assert cfg.soc_hard_min_pct == defaults.soc_hard_min_pct
        assert cfg.max_grid_import_w == defaults.max_grid_import_w
        assert cfg.max_chip_temp_c == defaults.max_chip_temp_c
        assert cfg.t_resume_c == defaults.t_resume_c
        assert cfg.comm_timeout_sec == defaults.comm_timeout_sec
        assert cfg.min_predicted_surplus_kw == defaults.min_predicted_surplus_kw
        assert cfg.price_spike_threshold_ct == defaults.price_spike_threshold_ct
        assert cfg.deadband_hold_blocks == defaults.deadband_hold_blocks
        assert cfg.min_runtime_blocks == defaults.min_runtime_blocks
        assert cfg.min_pause_blocks == defaults.min_pause_blocks

    def test_partial_r1_override_preserves_other_defaults(self) -> None:
        data = {"rules": {"r1": {"surplus_min_kw": 2.5}}}
        cfg = rules_to_engine_config(data)

        assert cfg.surplus_min_kw == pytest.approx(2.5)
        # Alle anderen Defaults unverändert
        assert cfg.price_max_ct_kwh == RuleEngineConfig().price_max_ct_kwh
        assert cfg.max_chip_temp_c == RuleEngineConfig().max_chip_temp_c

    def test_all_rules_overridden(self) -> None:
        data = {
            "rules": {
                "r1": {"surplus_min_kw": 2.0, "price_max_ct_kwh": 20.0},
                "r2": {
                    "soc_soft_min_pct": 30.0,
                    "soc_hard_min_pct": 15.0,
                    "max_grid_import_w": 300.0,
                },
                "r3": {
                    "max_chip_temp_c": 80.0,
                    "t_resume_c": 70.0,
                    "comm_timeout_sec": 45.0,
                },
                "r4": {
                    "min_predicted_surplus_kw": 1.5,
                    "price_spike_threshold_ct": 25.0,
                },
                "r5": {
                    "deadband_hold_blocks": 3,
                    "min_runtime_blocks": 4,
                    "min_pause_blocks": 3,
                },
            }
        }
        cfg = rules_to_engine_config(data)

        assert cfg.surplus_min_kw == pytest.approx(2.0)
        assert cfg.price_max_ct_kwh == pytest.approx(20.0)
        assert cfg.soc_soft_min_pct == pytest.approx(30.0)
        assert cfg.soc_hard_min_pct == pytest.approx(15.0)
        assert cfg.max_grid_import_w == pytest.approx(300.0)
        assert cfg.max_chip_temp_c == pytest.approx(80.0)
        assert cfg.t_resume_c == pytest.approx(70.0)
        assert cfg.comm_timeout_sec == pytest.approx(45.0)
        assert cfg.min_predicted_surplus_kw == pytest.approx(1.5)
        assert cfg.price_spike_threshold_ct == pytest.approx(25.0)
        assert cfg.deadband_hold_blocks == 3
        assert cfg.min_runtime_blocks == 4
        assert cfg.min_pause_blocks == 3

    def test_price_max_null_becomes_none(self) -> None:
        """price_max_ct_kwh: null → None (kein Preis-Veto)."""
        data = {"rules": {"r1": {"price_max_ct_kwh": None}}}
        cfg = rules_to_engine_config(data)
        assert cfg.price_max_ct_kwh is None

    def test_missing_rules_key_uses_defaults(self) -> None:
        """Config ohne 'rules'-Schlüssel → alle Defaults."""
        cfg = rules_to_engine_config({"metadata": {"version": "1.0"}})
        defaults = RuleEngineConfig()
        assert cfg.surplus_min_kw == defaults.surplus_min_kw
        assert cfg.deadband_hold_blocks == defaults.deadband_hold_blocks

    def test_config_is_rule_engine_config_instance(self) -> None:
        cfg = rules_to_engine_config({})
        assert isinstance(cfg, RuleEngineConfig)
