"""
BitGridAI REST API — FastAPI

Endpunkte:
  GET  /health              → Systemstatus
  GET  /state               → aktueller EnergyState
  GET  /decision            → letzte Decision mit Erklärung
  GET  /timeline?n=20       → letzte N DecisionEvents aus EventStore
  GET  /explain/{id}        → vollständiger ExplainResult für decision_id
  POST /override            → manueller Eingriff mit TTL
  POST /research/export     → Forschungs-Export (Parquet + Manifest + SHA256)

Keine Business-Logic hier — nur dünne Schicht über core/ und data/.
"""

from __future__ import annotations

import hashlib
import io
import json
import time
import uuid
import zipfile
from collections import defaultdict
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel

from src.adapters.health_monitor import HealthMonitor
from src.core.models import EnergyState
from src.core.override_handler import AutonomyLevel, OverrideHandler
from src.core.rule_engine import RuleEngineConfig
from src.core.rule_engine import evaluate as _engine_evaluate

if TYPE_CHECKING:
    from src.data.event_store import EventStore
    from src.explain.explain_agent import ExplainAgent

app = FastAPI(title="BitGridAI API", version="0.3.0")

# ---------------------------------------------------------------------------
# Dependency-Injection via Setter (wird vom ProductionRunner befüllt)
# ---------------------------------------------------------------------------

_current_state: dict[str, Any] | None = None
_current_decision: dict[str, Any] | None = None
_event_store: "EventStore | None" = None
_explain_agent: "ExplainAgent | None" = None
_override_handler: OverrideHandler | None = None
_engine_config: RuleEngineConfig | None = None
_health_monitor: HealthMonitor | None = None
_api_token: str = ""
_auth_enabled: bool = False


def set_state(state: dict[str, Any]) -> None:
    global _current_state
    _current_state = state


def set_decision(decision: dict[str, Any]) -> None:
    global _current_decision
    _current_decision = decision


def set_stores(event_store: "EventStore", explain_agent: "ExplainAgent") -> None:
    global _event_store, _explain_agent
    _event_store = event_store
    _explain_agent = explain_agent


def set_override_handler(handler: OverrideHandler) -> None:
    global _override_handler
    _override_handler = handler


def set_health_monitor(monitor: HealthMonitor) -> None:
    global _health_monitor
    _health_monitor = monitor


def set_engine_config(config: RuleEngineConfig) -> None:
    global _engine_config
    _engine_config = config


def set_auth(enabled: bool, token: str) -> None:
    global _auth_enabled, _api_token
    _auth_enabled = enabled
    _api_token = token


# ---------------------------------------------------------------------------
# Auth-Middleware (H4) — Bearer-Token wenn auth_enabled
# ---------------------------------------------------------------------------

_PUBLIC_PATHS = {"/health", "/docs", "/openapi.json", "/redoc"}


@app.middleware("http")
async def auth_middleware(request: Request, call_next: Any) -> Any:
    if _auth_enabled and request.url.path not in _PUBLIC_PATHS:
        header = request.headers.get("Authorization", "")
        if not header.startswith("Bearer ") or header[7:] != _api_token:
            return JSONResponse(status_code=401, content={"detail": "Unauthorized"})
    return await call_next(request)


# ---------------------------------------------------------------------------
# Rate-Limiter (H5) — sliding window, max 10 req/min per IP für /override
# ---------------------------------------------------------------------------

_override_hits: dict[str, list[float]] = defaultdict(list)
_RATE_LIMIT = 10
_RATE_WINDOW = 60.0


def _check_rate(client_ip: str) -> bool:
    now = time.monotonic()
    hits = [t for t in _override_hits[client_ip] if now - t < _RATE_WINDOW]
    _override_hits[client_ip] = hits
    if len(hits) >= _RATE_LIMIT:
        return False
    _override_hits[client_ip].append(now)
    return True


# ---------------------------------------------------------------------------
# Endpunkte
# ---------------------------------------------------------------------------


@app.get("/health")
def health() -> dict[str, Any]:
    adapters: list[dict[str, Any]] = []
    if _health_monitor is not None:
        for ah in _health_monitor.all_adapters():
            adapters.append(
                {
                    "adapter": ah.adapter,
                    "status": ah.status,
                    "conn_state": ah.conn_state,
                    "last_seen": ah.last_seen.isoformat(),
                    "error_message": ah.error_message,
                }
            )
    return {
        "status": "ok",
        "state_available": _current_state is not None,
        "adapters": adapters,
    }


@app.get("/state")
def get_state() -> dict[str, Any]:
    if _current_state is None:
        raise HTTPException(status_code=503, detail="Noch kein EnergyState verfügbar")
    return _current_state


