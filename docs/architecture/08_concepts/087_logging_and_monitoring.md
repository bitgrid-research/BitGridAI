# 8.7 Logging, Events & Monitoring

Was ist passiert – und warum?

BitGridAI ist ein autonomes, deterministisches System.  
Damit Entscheidungen nachvollziehbar, Fehler analysierbar und der Betrieb kontrollierbar bleibt, braucht es eine einheitliche Strategie für **Logs, Events und Monitoring**.

Dieses Kapitel beschreibt die **systemweiten Regeln** dafür:
- was protokolliert wird,
- in welcher Form es veröffentlicht wird,
- und wie „Gesundheit“ des Systems sichtbar gemacht wird.

*(Platzhalter für ein Bild: Ein Pixel-Art-Hamster mit Taschenlampe schaut in ein großes Logbuch. Daneben blinken kleine Anzeigen „Health“, „Events“, „Audit“.)*  
![Hamster liest die Systemspuren](link_zum_logging_hamster.png)

---

## Ziele

Logging und Monitoring in BitGridAI dienen vier Hauptzwecken:

1. **Auditierbarkeit**  
   Entscheidungen und sicherheitsrelevante Aktionen sind nachträglich überprüfbar.

2. **Debuggability**  
   Fehler lassen sich reproduzieren und eingrenzen (insbesondere mit Replays).

3. **Transparenz**  
   Nutzer und Operatoren sehen, was das System tut und warum.

4. **Betriebssicherheit**  
   Ausfälle, Degradation und Grenzzustände werden früh sichtbar.

---

## Grundprinzipien

- **Events sind semantisch, nicht nur textuell**  
  Wo möglich werden strukturierte Events erzeugt, nicht nur freie Log-Zeilen.

- **Warum ist ein First-Class-Attribut**  
  Entscheidungen werden immer mit Begründung/Reason erfasst.

- **Keine stillen Aktionen**  
  Safety/Stop, Degradation, abgelehnte Requests und Config-Fails sind immer sichtbar.

- **Append-only für relevante Historie**  
  Entscheidungs- und Safety-Ereignisse werden nicht überschrieben.

- **Local-first**  
  Logs bleiben standardmäßig lokal (kein Telemetrie-Abfluss).

---

## Event-Typen

BitGridAI unterscheidet systemweit mehrere Event-Kategorien:

### Decision Events
Dokumentieren Entscheidungen der Rule Engine.

Enthalten typischerweise:
- Aktion (Start/Stop/Hold/…)
- beteiligte Regeln (R1–R5)
- Reason-Code
- Trigger-Metriken (auslösende Werte)

### Safety Events
Dokumentieren Eingriffe der Safety-Logik (R3).

Beispiele:
- Übertemperatur
- fehlende Pflichtsignale
- Kommunikationsverlust

Safety Events haben immer:
- hohe Priorität
- klare, knappe Begründung
- Sichtbarkeit in UI und Monitoring

### Health Events
Dokumentieren den Zustand von Abhängigkeiten und Komponenten.

Beispiele:
- MQTT unreachable
- Adapter degraded
- DB error
- Config invalid

Health Events sind Grundlage für:
- Statusanzeigen
- Alerts
- Degradationslogik (Kap. 8.6)

### Audit Events
Dokumentieren sicherheits- und governance-relevante Vorgänge.

Beispiele:
- Auth failed / rate limited
- Override gesetzt/abgelaufen
- Config reload success/fail
- Research export erstellt

---

## Log-Ebenen

Logs sind für Menschen, Events für Systeme.  
Beides ergänzt sich.

Empfohlene Log-Ebenen:

- **DEBUG**: Detaildiagnostik (nur für Entwicklung)
- **INFO**: Normalbetrieb, wichtige Zustandswechsel
- **WARN**: Degradation, nicht-kritische Fehler, Limits erreicht
- **ERROR**: Ausfall von Pflichtkomponenten, Abbruchpfade
- **CRITICAL**: Safety Stop / gefährliche Zustände

---

## Health-Status (systemweite Semantik)

BitGridAI nutzt einen konsistenten Health-Begriff, der nach außen sichtbar ist.

- `ok`  
  Betrieb vollständig möglich.

- `warn`  
  Betrieb möglich, aber degradiert oder mit Einschränkungen.

- `error`  
  Pflichtabhängigkeiten fehlen, nur Minimalbetrieb oder Fail-safe.

Health ist:
- extern beobachtbar (UI/Monitoring)
- Quelle für Degradationsentscheidungen (Kap. 8.6)
- Grundlage für Betrieb/Alarmierung

---

## Sichtbarkeit im UI (Transparenz)

Für Nutzer ist entscheidend:

- „Was passiert?“ (Status)
- „Warum passiert es?“ (Reason)
- „Was ist die Konsequenz?“ (z.B. Safe/Stop)

Daher gelten Mindestanforderungen:
- aktive Safety-Zustände sind prominent
- Overrides sind sichtbar (inkl. TTL)
- die letzte relevante Entscheidung ist abrufbar (inkl. Trigger-Werte)

---

## Aufbewahrung & Rotation

Logs und Events folgen den Leitlinien aus Kapitel 8.3:

- operative Logs: rotierend, begrenzte Haltedauer
- relevante Events: append-only / historisch
- Forschung: Export nur per Opt-in

Low-Disk-Situationen führen zu:
- Warnungen/Events
- kontrollierter Rotation
- niemals zu stiller Datenkorruption

---

## Abgrenzungen

Nicht Bestandteil dieses Kapitels sind:
- konkrete Tooling-Wahl (Prometheus, Grafana, etc.)
- konkrete Log-Formate je Datei
- Dashboard-Designs

Diese Details gehören in Betriebs- oder Entwicklerdokumentation.

---

## Zusammenfassung

Logging, Events und Monitoring sind in BitGridAI kein „Nebengeräusch“, sondern Teil der Architektur.

Sie stellen sicher, dass:
- Entscheidungen nachvollziehbar bleiben,
- Fehler früh sichtbar werden,
- der Betrieb kontrolliert und auditierbar ist.

BitGridAI arbeitet nicht im Verborgenen – es hinterlässt Spuren mit Bedeutung.

---

> **Nächster Schritt:** Wenn wir das System beobachten können, wollen wir es auch reproduzierbar testen.  
> Im nächsten Abschnitt betrachten wir **Testbarkeit, Simulation & Replays**.
>
> 👉 Weiter zu **[8.8 Testbarkeit, Simulation & Replays](./088_testability_and_simulation.md)**
>
> 🔙 Zurück zur **[Kapitelübersicht](./README.md)**
