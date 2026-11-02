"""
QueryServer — typisierte, read-only Abfragen auf bitgrid.db fuer den Nachtforscher.

Bewusst **kein** frei formuliertes SQL fuer das Sprachmodell. Der Agent waehlt
ein Werkzeug und einen Zeitraum, nicht Joins und Spaltennamen. Drei Gruende:

1. Reproduzierbarkeit. Dieselbe Frage liefert in drei Monaten dieselbe Zahl.
   Darauf beruht die Nachvollziehbarkeit des Projekts.
2. Kontextfenster. Jede Antwort ist hart begrenzt (_MAX_ROWS). Eine freie
   Abfrage ueber energy_states koennte 4464 Zeilen liefern und das Fenster
   fuellen, ohne dass der Agent klueger waere.
3. Sicherheit. Die DB wird schreibgeschuetzt geoeffnet (mode=ro). Der Agent
   kann nichts veraendern, auch nicht versehentlich.

Antwortformate:
  ?format=json  Standard, maschinenlesbar
  ?format=md    Markdown-Tabelle, deutlich tokensparsamer fuer ein LLM

Die Werkzeuge entsprechen database_exploration/werkzeuge.md im Obsidian-Vault.
Wer hier etwas aendert, aendert dort mit, sonst beschreibt der Vault ein System,
das es nicht gibt.

CLI:
    python -m src.data.query_server

Env:
    BITGRID_DB          Pfad zur DB (default: data/bitgrid.db)
    QUERY_SERVER_PORT   Listen-Port (default: 8768)
"""

from __future__ import annotations

import json
import logging
import os
import sqlite3
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Callable
from urllib.parse import parse_qs, urlparse

log = logging.getLogger(__name__)

_DEFAULT_PORT = 8768
# Harte Obergrenzen je Werkzeug. Sie schuetzen das Kontextfenster des Agenten
# und sind bewusst niedrig: wer mehr Zeilen braucht, stellt die falsche Frage
# auf der falschen Verdichtungsebene.
_MAX_ROWS: dict[str, int] = {
    "tage": 400,  # gut ein Jahr
    "miner_tage": 800,
    "modus_effizienz": 50,
    "schaltfehler": 200,
    "ungenutzter_ueberschuss": 200,
    "bloecke": 18,  # 3 Stunden a 10 Minuten
}


def _connect(db_path: str) -> sqlite3.Connection:
    """Oeffnet die DB strikt schreibgeschuetzt."""
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def _rows(
    conn: sqlite3.Connection, sql: str, params: tuple[Any, ...]
) -> list[dict[str, Any]]:
    return [dict(r) for r in conn.execute(sql, params).fetchall()]


def _round(rows: list[dict[str, Any]], digits: int = 2) -> list[dict[str, Any]]:
    """Rundet Gleitkommazahlen. 14 Nachkommastellen sind reine Tokenverschwendung."""
    out: list[dict[str, Any]] = []
    for row in rows:
        out.append(
            {
                k: (round(v, digits) if isinstance(v, float) else v)
                for k, v in row.items()
            }
        )
    return out


# ---------------------------------------------------------------------------
# Werkzeuge
# ---------------------------------------------------------------------------


def tool_tage(conn: sqlite3.Connection, q: dict[str, str]) -> list[dict[str, Any]]:
    von = q.get("von", "0000-01-01")
    bis = q.get("bis", "9999-12-31")
    return _rows(
        conn,
        "SELECT day, blocks, coverage_pct, quality_warn, quality_error,"
        " missing_signals, pv_kwh, house_kwh, grid_import_kwh, grid_export_kwh,"
        " mining_kwh, heizstab_kwh, energy_to_sats, pv_peak_w, soc_min_pct,"
        " soc_max_pct, soc_mean_pct, soc_h_locked, soc_h_hold, soc_h_eco,"
        " soc_h_standard, soc_h_super, blocks_temp_ge_110, blocks_switch_mismatch,"
        " blocks_surplus_idle FROM daily_kpi WHERE day >= ? AND day <= ?"
        " ORDER BY day LIMIT ?",
        (von, bis, _MAX_ROWS["tage"]),
    )


def tool_miner_tage(
    conn: sqlite3.Connection, q: dict[str, str]
) -> list[dict[str, Any]]:
    von = q.get("von", "0000-01-01")
    bis = q.get("bis", "9999-12-31")
    miner = q.get("miner", "%")
    return _rows(
        conn,
        "SELECT day, miner, h_eco, h_standard, h_super, h_standby, ths_mean,"
        " watt_mean, w_per_th, tmax_max_c, tmax_mean_c, spread_mean_k,"
        " blocks_ge_110, switch_mismatches, rejection_mean_pct"
        " FROM daily_miner_kpi WHERE day >= ? AND day <= ? AND miner LIKE ?"
        " ORDER BY day, miner LIMIT ?",
        (von, bis, miner, _MAX_ROWS["miner_tage"]),
    )


def tool_modus_effizienz(
    conn: sqlite3.Connection, q: dict[str, str]
) -> list[dict[str, Any]]:
    miner = q.get("miner", "%")
    return _rows(
        conn,
        "SELECT miner, modus, bloecke, ths_mittel, watt_mittel, w_pro_th,"
        " watt_typenschild, tmax_mittel, tmax_max"
        " FROM v_modus_effizienz WHERE miner LIKE ?"
        " ORDER BY miner, watt_mittel LIMIT ?",
        (miner, _MAX_ROWS["modus_effizienz"]),
    )