@app.get("/decision")
def get_decision() -> dict[str, Any]:
    if _current_decision is None:
        raise HTTPException(status_code=503, detail="Noch keine Decision verfügbar")
    return _current_decision


@app.get("/timeline")
def get_timeline(n: int = Query(default=20, ge=1, le=200)) -> list[dict[str, Any]]:
    """Gibt die letzten N DecisionEvents zurück (neueste zuerst)."""
    if _event_store is None:
        raise HTTPException(status_code=503, detail="EventStore nicht initialisiert")
    return _event_store.latest(n)


@app.get("/explain/{decision_id}")
def get_explain(decision_id: str) -> dict[str, Any]:
    """Gibt den vollständigen ExplainResult für eine decision_id zurück."""
    if _event_store is None or _explain_agent is None:
        raise HTTPException(status_code=503, detail="Stores nicht initialisiert")

    row = _event_store.read(decision_id)
    if row is None:
        raise HTTPException(
            status_code=404, detail=f"Decision {decision_id!r} nicht gefunden"
        )

    import json

    params = json.loads(row.get("params_json") or "{}")
    result = _explain_agent.explain(
        decision_code=row["decision_code"],
        params=params,
    )
    return {
        "decision_id": decision_id,
        "decision_code": result.decision_code,
        "short": result.short,
        "long": result.long,
        "trigger": result.trigger,
        "data_basis": result.data_basis,
        "effect": result.effect,
        "options": result.options,
        "lang": result.lang,
    }


class OverrideRequest(BaseModel):
    action: str
    duration_min: int


@app.post("/override")
def post_override(req: OverrideRequest, request: Request) -> dict[str, Any]:
    client_ip = request.client.host if request.client else "unknown"
    if not _check_rate(client_ip):
        raise HTTPException(
            status_code=429,
            detail="Rate limit überschritten — max. 10 Anfragen/Minute",
        )

    if req.action not in ("START", "STOP", "NOOP"):
        raise HTTPException(status_code=400, detail=f"Ungültige Action: {req.action}")

    if req.duration_min < 1 or req.duration_min > 120:
        raise HTTPException(
            status_code=400, detail="duration_min muss zwischen 1 und 120 liegen"
        )

    if _current_decision and _current_decision.get("decision_code", "").startswith(
        "STOP_R3_"
    ):
        return {
            "accepted": False,
            "reason": "R3_SAFETY_ACTIVE — Override nicht erlaubt",
        }

    command_id = str(uuid.uuid4())
    return {
        "accepted": True,
        "command_id": command_id,
        "action": req.action,
        "duration_min": req.duration_min,
        "message": f"Override akzeptiert für {req.duration_min} Minuten",
    }


# ---------------------------------------------------------------------------
# Research Export (H3) — Parquet + Manifest + SHA256, opt-in via feature flag
# ---------------------------------------------------------------------------

_research_export_enabled: bool = False


def set_research_export(enabled: bool) -> None:
    global _research_export_enabled
    _research_export_enabled = enabled


