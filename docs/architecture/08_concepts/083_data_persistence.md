# 8.3 - Datenhaltung & Datenlebenszyklus

Das Gedächtnis des Systems.

BitGridAI arbeitet **local-first**.  
Es gibt keine Cloud-Datenbank, die Zustände oder Entscheidungen automatisch sichert.  
Persistenz ist daher kein technisches Detail, sondern ein **zentrales Architekturthema**.

Dieses Kapitel beschreibt, **wie BitGridAI Daten systemweit behandelt**:
von der Entstehung über die Nutzung bis hin zu Archivierung, Export oder Löschung.

Ziel ist eine Datenhaltung, die:
- deterministisch,
- auditierbar,
- ressourcenschonend
- und nutzerkontrolliert ist.

*(Platzhalter für ein Bild: Ein Pixel-Art-Hamster als Bibliothekar, der Bücher in ein Regal („SQLite“) sortiert und große Kisten in ein Archiv („Parquet“) stapelt.)*  
![Hamster sortiert Daten](../../media/bithamster_08.png)

&nbsp;

## Grundprinzipien

Die Datenhaltung von BitGridAI folgt fünf übergreifenden Prinzipien:

1. **Local-first & Privacy-by-Default**  
   Alle Daten verbleiben standardmäßig auf dem lokalen Host.

2. **Zweckgetrennte Speicherung**  
   Laufzeitdaten, Entscheidungsprotokolle und Forschungsdaten werden unterschiedlich behandelt.

3. **Append-only für relevante Historie**  
   Entscheidungen und Logs werden nicht überschrieben, sondern fortgeschrieben.

4. **Expliziter Lebenszyklus**  
   Jede Datenart hat eine klar definierte Rolle und Haltedauer.

5. **Opt-in für Exporte**  
   Daten verlassen das System ausschließlich bewusst und nachvollziehbar.

&nbsp;

## Die hybride Speicherstrategie

BitGridAI nutzt bewusst einen **hybriden Ansatz**, der unterschiedliche Speichertechnologien nach ihrem Zweck einsetzt.

| Datenkategorie | Charakter | Rolle im System |
| --- | --- | --- |
| **Operative Laufzeitdaten (Hot Data)** | flüchtig, schnell | aktueller Zustand, UI, Betrieb |
| **Entscheidungs- & Ereignisdaten** | append-only, erklärend | Audit, Explainability |
| **Historische & Forschungsdaten (Cold Data)** | langfristig, komprimiert | Analyse, Replay |
| **Konfigurationsdaten** | versioniert, nachvollziehbar | Rahmenbedingungen |

Diese Trennung ist Grundlage für Performance, Reproduzierbarkeit und Datensouveränität.

&nbsp;

## Laufzeitdaten (Hot Data)

Laufzeitdaten sind notwendig, um das System **jetzt** zu betreiben.

**Beispiele:**
- aktueller `EnergyState`
- aktive Overrides
- UI-Zustände
- kurzfristige KPIs

**Eigenschaften:**
- häufige Lese-/Schreibzugriffe
- begrenzter Umfang
- ersetzbar durch neuere Zustände

Diese Daten ermöglichen einen schnellen Neustart, sind aber **nicht die alleinige Wahrheit** für Analyse oder Audit.

&nbsp;

## Entscheidungs- & Ereignisdaten (Append-only)

Diese Daten dokumentieren, **was entschieden wurde – und warum**.

**Beispiele:**
- Decision Events
- Safety Events
- Health Events
- Konfigurationsänderungen (als Ereignis)

**Eigenschaften:**
- strikt append-only
- zeitlich geordnet
- nicht nachträglich veränderbar

Sie bilden die Grundlage für:
- Explainability
- Auditierbarkeit
- Replays

&nbsp;

## Historische & Forschungsdaten (Cold Data)

Cold Data dient Analyse, Simulation und Forschung.

**Beispiele:**
- historische Zustandsverläufe
- Entscheidungs-Historien
- Explain-Sessions

**Eigenschaften:**
- schreibarm
- leselastig
- langfristig haltbar
- effizient verdichtbar

Diese Daten werden bewusst getrennt vom operativen Betrieb gehalten.

&nbsp;

## Konfigurationsdaten als Teil der Historie

Konfiguration ist Teil der fachlichen Wahrheit.

**Grundsätze:**
- Konfiguration ist versioniert
- Änderungen sind nachvollziehbar
- relevante Änderungen werden als Ereignisse erfasst

So ist bei Replays klar:
> *Welche Regeln galten zu welchem Zeitpunkt?*

&nbsp;

## Datenlebenszyklus

Der typische Lebenszyklus eines Datums ist:

1. **Entstehung**  
   Messung, Ableitung oder Entscheidung.

2. **Operative Nutzung**  
   Regelbewertung, UI, Explain.

3. **Persistenz**  
   Speicherung gemäß Datenkategorie.

4. **Verdichtung / Archivierung**  
   Reduktion oder Zusammenfassung älterer Daten.

5. **Export oder Löschung**  
   Ausschließlich explizit und nutzerkontrolliert.

&nbsp;

## Integrität, Audit & Reproduzierbarkeit

Das Datenkonzept von BitGridAI unterstützt gezielt:

- deterministisches Verhalten
- Replay-Fähigkeit
- nachträgliche Prüfung von Entscheidungen

Dies wird erreicht durch:
- unveränderliche Zustände (siehe 8.1),
- vollständige Entscheidungsprotokolle,
- Integritätsmechanismen bei Exporten.

&nbsp;

## Aufbewahrung & Löschung

BitGridAI erzwingt keine festen Aufbewahrungsfristen, stellt jedoch Leitlinien bereit:

- Laufzeitdaten: kurzlebig
- Logs & Events: begrenzt, rotierend
- Forschungsdaten: nutzerkontrolliert

Löschung erfolgt:
- bewusst,
- nachvollziehbar,
- ohne Einfluss auf den laufenden Betrieb.

&nbsp;

## Abgrenzungen

Nicht Bestandteil dieses Kapitels sind:
- konkrete Dateipfade oder Tabellen
- Backup-Tools
- UI-Dialoge für Exporte

Diese Details gehören in Betriebs- oder Entwicklerdokumentation.

&nbsp;

## Zusammenfassung

Die Datenhaltung von BitGridAI ist kein Nebenprodukt, sondern Teil der Architektur.

Sie stellt sicher, dass:
- Entscheidungen nachvollziehbar bleiben,
- der Betrieb robust ist,
- Analyse und Forschung möglich sind,
- der Nutzer die Kontrolle behält.

Daten sind Gedächtnis – und Verantwortung.

---

> **Nächster Schritt:** Entscheidungen sollen nicht nur korrekt, sondern auch verständlich sein.  
> Im nächsten Abschnitt betrachten wir **Explainability & Transparenz**.
>
> 👉 Weiter zu **[8.4 - Explainability & Transparenz](./084_explainability.md)**
>
> 🔙 Zurück zur **[Kapitelübersicht](./README.md)**