def tool_schaltfehler(
    conn: sqlite3.Connection, q: dict[str, str]
) -> list[dict[str, Any]]:
    von = q.get("von", "0000")
    bis = q.get("bis", "9999")
    return _rows(
        conn,
        "SELECT block_id, miner, workmode_set, workmode_status FROM v_schaltfehler"
        " WHERE block_id >= ? AND block_id <= ? ORDER BY block_id LIMIT ?",
        (von, bis + "T99", _MAX_ROWS["schaltfehler"]),
    )


def tool_ungenutzter_ueberschuss(
    conn: sqlite3.Connection, q: dict[str, str]
) -> list[dict[str, Any]]:
    von = q.get("von", "0000")
    bis = q.get("bis", "9999")
    return _rows(
        conn,
        "SELECT block_id, grid_export_w, miner_power_w, battery_soc_pct, pv_power_w"
        " FROM v_ungenutzter_ueberschuss WHERE block_id >= ? AND block_id <= ?"
        " ORDER BY block_id LIMIT ?",
        (von, bis + "T99", _MAX_ROWS["ungenutzter_ueberschuss"]),
    )


def tool_bloecke(conn: sqlite3.Connection, q: dict[str, str]) -> list[dict[str, Any]]:
    tag = q.get("tag", "")
    von = q.get("von", "00:00")
    bis = q.get("bis", "23:59")
    return _rows(
        conn,
        "SELECT block_id, pv_power_w, house_load_w, grid_export_w, grid_import_w,"
        " battery_soc_pct, miner_power_w, miner_temp_c, quality, missing_signals_json"
        " FROM energy_states WHERE block_id >= ? AND block_id <= ?"
        " ORDER BY block_id LIMIT ?",
        (f"{tag}T{von}:00", f"{tag}T{bis}:59", _MAX_ROWS["bloecke"]),
    )


TOOLS: dict[
    str, Callable[[sqlite3.Connection, dict[str, str]], list[dict[str, Any]]]
] = {
    "tage": tool_tage,
    "miner_tage": tool_miner_tage,
    "modus_effizienz": tool_modus_effizienz,
    "schaltfehler": tool_schaltfehler,
    "ungenutzter_ueberschuss": tool_ungenutzter_ueberschuss,
    "bloecke": tool_bloecke,
}


def to_markdown(rows: list[dict[str, Any]]) -> str:
    """Markdown-Tabelle. Spart gegenueber JSON rund die Haelfte der Token,
    weil die Spaltennamen nur einmal statt pro Zeile auftauchen."""
    if not rows:
        return "_keine Zeilen_"
    cols = list(rows[0].keys())
    out = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for row in rows:
        out.append(
            "| "
            + " | ".join("" if row[c] is None else str(row[c]) for c in cols)
            + " |"
        )
    return "\n".join(out)


class _Handler(BaseHTTPRequestHandler):
    db_path: str = "data/bitgrid.db"

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        name = parsed.path.strip("/")
        params = {k: v[0] for k, v in parse_qs(parsed.query).items()}

        if name in ("", "health"):
            self._send_json(200, {"ok": True, "werkzeuge": sorted(TOOLS)})
            return

        tool = TOOLS.get(name)
        if tool is None:
            self._send_json(
                404,
                {
                    "ok": False,
                    "fehler": f"unbekanntes Werkzeug: {name}",
                    "verfuegbar": sorted(TOOLS),
                },
            )
            return

        try:
            conn = _connect(self.db_path)
            try:
                rows = _round(tool(conn, params))
            finally:
                conn.close()
        except sqlite3.Error as exc:
            log.exception("Abfrage fehlgeschlagen: %s", name)
            self._send_json(500, {"ok": False, "fehler": str(exc)})
            return

        limit = _MAX_ROWS.get(name, 0)
        gekuerzt = len(rows) >= limit
        if params.get("format") == "md":
            text = to_markdown(rows)
            if gekuerzt:
                text += (
                    f"\n\n_Achtung: bei {limit} Zeilen abgeschnitten. "
                    "Waehle einen kuerzeren Zeitraum oder eine groebere Ebene._"
                )
            self._send_text(200, text)
        else:
            self._send_json(
                200,
                {
                    "ok": True,
                    "werkzeug": name,
                    "zeilen": len(rows),
                    "gekuerzt": gekuerzt,
                    "daten": rows,
                },
            )

    def _send_json(self, status: int, payload: dict[str, Any]) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self._send(status, body, "application/json; charset=utf-8")

    def _send_text(self, status: int, text: str) -> None:
        self._send(status, text.encode("utf-8"), "text/markdown; charset=utf-8")

    def _send(self, status: int, body: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:  # noqa: A002
        log.info("%s - %s", self.address_string(), format % args)


def main() -> None:
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s"
    )
    port = int(os.getenv("QUERY_SERVER_PORT", str(_DEFAULT_PORT)))
    _Handler.db_path = os.getenv("BITGRID_DB", "data/bitgrid.db")

    server = ThreadingHTTPServer(("0.0.0.0", port), _Handler)
    log.info(
        "Query-Server auf Port %d, DB %s (read-only), Werkzeuge: %s",
        port,
        _Handler.db_path,
        ", ".join(sorted(TOOLS)),
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
