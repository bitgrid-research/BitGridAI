# 8.7 - Logging, Events & Monitoring

Was passiert – und woher wissen wir das?

BitGridAI ist ein autonomes, verteiltes System, das reale Energieflüsse und Hardware steuert.  
Damit Entscheidungen nachvollziehbar, Fehler analysierbar und der Betrieb sicher bleibt, benötigt das System eine **einheitliche Strategie für Logging, Events und Monitoring**.

Dieses Kapitel beschreibt die **übergreifenden Prinzipien**, nach denen BitGridAI Beobachtbarkeit herstellt – nicht als Zusatz, sondern als festen Bestandteil der Architektur.

*(Platzhalter für ein Bild: Ein Pixel-Art-Hamster sitzt vor einer großen Wand aus Monitoren mit Anzeigen wie „Health“, „Events“, „Safety“. Ein Logbuch liegt offen daneben.)*
![Hamster überwacht das System](../../media/pixel_art_hamster_monitoring.png)

&nbsp;

## Ziel der Beobachtbarkeit

Logging und Monitoring verfolgen in BitGridAI vier Hauptziele:

1. **Nachvollziehbarkeit**  
   Entscheidungen und Zustandsänderungen sind erklärbar und auditierbar.

2. **Fehleranalyse**  
   Störungen lassen sich reproduzieren und eingrenzen.

3. **Betriebssicherheit**  
   Ausfälle und Degradation werden frühzeitig sichtbar.

4. **Transparenz für den Nutzer**  
   Das System zeigt offen, was es tut – und warum.

&nbsp;

## Grundprinzipien

- **Events sind semantisch**  
  Wo möglich werden strukturierte Events erzeugt, nicht nur Textlogs.

- **Warum ist ein First-Class-Attribut**  
  Entscheidungen enthalten immer eine Begründung (Reason-Code + Kontext).

- **Keine stillen Zustände**  
  Safety-Eingriffe, Degradation und Fehler sind immer sichtbar.

- **Append-only für relevante Historie**  
  Entscheidungs- und Safety-Events werden nicht überschrieben.

- **Local-first**  
  Logs verbleiben standardmäßig lokal; es gibt keine Pflicht-Telemetrie.

&nbsp;

## Event-Kategorien

BitGridAI unterscheidet systemweit mehrere Event-Typen:

### Decision Events
Dokumentieren Entscheidungen der Rule Engine (R1–R5).

Typische Inhalte:
- Aktion (Start, Stop, Hold, …)
- beteiligte Regeln
- Reason-Code
- auslösende Metriken

&nbsp;

### Safety Events
Dokumentieren Eingriffe der Sicherheitslogik (R3).

Beispiele:
- Übertemperatur
- fehlende Pflichtsignale
- Kommunikationsabbruch

Safety Events haben:
- höchste Priorität
- klare, knappe Begründung
- sofortige Sichtbarkeit

&nbsp;

### Health Events
Beschreiben den Zustand von Komponenten und Abhängigkeiten.

Beispiele:
- Adapter degraded
- MQTT unreachable
- DB error
- Config invalid

Health Events sind Grundlage für:
- Monitoring
- Degradationslogik (Kap. 8.6)
- UI-Statusanzeigen

&nbsp;

### Audit Events
Dokumentieren sicherheits- und governance-relevante Aktionen.

Beispiele:
- Override gesetzt / abgelaufen
- Authentifizierung fehlgeschlagen
- Rate-Limit erreicht
- Config-Reload erfolgreich / fehlgeschlagen
- Research-Export erstellt

&nbsp;

## Log-Level

Logs sind für Menschen, Events für Systeme – beides ergänzt sich.

Verwendete Ebenen:

- **DEBUG** – Detaildiagnostik (Entwicklung)
- **INFO** – Normalbetrieb, relevante Zustandswechsel
- **WARN** – Degradation, Grenzfälle, Limits
- **ERROR** – Ausfall von Pflichtkomponenten
- **CRITICAL** – Safety Stop, akute Gefahrenlage

&nbsp;

## Health-Status (einheitliche Semantik)

BitGridAI nutzt einen konsistenten Health-Begriff:

- **`ok`**  
  Voller Betrieb möglich.

- **`warn`**  
  Betrieb möglich, aber eingeschränkt oder degradiert.

- **`error`**  
  Pflichtfunktionen nicht verfügbar, Fail-safe aktiv.

Health ist:
- extern beobachtbar (UI, Monitoring)
- Trigger für Fail-safe-Logik
- Grundlage für Alerts

&nbsp;

## Sichtbarkeit im UI

Für Nutzer gilt:

- aktueller Health-Status ist jederzeit sichtbar
- aktive Safety-Zustände sind prominent
- letzte Entscheidung ist einsehbar (inkl. Begründung)
- aktive Overrides werden inkl. TTL angezeigt

Der Nutzer soll jederzeit verstehen:
> *Was passiert – und warum?*

&nbsp;

## Aufbewahrung & Rotation

Logs und Events unterliegen klaren Regeln:

- operative Logs: rotierend, zeitlich begrenzt
- Entscheidungs- & Safety-Events: historisch, append-only
- Research-Daten: nur per Opt-in exportierbar

Bei knappem Speicher:
- frühzeitige Warnung
- kontrollierte Rotation
- keine stille Datenkorruption

&nbsp;

## Abgrenzungen

Nicht Bestandteil dieses Kapitels sind:
- konkrete Monitoring-Tools oder Dashboards
- Log-Formate je Datei
- Alerting-Regeln im Detail

Diese Themen gehören in Betriebs- oder Entwicklerdokumentation.

&nbsp;

## Zusammenfassung

Logging, Events und Monitoring sind integraler Bestandteil der Architektur von BitGridAI.

Sie stellen sicher, dass:
- Entscheidungen nachvollziehbar bleiben,
- Fehler früh sichtbar werden,
- der Betrieb kontrollierbar ist.

BitGridAI arbeitet nicht im Verborgenen –  
es macht sein Verhalten sichtbar.

---

> **Nächster Schritt:** Beobachtbarkeit ist die Basis für Vertrauen – aber erst durch Tests wird Verhalten beweisbar.  
> Im nächsten Kapitel betrachten wir **Testbarkeit, Simulation & Replays**.
>
> 👉 Weiter zu **[8.8 Testbarkeit, Simulation & Replays](./088_testability_and_simulation.md)**
>
> 🔙 Zurück zur **[Kapitelübersicht](./README.md)**
