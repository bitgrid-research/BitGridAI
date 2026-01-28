# 23 – Systemmodell & Entscheidungslogik

Dieses Kapitel beschreibt das **konzeptionelle Systemmodell** sowie die **Entscheidungslogik**, die das Verhalten des Systems bestimmt.
Der Fokus liegt auf **Zuständen, Datenflüssen und Regeln**, nicht auf konkreten Implementierungsdetails oder Softwarearchitektur.

Technische Details (z. B. Module, Schnittstellen, Deployment) sind bewusst ausgelagert und in der
[Architekturübersicht](../../architecture/README.md) dokumentiert.

&nbsp;

## Ziel des Systemmodells

Das Systemmodell verfolgt drei zentrale Ziele:

1. **Trennung von Wahrnehmung, Entscheidung und Aktion**
   Messwerte sollen nicht direkt zu Schaltvorgängen führen.
2. **Stabile, vorhersehbare Entscheidungen**
   Entscheidungen werden bewusst selten und blockbasiert getroffen.
3. **Vollständige Erklärbarkeit**
   Jede Entscheidung – einschließlich bewussten Nicht-Handelns – ist regelbasiert begründbar.

Das Modell dient damit als **konzeptionelle Grundlage** für UX, Explainability und Evaluation.

&nbsp;

## Systemmodell: Komponenten & Datenflüsse (konzeptionell)

Das System ist als **mehrstufiges Entscheidungsmodell** aufgebaut:

```
Messungen
   ↓
Regelzustände (R1–R5)
   ↓
Entscheidung (START / STOP / NOOP / THROTTLE)
   ↓
Aktion (optional)
   ↓
Systemzustand (z. B. OFF, RUNNING)
   ↓
Logging & Analyse
```

### Zentrale Komponenten (abstrakt)

* **Mess-Ebene**
  Erfasst Zustands- und Telemetriedaten (z. B. PV, SoC, Temperatur).
* **Regel-Ebene**
  Bewertet Messungen anhand expliziter Regeln (R1–R5).
* **Entscheidungs-Ebene**
  Trifft diskrete Entscheidungen in festen Zeitintervallen.
* **Aktions-Ebene**
  Führt Entscheidungen physisch aus (Start, Stop, Drosselung).
* **Zustands-Ebene**
  Repräsentiert den aktuellen, nutzerrelevanten Systemzustand.
* **Logging- & Analyse-Ebene**
  Dokumentiert Entscheidungen, Gründe und kontrafaktische Alternativen.

Diese Trennung verhindert direkte Kopplungen zwischen Messrauschen und Aktorverhalten.

&nbsp;

## Zustandsmodell

Das System kennt mehrere **explizite Zustandsklassen**, die unterschiedliche Ebenen abbilden.

### System-/Gerätezustände (nutzerrelevant)

* **OFF** – System inaktiv
* **ARMED** – Start erlaubt, wartet auf Entscheidungszeitpunkt
* **RUNNING** – Aktive Laufphase
* **THROTTLED** – Reduzierter Betrieb aus Schutzgründen
* **COOLDOWN** – Zwangspause nach Sicherheitsereignis
* **LOCKOUT** – Sicherheitsblockade

Zu jedem Zeitpunkt ist **genau ein Zustand aktiv**.

&nbsp;

## Entscheidungslogik: Regeln, Trigger und Stabilität

### Regelbasierte Entscheidungsfindung (R1–R5)

Die Entscheidungslogik basiert auf einem festen Satz expliziter Regeln:

* **R1 – Startregel**
  Bewertung von Überschuss- und Kontextbedingungen.
* **R2 – Speicher- und Autarkieschutz**
  Verhindert kritische Entladung.
* **R3 – Sicherheits- und Thermoschutz**
  Greift unabhängig vom Entscheidungstakt.
* **R4 – Prognose- und Stabilitätsbewertung**
  Verhindert Starts bei unsicherer Datenlage.
* **R5 – Deadband / Anti-Flapping**
  Erzwingt Mindestlauf- und Mindestpausenzeiten.

Die Regeln erzeugen **Regelzustände**, aus denen eine Entscheidung abgeleitet wird.

&nbsp;

### Entscheidungszeitpunkte (Blocklogik)

* Entscheidungen werden in **diskreten Zeitintervallen** (z. B. 10-Minuten-Blöcken) getroffen.
* Pro Block existiert **genau eine Entscheidung**:

  * `START`
  * `STOP`
  * `THROTTLE`
  * `NOOP` (bewusstes Nicht-Handeln)

Sicherheitsrelevante Eingriffe (R3) können den Blockrhythmus **asymmetrisch unterbrechen**.

&nbsp;


## Einordnung

Das Systemmodell bildet die **konzeptionelle Klammer** zwischen:

* den Annahmen und Grenzen (Kapitel 22),
* dem Erklärungsmodell (Kapitel 24),
* und der späteren Evaluation.

Es stellt sicher, dass Entscheidungen **stabil, erklärbar und reproduzierbar** sind, bevor Optimierungsfragen betrachtet werden.

---

> **Nächster Schritt:** Das Systemmodell ist definiert.
> Im nächsten Kapitel wird das Erklärungsmodell beschrieben.
>
> 👉 Weiter zu **[24 - Erklärungsmodell](../24_explanation_model/README.md)**
>
> 🔙 Zurück zu **[2 - Forschung](../README.md)**
>
> 🏠 Zurück zur **[Hauptübersicht](../../README.md)**
