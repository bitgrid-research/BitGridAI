"""
BitGridAI REST API — FastAPI

Drei Endpunkte:
  GET  /state     → aktueller EnergyState
  GET  /decision  → letzte Decision mit Erklärung
  POST /override  → manueller Eingriff mit TTL

Keine Business-Logic — nur dünne Schicht über core/ und data/.
"""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="BitGridAI API", version="0.1.0")

# ---------------------------------------------------------------------------
# In-Memory State (wird im echten Betrieb durch DI ersetzt)
# ---------------------------------------------------------------------------

_current_state: dict | None = None
_current_decision: dict | None = None


def set_state(state: dict) -> None:
    global _current_state
    _current_state = state


def set_decision(decision: dict) -> None:
    global _current_decision
    _current_decision = decision


# ---------------------------------------------------------------------------
# Endpunkte
# ---------------------------------------------------------------------------


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/state")
def get_state() -> dict:
    if _current_state is None:
        raise HTTPException(status_code=503, detail="Noch kein EnergyState verfügbar")
    return _current_state


@app.get("/decision")
def get_decision() -> dict:
    if _current_decision is None:
        raise HTTPException(status_code=503, detail="Noch keine Decision verfügbar")
    return _current_decision


class OverrideRequest(BaseModel):
    action: str        # START | STOP | NOOP
    duration_min: int  # Gültigkeitsdauer in Minuten


@app.post("/override")
def post_override(req: OverrideRequest) -> dict:
    if req.action not in ("START", "STOP", "NOOP"):
        raise HTTPException(status_code=400, detail=f"Ungültige Action: {req.action}")

    if req.duration_min < 1 or req.duration_min > 120:
        raise HTTPException(status_code=400, detail="duration_min muss zwischen 1 und 120 liegen")

    # R3 Safety prüfen
    if _current_decision and _current_decision.get("decision_code", "").startswith("STOP_R3_"):
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
