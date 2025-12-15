# 05.2.3.1 API-Layer

Verantwortung: stellt lokale REST/WS-Schnittstellen fuer State, Timeline, Overrides, Preview/What-if und Research-Opt-in bereit; sichert Zugriffe (lokal, optional Auth) und rate-limitiert schreibende Operationen.

## Struktur

- **REST Handler:** Endpunkte `GET /state`, `GET /timeline`, `GET /preview`, `POST /override`, `POST /research/export`.
- **WebSocket Hub:** broadcastet State-, Decision- und Explain-Events; verwaltet Sessions.
- **Auth & Rate Limits:** optionaler Token-Check, Write-Rate-Limits fuer `/override`/`/export`.
- **Serializer/DTOs:** stellt stabile Payload-Schemas bereit (z.B. `DecisionEvent`, `EnergyState`).

## Schnittstellen

- **Provided:** REST/WS fuer State/Timeline/Preview/Override/Export, Events (Decision/Explain/Health) an UI.
- **Required:** State/DecisionEvent-Streams aus Core, Preview-Service, Override Handler, Export-Service, optional Auth-Backend.

## Ablauf (vereinfacht)

1) Client ruft State/Timeline ab -> REST Handler liefert Snapshot.  
2) Client abonniert WS -> erhaelt laufende State-/Decision-/Explain-Events.  
3) Client sendet Override -> Auth/Rate Limit -> Weiterleitung an Override Handler -> Bestaetigung zurueck.  
4) Client sendet Preview -> API ruft Preview-Service -> Antwort mit hypothetischem Outcome.

## Qualitaet und Betrieb

- Nur lokal exposed; Auth optional, aber Rate-Limits fuer Writes Pflicht.  
- Stabile DTOs/versionierte Payloads; Breaking Changes mit Versionspfad.  
- Backpressure im WS-Hub, Drop-Policy bei Ueberlast, Health-Events bei Abwurf.

---
> Zurueck zu **[5.2.3.x UI und Explainability (Level 3)](./README.md)**  
> Zurueck zu **[5.2.3 Whitebox UI und Explainability](../0523_ui_explain_whitebox.md)**