@app.post("/research/export")
def post_research_export() -> StreamingResponse:
    """Exportiert alle DecisionEvents als Parquet-Bundle (ZIP).

    Erfordert Feature-Flag research_export=true.
    Gibt zurück: ZIP mit events.parquet, manifest.json, CHECKSUMS.sha256.
    """
    if not _research_export_enabled:
        raise HTTPException(
            status_code=403,
            detail="research_export ist deaktiviert — Feature-Flag setzen",
        )
    if _event_store is None:
        raise HTTPException(status_code=503, detail="EventStore nicht initialisiert")

    try:
        import pandas as pd
    except ImportError:
        raise HTTPException(
            status_code=501,
            detail="pandas/pyarrow nicht installiert",
        )

    rows = _event_store.latest(n=10_000)
    df = pd.DataFrame(rows)

    parquet_buf = io.BytesIO()
    df.to_parquet(parquet_buf, index=False, engine="pyarrow")
    parquet_bytes = parquet_buf.getvalue()
    parquet_sha256 = hashlib.sha256(parquet_bytes).hexdigest()

    now_iso = datetime.now(tz=timezone.utc).isoformat()
    manifest = {
        "exported_at": now_iso,
        "row_count": len(df),
        "columns": list(df.columns),
        "events_parquet_sha256": parquet_sha256,
        "format_version": "1.0",
    }
    manifest_bytes = json.dumps(manifest, indent=2, ensure_ascii=False).encode()
    checksums = (
        f"{parquet_sha256}  events.parquet\n"
        f"{hashlib.sha256(manifest_bytes).hexdigest()}  manifest.json\n"
    ).encode()

    zip_buf = io.BytesIO()
    with zipfile.ZipFile(zip_buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("events.parquet", parquet_bytes)
        zf.writestr("manifest.json", manifest_bytes)
        zf.writestr("CHECKSUMS.sha256", checksums)

    zip_buf.seek(0)
    filename = f"bitgridai_export_{now_iso[:10]}.zip"
    return StreamingResponse(
        zip_buf,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ---------------------------------------------------------------------------
# Preview / What-if (M3) — read-only sandbox, no actuation
# ---------------------------------------------------------------------------


class PreviewRequest(BaseModel):
    pv_power_w: float | None = None
    house_load_w: float | None = None
    grid_import_w: float | None = None
    battery_soc_pct: float | None = None
    miner_temp_c: float | None = None
    miner_heartbeat_age_sec: float | None = None
    energy_price_ct_kwh: float | None = None
    pv_forecast_kw: float | None = None


@app.post("/preview")
def post_preview(req: PreviewRequest) -> dict[str, Any]:
    """Simuliert eine Regelentscheidung mit hypothetischen Eingaben (kein Seiteneffekt)."""
    if _current_state is None:
        raise HTTPException(status_code=503, detail="Noch kein EnergyState verfügbar")

    now = datetime.now(tz=timezone.utc)

    base = _current_state
    pv = (
        req.pv_power_w
        if req.pv_power_w is not None
        else float(base.get("pv_power_w") or 0.0)
    )
    load = (
        req.house_load_w
        if req.house_load_w is not None
        else float(base.get("house_load_w") or 0.0)
    )
    grid = (
        req.grid_import_w
        if req.grid_import_w is not None
        else float(base.get("grid_import_w") or 0.0)
    )
    soc = (
        req.battery_soc_pct
        if req.battery_soc_pct is not None
        else float(base.get("battery_soc_pct") or 0.0)
    )
    temp = (
        req.miner_temp_c
        if req.miner_temp_c is not None
        else float(base.get("miner_temp_c") or 25.0)
    )
    age = (
        req.miner_heartbeat_age_sec if req.miner_heartbeat_age_sec is not None else 0.0
    )
    price = req.energy_price_ct_kwh
    forecast = (
        req.pv_forecast_kw
        if req.pv_forecast_kw is not None
        else base.get("pv_forecast_kw")
    )
    surplus_kw = (pv - load) / 1000.0

    hypothetical = EnergyState(
        block_id=f"preview-{now.strftime('%Y%m%dT%H%M%S')}",
        window_start=now,
        window_end=now,
        pv_power_w=pv,
        house_load_w=load,
        grid_import_w=grid,
        battery_soc_pct=soc,
        miner_temp_c=temp,
        miner_heartbeat_age_sec=age,
        surplus_kw=surplus_kw,
        quality="ok",
        energy_price_ct_kwh=price,
        pv_forecast_kw=forecast,
    )

    config = _engine_config if _engine_config is not None else RuleEngineConfig()
    event = _engine_evaluate(hypothetical, config=config, now=now)

    return {
        "action": event.decision.action,
        "decision_code": event.decision_code,
        "reason": event.reason,
        "params": event.params,
        "hypothetical_state": {
            "pv_power_w": pv,
            "house_load_w": load,
            "grid_import_w": grid,
            "battery_soc_pct": soc,
            "miner_temp_c": temp,
            "surplus_kw": surplus_kw,
            "energy_price_ct_kwh": price,
            "pv_forecast_kw": forecast,
        },
    }


# ---------------------------------------------------------------------------
# Autonomy Level (M4) — GET/POST
# ---------------------------------------------------------------------------

_VALID_AUTONOMY_LEVELS = {"FULL", "SEMI", "MANUAL"}


class AutonomyRequest(BaseModel):
    level: str


@app.get("/autonomy")
def get_autonomy() -> dict[str, Any]:
    """Gibt die aktuelle Autonomie-Stufe zurück."""
    if _override_handler is None:
        raise HTTPException(
            status_code=503, detail="OverrideHandler nicht initialisiert"
        )
    return {"level": _override_handler.autonomy_level}


@app.post("/autonomy")
def post_autonomy(req: AutonomyRequest) -> dict[str, Any]:
    """Setzt die Autonomie-Stufe (FULL / SEMI / MANUAL)."""
    if _override_handler is None:
        raise HTTPException(
            status_code=503, detail="OverrideHandler nicht initialisiert"
        )
    if req.level not in _VALID_AUTONOMY_LEVELS:
        raise HTTPException(
            status_code=400,
            detail=f"Ungültige Autonomie-Stufe: {req.level!r}. Erlaubt: FULL, SEMI, MANUAL",
        )
    _override_handler.autonomy_level = req.level  # type: ignore[assignment]
    return {"level": _override_handler.autonomy_level, "accepted": True}
