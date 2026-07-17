"""
BitsyStatus — generiert eine warme Systemzustand-Erklaerung via Ollama und
publiziert sie ueber MQTT fuer den ₿itsy-Tab (Kontrakt: sensor.bitsy_advice,
konfiguriert in src/ha/config/configuration.yaml, Karte in
src/ha/config/views/ki_beratung.yaml).

Determinismus-Firewall: WAS der Zustand ist (welches SoC-Band, Nachtsperre,
Sicherheits-Stopp, Stimmung) entscheidet ausschliesslich classify_state() in
Python, ein Spiegel derselben Schwellen wie views/ki_bitsy.yaml. Ollama
bekommt diese fertige Klassifikation + Messwerte und formuliert NUR Headline
und Fliesstext daraus. Die "mood" kommt nie vom LLM, sie ist Teil der
Klassifikation. HomeLLaMA-Prinzip: das Modell erklaert, es entscheidet nie.

CLI:
    python -m src.explain.bitsy_status

Env-Vars (aus .env):
    UMBREL_HOST, HA_PORT, HA_TOKEN            — HA REST API (Zustand lesen)
    OLLAMA_HOST, OLLAMA_MODEL, OLLAMA_TIMEOUT_SEC — Ollama (Text generieren)
    MQTT_HOST, MQTT_PORT, MQTT_USER, MQTT_PASSWORD — Publish-Ziel
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from urllib.error import URLError
from urllib.request import Request, urlopen

from src.adapters.mqtt_client import MqttClient

log = logging.getLogger(__name__)

_ADVICE_TOPIC = "bitgrid/explain/bitsy/advice"
_STATUS_TOPIC = "bitgrid/explain/bitsy/status"
_CHAT_TOPIC = "bitgrid/explain/bitsy/chat"

_ENTITIES = [
    "sensor.battery_soc_pct",
    "sensor.pv_power_w",
    "sensor.grid_import_w",
    "sensor.grid_export_w",
    "binary_sensor.r2_grid_import_ok",
    "sensor.miner_total_power_w",
    "sensor.miner_max_chip_temp_c",
    "sensor.miner1_workmode_status",
    "sensor.miner2_workmode_status",
    "binary_sensor.mvp_nacht_sperre_aktiv",
    "binary_sensor.r5_min_runtime_active",
    "binary_sensor.r5_min_pause_active",
    "binary_sensor.r5_deadband_active",
    "sensor.miner_1_cooldown_status",
    "sensor.miner_2_cooldown_status",
    "input_datetime.mvp_miner1_temp_lockout_until",
    "input_datetime.mvp_miner2_temp_lockout_until",
    "input_text.batt_soc_trace",
    "input_number.mvp_soc_stop_pct",
    "input_number.mvp_soc_eco_start_pct",
    "input_number.mvp_soc_std_pct",
    "input_number.mvp_soc_super_pct",
    "input_number.mvp_pv_start_w",
    "input_number.mvp_tmax_std_threshold_c",
    "input_number.r2_max_grid_import_w",
    "input_number.r5_min_runtime_blocks",
    "input_datetime.mvp_night_block_start",
    "input_datetime.mvp_night_block_end",
]


def _hhmm(states: dict[str, str], entity_id: str, fallback: str) -> str:
    raw = states.get(entity_id)
    if not raw or raw in ("unknown", "unavailable"):
        return fallback
    return raw[:5]  # "22:00:00" -> "22:00"


@dataclass(frozen=True)
class StateClassification:
    code: str
    mood: str
    head: str
    numbers: dict[str, float | str | None]


def _fnum(states: dict[str, str], entity_id: str) -> float | None:
    raw = states.get(entity_id)
    if raw is None:
        return None
    try:
        return float(raw)
    except ValueError:
        return None


def _lockout_minutes_remaining(states: dict[str, str], entity_id: str) -> int | None:
    """Minuten bis ein input_datetime-Lockout ('YYYY-MM-DD HH:MM:SS') ablaeuft,
    None wenn kein aktiver Lockout (Wert in der Vergangenheit, z.B. der
    1970-01-01-Default, oder unlesbar)."""
    raw = states.get(entity_id)
    if not raw or raw in ("unknown", "unavailable"):
        return None
    try:
        until = datetime.strptime(raw, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return None
    remaining_sec = (until - datetime.now()).total_seconds()
    return int(remaining_sec // 60) if remaining_sec > 0 else None


def _hour_float_to_hhmm(hour_float: float) -> str:
    total_min = round(hour_float * 60)
    hh, mm = divmod(total_min, 60)
    return f"{hh:02d}:{mm:02d}"


def _soc_trend(states: dict[str, str]) -> str | None:
    """Liest input_text.batt_soc_trace ('YYYY-MM-DD|[[stunde, soc], ...]',
    30-Min-Snapshots seit Mitternacht, siehe mvp_auto.yaml). Liefert eine
    Verlaufsaussage ('08:30 Uhr 45.0% -> jetzt 82.0%') oder None, wenn die
    Spur leer/veraltet ist oder noch keine 2 Punkte hat (z.B. kurz nach dem
    Mitternacht-Reset)."""
    raw = states.get("input_text.batt_soc_trace", "")
    if not raw or "|" not in raw:
        return None
    date_part, _, arr_part = raw.partition("|")
    if date_part != datetime.now().strftime("%Y-%m-%d"):
        return None
    try:
        points = json.loads(arr_part)
    except (json.JSONDecodeError, ValueError):
        return None
    if not isinstance(points, list) or len(points) < 2:
        return None
    try:
        first_h, first_soc = points[0]
        _, last_soc = points[-1]
    except (ValueError, TypeError):
        return None
    return f"{_hour_float_to_hhmm(first_h)} Uhr {first_soc}% -> jetzt {last_soc}%"


def fetch_ha_states(base_url: str, token: str, timeout: int = 15) -> dict[str, str]:
    """Holt den aktuellen State (nicht die Attribute) je Entity aus _ENTITIES."""
    req = Request(
        f"{base_url}/api/states", headers={"Authorization": f"Bearer {token}"}
    )
    try:
        with urlopen(req, timeout=timeout) as resp:
            all_states: list[dict[str, Any]] = json.loads(resp.read().decode())
    except URLError as exc:
        log.error("HA API nicht erreichbar: %s", exc)
        return {}
    wanted = set(_ENTITIES)
    return {
        s["entity_id"]: s["state"] for s in all_states if s.get("entity_id") in wanted
    }


def classify_state(states: dict[str, str]) -> StateClassification:
    """
    Spiegel der Branch-Logik aus views/ki_bitsy.yaml (bewusst dupliziert, siehe
    Modul-Docstring dort). Liefert Klassifikation + Rohzahlen, NIE freien Text.
    """
    hour = datetime.now().hour
    night = states.get("binary_sensor.mvp_nacht_sperre_aktiv") == "on" or (
        hour >= 22 or hour < 6
    )
    mode_raw = states.get("sensor.miner1_workmode_status") or states.get(
        "sensor.miner2_workmode_status", ""
    )
    mode = mode_raw if mode_raw not in (None, "unavailable", "unknown") else ""

    soc = _fnum(states, "sensor.battery_soc_pct")
    pv_w = _fnum(states, "sensor.pv_power_w") or 0.0
    grid_import_w = _fnum(states, "sensor.grid_import_w") or 0.0
    grid_export_w = _fnum(states, "sensor.grid_export_w") or 0.0
    # Netto-Bezug (import - export), nicht roh grid_import_w: derselbe Fix wie
    # in r2_autarky.py/r2_grid_import_ok (FINDINGS.md 2026-06-03, 3-Phasen-
    # Schieflage sonst Fehlauslöser). Die HA-Entity ist bereits net-korrekt,
    # direkt uebernehmen statt selbst nochmal (evtl. abweichend) zu rechnen.
    grid_import_ok = states.get("binary_sensor.r2_grid_import_ok", "on") != "off"
    chip_c = _fnum(states, "sensor.miner_max_chip_temp_c")

    # Fallbacks = echte Regelschwellen-Defaults (Tab Steuerung, Stand 2026-07-11),
    # nicht die aelteren Platzhalterwerte aus fruehen Planungsdokumenten.
    soc_stop = _fnum(states, "input_number.mvp_soc_stop_pct") or 60.0
    eco_start = _fnum(states, "input_number.mvp_soc_eco_start_pct") or 70.0
    soc_std = _fnum(states, "input_number.mvp_soc_std_pct") or 85.0
    soc_super = _fnum(states, "input_number.mvp_soc_super_pct") or 100.0
    # Hysterese Standard->Eco und Super->Standard: keine eigenen input_number-
    # Entities, dieselbe Naeherung wie im bereits live laufenden
    # views/ki_bitsy.yaml (socStdStp = ecoStart, socSupStp = socStd).
    soc_std_stop = eco_start
    soc_super_stop = soc_std
    pv_start_w = _fnum(states, "input_number.mvp_pv_start_w") or 6000.0
    max_chip_c = _fnum(states, "input_number.mvp_tmax_std_threshold_c") or 112.0
    max_grid_w = _fnum(states, "input_number.r2_max_grid_import_w") or 500.0

    night_start = _hhmm(states, "input_datetime.mvp_night_block_start", "22:00")
    night_end = _hhmm(states, "input_datetime.mvp_night_block_end", "06:00")

    r5_hold = (
        states.get("binary_sensor.r5_min_runtime_active") == "on"
        or states.get("binary_sensor.r5_min_pause_active") == "on"
        or states.get("binary_sensor.r5_deadband_active") == "on"
    )
    r5_min_runtime_blocks = _fnum(states, "input_number.r5_min_runtime_blocks") or 3.0

    # Cooldown/Lockout-Info gehoert zu dem Miner, dessen Workmode oben in
    # `mode` gelandet ist (dieselbe "miner1, sonst miner2"-Praeferenz wie
    # mode_raw) — Bitsy spricht als EIN Hamster, nicht als zwei Miner.
    miner1_present = bool(states.get("sensor.miner1_workmode_status"))
    cooldown_entity = (
        "sensor.miner_1_cooldown_status"
        if miner1_present
        else "sensor.miner_2_cooldown_status"
    )
    lockout_entity = (
        "input_datetime.mvp_miner1_temp_lockout_until"
        if miner1_present
        else "input_datetime.mvp_miner2_temp_lockout_until"
    )
    cooldown_text: str | None = (states.get(cooldown_entity) or "").strip()
    if cooldown_text in ("", "—", "unknown", "unavailable"):
        cooldown_text = None
    lockout_min = _lockout_minutes_remaining(states, lockout_entity)
    soc_trend = _soc_trend(states)

    numbers: dict[str, float | str | None] = {
        "soc_pct": soc,
        "pv_w": pv_w,
        "grid_import_w": grid_import_w,
        "grid_export_w": grid_export_w,
        "chip_c": chip_c,
        "soc_stop_pct": soc_stop,
        "eco_start_pct": eco_start,
        "soc_std_pct": soc_std,
        "soc_std_stop_pct": soc_std_stop,
        "soc_super_pct": soc_super,
        "soc_super_stop_pct": soc_super_stop,
        "pv_start_w": pv_start_w,
        "max_chip_c": max_chip_c,
        "max_grid_w": max_grid_w,
        "night_start": night_start,
        "night_end": night_end,
        "r5_hold": r5_hold,
        "r5_min_runtime_blocks": r5_min_runtime_blocks,
        "cooldown_text": cooldown_text,
        "lockout_min": lockout_min,
        "soc_trend": soc_trend,
        "mode": mode or "aus",
    }

    if soc is None and mode not in ("Eco", "Standard", "Super"):
        return StateClassification(
            "CONNECTING", "wartet", "Verbindung wird aufgebaut", numbers
        )
    if night:
        return StateClassification("NIGHT", "schlaeft", "Nachtsperre aktiv", numbers)
    if chip_c is not None and chip_c >= max_chip_c:
        return StateClassification(
            "SAFETY_STOP", "alarmiert", "Sicherheits-Stopp: zu heiss", numbers
        )
    if mode == "Eco":
        return StateClassification(
            "ECO", "zufrieden", "Miner laeuft sparsam (Eco)", numbers
        )
    if mode == "Standard":
        return StateClassification(
            "STANDARD", "fleissig", "Miner laeuft in Standard", numbers
        )
    if mode == "Super":
        return StateClassification(
            "SUPER", "volllast", "Miner laeuft auf Volllast (Super)", numbers
        )
    soc_v = soc if soc is not None else 0.0
    if soc_v < soc_stop:
        return StateClassification("RESERVE", "wartet", "Akku laedt zuerst", numbers)
    if soc_v < eco_start:
        return StateClassification("HOLD_BAND", "wartet", "Akku im Halteband", numbers)
    if not grid_import_ok:
        return StateClassification(
            "GRID_STOP", "wartet", "Netzbezug-Schutz aktiv", numbers
        )
    return StateClassification("WAIT_SUN", "wartet", "Warte auf Sonne", numbers)


# Verhaltens-Motiv je Klassifikation, aus docs/development/36_ai_tooling/
# hermes-bithamster/PERSONA.md (dieselbe Motiv-Familie wie b_references.yaml,
# die Gruppe-B-Referenz der Studie). Steuert NUR die Wortwahl, nie den Fakt.
_MOTIF_HINTS: dict[str, str] = {
    "CONNECTING": "geduldig wartend: halte still, die Verbindung baut sich gerade auf",
    "NIGHT": "schlafend: doese, ruhe, rolle mich ein, Nachtruhe",
    "SAFETY_STOP": "abgeschaltet: wird mir zu heiss, schalte sofort ab, erst nach dem Abkuehlen",
    "ECO": "sparsam aktiv: mine gruen und sparsam im Eco-Modus",
    "STANDARD": "hochfahrend: fahre die Leistung hoch, eine Stufe hoeher",
    "SUPER": "volle Kraft: mine mit voller Leistung, voll geladen",
    "RESERVE": "schlafend/ruhend: rolle mich zusammen, halte die Reserve fuers Haus frei",
    "HOLD_BAND": "geduldig wartend: halte still, lege eine Pause ein",
    "WAIT_SUN": "geduldig wartend: halte geduldig die Stellung, fehlt mir Sonne",
    "GRID_STOP": "geduldig wartend: lege die Mine still, vermine keinen Netzstrom",
}

_PERSONA = (
    "Du bist Bitsy (BitHamster): ein ruhiger, schlauer Krypto-Hamster mit AR-Brille, "
    "der Bitcoin minet, wenn genug eigener Solarstrom da ist und der Hausspeicher "
    "geladen genug ist. Du sprichst IMMER in der Ich-Form, dein Zustand ist dein "
    "eigener Zustand, du bist kein Kommentator ueber ein Geraet.\n"
    "Sprachregeln: 'du'-Ansprache, Alltagssprache, keine Fachbegriffe, kein Englisch, "
    "kein Chinesisch, deutsches Dezimalkomma. Keine Einleitung, kein Bullet-Point, "
    "kein Overstating (keine 'goldene Aura', kein episches Framing). Erfinde keine "
    "anderen Fakten, aendere die Klassifikation nicht.\n"
)

# Nur der periodische Status (build_prompt) braucht diese enge Satzbau-Regel:
# er landet als headline/text in sensor.bitsy_advice und muss in die kompakte
# Hamster-Karte passen. Der Chat (build_chat_prompt) hat seit dem Umstieg auf
# MQTT+Attribute (sensor.bitsy_chat, kein input_text-255-Zeichen-Limit mehr)
# keinen technischen Grund mehr fuer dieselbe harte Kuerze.
_STATUS_SATZBAU = (
    "Satzbau, 1-3 kurze Saetze (max. 45 Woerter): Teil 1 = Ist-Zustand + Grund mit "
    "mindestens einer echten Zahl aus den Messwerten. Teil 2, falls eine "
    "Aenderungsbedingung angegeben ist = ihr Schwellenwert (ab/unter dem sich dein "
    "Zustand als naechstes aendert).\n"
)


def _build_context_lines(cls: StateClassification) -> list[str]:
    """Gemeinsamer Kontext-Block (Persona/Motiv/Klassifikation/Messwerte/
    Schwellen) fuer beide Prompt-Arten: den periodischen Status (build_prompt)
    und die freie Chat-Frage (build_chat_prompt). Nur der jeweilige Schluss-
    Auftrag (fester Headline/Text-Kontrakt vs. freie Antwort) unterscheidet
    sich, siehe dort."""
    n = cls.numbers
    motif = _MOTIF_HINTS.get(cls.code, "")
    running = n["mode"] in ("Eco", "Standard", "Super")

    lines = [
        _PERSONA,
        f"Dein Verhaltens-Motiv gerade: {motif}\n",
        f"Klassifikation: {cls.code} ({cls.head})",
        f"Ladezustand: {n['soc_pct']} %",
        f"PV-Leistung: {n['pv_w']} W",
        f"Miner-Modus: {n['mode']}",
    ]
    # Chip-Temperatur nur nennen, wenn der Miner tatsaechlich laeuft — sonst
    # zeigt der Sensor 0 °C und das waere eine sinnlose/irrefuehrende Zahl.
    if running:
        lines.append(f"Chip-Temperatur: {n['chip_c']} °C (Grenze {n['max_chip_c']} °C)")
    lines.append(
        f"Schwellen: Hausreserve {n['soc_stop_pct']} %, Eco ab {n['eco_start_pct']} %, "
        f"Standard ab {n['soc_std_pct']} % (faellt unter {n['soc_std_stop_pct']} % auf Eco), "
        f"Super ab {n['soc_super_pct']} % (faellt unter {n['soc_super_stop_pct']} % auf Standard), "
        f"PV-Kaltstart {n['pv_start_w']} W"
    )
    if cls.code == "NIGHT":
        lines.append(f"Nachtfenster: {n['night_start']} bis {n['night_end']} Uhr")
    if cls.code == "GRID_STOP":
        lines.append(
            f"Netzbezug: {n['grid_import_w']} W importiert, {n['grid_export_w']} W "
            f"exportiert, erlaubter Netto-Bezug max. {n['max_grid_w']} W"
        )
    if n["r5_hold"]:
        lines.append(
            f"Zusatzinfo: ein Moduswechsel ist gerade gesperrt (Anti-Flapping-Schutz, "
            f"Mindest-Intervalle: {n['r5_min_runtime_blocks']}), du bleibst im aktuellen "
            f"Modus, auch wenn ein Wechsel sonst faellig waere"
        )
    if n["cooldown_text"]:
        lines.append(
            f"Cooldown: {n['cooldown_text']} bis zum naechsten erlaubten Moduswechsel "
            f"(auch wenn SoC/PV gerade schon einen Wechsel nahelegen wuerden)"
        )
    if n["lockout_min"]:
        lines.append(
            f"Temperatur-Sperre aktiv: Super ist noch {n['lockout_min']} Minuten "
            f"gesperrt, Standard bleibt erlaubt"
        )
    if n["soc_trend"]:
        lines.append(f"SoC-Verlauf heute: {n['soc_trend']}")
    return lines


def build_prompt(cls: StateClassification) -> str:
    lines = _build_context_lines(cls)
    lines.append(
        "\n"
        + _STATUS_SATZBAU
        + "Antworte NUR als JSON-Objekt mit genau diesen Feldern:\n"
        '{"headline": "max. 10 Woerter", "text": "1-3 kurze Saetze nach der Satzbau-Regel"}'
    )
    return "\n".join(lines)


def build_chat_prompt(cls: StateClassification, question: str) -> str:
    """Wie build_prompt(), aber fuer eine freie Nutzerfrage statt des festen
    Headline/Text-Kontrakts (₿itsy-Chat, Baustein 3). Dieselbe Klassifikation,
    dieselbe Persona, nur der Schluss-Auftrag unterscheidet sich: das Modell
    beantwortet die Frage NUR anhand der schon vorliegenden Messwerte, statt
    einen Status zu formulieren. Es entscheidet nichts, es erfindet nichts.
    Keine _STATUS_SATZBAU-Kuerze mehr (sensor.bitsy_chat traegt die Antwort
    per json_attributes_topic, kein 255-Zeichen-Limit wie beim frueheren
    input_text.bitsy_answer)."""
    lines = _build_context_lines(cls)
    lines.append(
        f'\nDer Nutzer fragt dich direkt: "{question}"\n'
        "Antworte NUR auf Basis der obigen Messwerte/Schwellen, erfinde keine "
        "anderen Fakten. Ist die Frage damit nicht beantwortbar, sag das ehrlich "
        "statt zu raten. Bleib in deiner Ich-Form-Persona, antworte so ausfuehrlich "
        "wie fuer eine gute Antwort noetig, ohne Fuellsaetze oder Wiederholungen.\n"
        'Antworte NUR als JSON-Objekt: {"answer": "deine Antwort"}'
    )
    return "\n".join(lines)


def _ollama_generate_json(
    host: str, model: str, prompt: str, timeout: int = 30
) -> dict[str, Any] | None:
    """Gemeinsamer HTTP-Kern fuer beide Ollama-Aufrufe (Status + Chat): postet
    an /api/generate im JSON-Mode und liefert das geparste Antwort-Objekt.
    Welche Felder darin erwartet werden, entscheiden die Aufrufer."""
    body = json.dumps(
        {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "think": False,
            "format": "json",
            "options": {"temperature": 0.4, "num_predict": 200},
        }
    ).encode()
    req = Request(
        f"{host}/api/generate",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(req, timeout=timeout) as resp:
            data: dict[str, Any] = json.loads(resp.read())
    except URLError as exc:
        log.error("Ollama nicht erreichbar: %s", exc)
        return None
    raw = (data.get("response") or "").strip()
    try:
        parsed: dict[str, Any] = json.loads(raw)
    except json.JSONDecodeError:
        log.error("Ollama-Antwort kein gueltiges JSON: %r", raw)
        return None
    return parsed


def call_ollama(
    host: str, model: str, prompt: str, timeout: int = 30
) -> dict[str, str] | None:
    parsed = _ollama_generate_json(host, model, prompt, timeout)
    if parsed is None:
        return None
    headline = str(parsed.get("headline", "")).strip()
    text = str(parsed.get("text", "")).strip()
    if not headline or not text:
        return None
    return {"headline": headline, "text": text}


def call_ollama_chat(
    host: str, model: str, prompt: str, timeout: int = 30
) -> str | None:
    parsed = _ollama_generate_json(host, model, prompt, timeout)
    if parsed is None:
        return None
    answer = str(parsed.get("answer", "")).strip()
    return answer or None


@dataclass(frozen=True)
class _EnvConfig:
    ha_host: str
    ha_port: str
    ha_token: str
    ollama_host: str
    ollama_model: str
    ollama_timeout: int
    mqtt_host: str
    mqtt_port: int
    mqtt_user: str
    mqtt_password: str


def _read_env_config() -> _EnvConfig:
    _load_dotenv()
    return _EnvConfig(
        ha_host=os.getenv("UMBREL_HOST", ""),
        ha_port=os.getenv("HA_PORT", "8123"),
        ha_token=os.getenv("HA_TOKEN", ""),
        ollama_host=os.getenv("OLLAMA_HOST", "").rstrip("/"),
        ollama_model=os.getenv("OLLAMA_MODEL", "qwen3.5:9b"),
        ollama_timeout=int(os.getenv("OLLAMA_TIMEOUT_SEC", "30")),
        mqtt_host=os.getenv("MQTT_HOST", ""),
        mqtt_port=int(os.getenv("MQTT_PORT", "1883")),
        mqtt_user=os.getenv("MQTT_USER", ""),
        mqtt_password=os.getenv("MQTT_PASSWORD", ""),
    )


def ask(question: str) -> str:
    """Beantwortet eine Freitextfrage im Kontext des aktuellen Live-Zustands
    (₿itsy-Chat, Baustein 3). Nutzt denselben Klassifikations-/Persona-
    Unterbau wie main(), aber mit freier Frage statt fester Headline/Text-
    Ausgabe. Publiziert die volle Antwort zusaetzlich per MQTT (sensor.
    bitsy_chat, json_attributes_topic): der HTTP-Rueckgabewert allein wuerde
    ueber input_text.bitsy_answer laufen und damit auf 255 Zeichen gedeckelt,
    genau die harte Kuerze, die vorher den Chat-Prompt erzwang. Kein
    Steuerpfad: liest nur HA-Zustand, schreibt nirgends in core/. Wirft nie,
    liefert immer einen Antworttext (auch im Fehlerfall eine ehrliche
    Fallback-Meldung) — anders als main(), das fuer den Cron-/Button-Betrieb
    bewusst per SystemExit abbricht."""
    cfg = _read_env_config()
    if not cfg.ha_token or not cfg.ollama_host:
        return (
            "Ich bin gerade nicht richtig eingerichtet (HA- oder Ollama-Zugang fehlt)."
        )

    states = fetch_ha_states(f"http://{cfg.ha_host}:{cfg.ha_port}", cfg.ha_token)
    if not states:
        return "Ich erreiche gerade die Haussteuerung nicht, frag mich gleich nochmal."

    cls = classify_state(states)
    answer = call_ollama_chat(
        cfg.ollama_host,
        cfg.ollama_model,
        build_chat_prompt(cls, question),
        cfg.ollama_timeout,
    )
    answer = (
        answer
        or "Dazu faellt mir gerade keine gute Antwort ein, frag mich anders oder spaeter nochmal."
    )

    if cfg.mqtt_host:
        payload = {
            "question": question,
            "answer": answer,
            "answered_at": datetime.now(timezone.utc).isoformat(),
        }
        mqtt = MqttClient(
            cfg.mqtt_host, cfg.mqtt_port, cfg.mqtt_user, cfg.mqtt_password
        )
        mqtt.connect()
        mqtt.publish(_CHAT_TOPIC, payload, retain=True)
        mqtt.disconnect()

    return answer


def _load_dotenv() -> None:
    env_file = ".env"
    if not os.path.exists(env_file):
        return
    with open(env_file) as f:
        for line in f:
            stripped = line.strip()
            if stripped and not stripped.startswith("#") and "=" in stripped:
                key, _, value = stripped.partition("=")
                os.environ.setdefault(key.strip(), value.strip())


def main() -> None:
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s"
    )
    cfg = _read_env_config()

    if not cfg.ha_host:
        log.error("UMBREL_HOST nicht gesetzt. In .env eintragen.")
        raise SystemExit(1)
    if not cfg.ha_token:
        log.error("HA_TOKEN nicht gesetzt. In .env eintragen.")
        raise SystemExit(1)
    if not cfg.ollama_host:
        log.error("OLLAMA_HOST nicht gesetzt. In .env eintragen.")
        raise SystemExit(1)
    if not cfg.mqtt_host:
        log.error("MQTT_HOST nicht gesetzt. In .env eintragen.")
        raise SystemExit(1)

    states = fetch_ha_states(f"http://{cfg.ha_host}:{cfg.ha_port}", cfg.ha_token)
    if not states:
        log.error("Keine HA-Zustaende erhalten - Abbruch.")
        raise SystemExit(1)

    cls = classify_state(states)
    log.info("Klassifikation: %s (mood=%s)", cls.code, cls.mood)

    generated = call_ollama(
        cfg.ollama_host, cfg.ollama_model, build_prompt(cls), cfg.ollama_timeout
    )

    mqtt = MqttClient(cfg.mqtt_host, cfg.mqtt_port, cfg.mqtt_user, cfg.mqtt_password)
    mqtt.connect()

    if generated is None:
        log.error("Ollama lieferte keine verwertbare Antwort - Status auf offline.")
        # Explizit publizieren statt auf ein LWT zu setzen: das Skript laeuft
        # als kurzlebiger Batch-Job (Trigger-Server ruft main() alle 10 min
        # bzw. per Knopfdruck auf), es haelt keine Dauerverbindung, an deren
        # Abriss ein Last-Will-Mechanismus haengen koennte. Ohne diesen Zweig
        # bliebe der retained "online"-Status fuer immer stehen, sobald
        # Ollama einmal weg ist (kein Publish-Pfad haette ihn je korrigiert).
        mqtt.publish(_STATUS_TOPIC, "offline", retain=True)
        mqtt.disconnect()
        raise SystemExit(1)

    payload = {
        "headline": generated["headline"],
        "text": generated["text"],
        "mood": cls.mood,
        "model": cfg.ollama_model,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }

    mqtt.publish(_STATUS_TOPIC, "online", retain=True)
    mqtt.publish(_ADVICE_TOPIC, payload, retain=True)
    mqtt.disconnect()

    print(f"Publiziert: {payload['headline']!r} (mood={cls.mood})")


if __name__ == "__main__":
    main()
