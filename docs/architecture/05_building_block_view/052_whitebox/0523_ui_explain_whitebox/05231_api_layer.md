# 05.2.3.1 API-Layer

Der Empfangsschalter von BitGridAI.

Der API-Layer stellt die **lokalen REST- und WebSocket-Schnittstellen** bereit.
Er ist der einzige Weg, über den UIs, Tools oder Nutzer mit dem System sprechen.
Lesen ist günstig. Schreiben ist kontrolliert.

*(Platzhalter für ein Bild: Der Hamster sitzt an einem Tresen.
Schilder: „State“, „Timeline“, „Preview“, „Override (mit Ausweis)“.)*
![Hamster am API-Schalter](../media/pixel_art_api_layer.png)

&nbsp;

## Scope

- Lokale REST- und WebSocket-Endpunkte
- Zugriffskontrolle (lokal, optional Auth)
- Rate-Limiting für schreibende Aktionen
- Stabile, versionierte Payloads für UI und Tools

&nbsp;

## Struktur

- **REST Handler**  
  Endpunkte `GET /state`, `GET /timeline`, `GET /preview`,  
  `POST /override`, `POST /research/export`.

- **WebSocket Hub**  
  Broadcastet State-, Decision- und Explain-Events; verwaltet Sessions.

- **Auth & Rate Limits**  
  Optionaler Token-Check; verpflichtende Rate-Limits für Writes.

- **Serializer / DTOs**  
  Stabile Payload-Schemas (`EnergyState`, `DecisionEvent`, `ExplainSession`).

&nbsp;

## Schnittstellen

**Provided**
- REST/WS für State, Timeline, Preview, Overrides und Exporte
- Event-Streams (Decision, Explain, Health) für UI und Tools

**Required**
- State- und DecisionEvent-Streams aus dem Core
- Preview-Service (Sandbox)
- Override Handler
- Export-/Research-Service
- Optional: Auth-Backend

&nbsp;

## Ablauf (vereinfacht)

1) Client ruft `GET /state` oder `GET /timeline` ab → Snapshot.  
2) Client verbindet sich per WebSocket → Live-Events.  
3) Client sendet Override → Auth + Rate-Limit → Override Handler → Bestätigung.  
4) Client sendet Preview → Preview-Service → hypothetisches Ergebnis.

&nbsp;

## Qualitäts- und Betriebsaspekte

- **Local-only:** keine externe Exposition, keine Cloud-Abhängigkeit.  
- **Write-Schutz:** Rate-Limits und Validierung für `/override` und `/export`.  
- **Stabilität:** versionierte DTOs; Breaking Changes nur mit neuer API-Version.  
- **Robustheit:** Backpressure im WS-Hub, Drop-Policy bei Überlast, Health-Events.

---
> **Nächster Schritt:**  
> Der Empfang ist geklärt. Im nächsten Baustein schauen wir uns an,  
> **wie diese Schnittstellen visuell genutzt werden** – das eigentliche Cockpit für den Nutzer.
>
> 👉 Weiter zu **[5.2.3.2 Web-UI](./05232_web_ui.md)**
>
> 🔙 Zurück zur **[5.2.3 Whitebox UI & Explainability](./README.md)**
> 
> 🏠 Zurück zur **[5.2 Level-2-Whiteboxes](../README.md)**


