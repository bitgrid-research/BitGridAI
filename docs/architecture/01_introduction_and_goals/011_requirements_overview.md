# 01.1 Anforderungen & Überblick

Willkommen im Herzstück des Projekts. 

Bevor wir uns in die technischen Details stürzen, müssen wir die Gretchenfrage klären: Was bauen wir hier eigentlich?

**BitGridAI** ist unsere Antwort darauf, wie lokale Energiesysteme in Zukunft aussehen müssen: intelligent, dezentral und vor allem *einfach* für dich als Endanwender.

## Das Kernproblem & Unsere Lösung

**Das Problem 🏝️:** In modernen Haushalten und Gewerben wimmelt es von Technik: PV-Anlagen, Batteriespeicher, Wallboxen für E-Autos und Wärmepumpen. Doch aktuell sind das oft "Inseln". Sie reden nicht miteinander, und du musst ständig manuell eingreifen, um Energie effizient zu nutzen.

**Unsere Lösung (BitGridAI) 🎻:** Wir bauen den "lokalen Dirigenten". BitGridAI ist die Software-Plattform, die hardware-agnostisch verschiedene Erzeuger und Verbraucher vernetzt. Sie nutzt KI-gestützte Prognosen, um Energieflüsse vollautomatisch zu optimieren.

* **Das Ziel:** Eigenverbrauch maximieren, Kosten senken und das lokale Netz stabilisieren – ohne dass deine Daten das Haus verlassen.

<img src="../../media/bithamster_conductor.png" alt="Hamster Dirigent" width="1000" />

---

## Wesentliche Features (Was das System draufhaben muss)

Wir konzentrieren uns auf vier Kernfunktionen, die das System ausmachen:

### 1. Hardware-Agnostische Konnektivität 🔌
Kein "Vendor Lock-in". Wir spielen mit allen.
* **Anforderung:** BitGridAI muss über Standardprotokolle (z.B. Modbus TCP, MQTT, EEBUS) mit einer breiten Palette an gängigen Wechselrichtern, Zählern und Wallboxen kommunizieren können.
* **Ziel:** Echte "Plug & Play"-Erfahrung bei der Installation neuer Hardware.

### 2. KI-basierte Optimierung (Der "AI"-Teil) 🧠
Das System reagiert nicht nur, es denkt voraus.
* **Anforderung:** Integration von Machine-Learning-Modellen, die basierend auf historischen Daten und Wetterprognosen die Erzeugung und den Verbrauch für die nächsten 12 Stunden vorhersagen.
* **Ziel:** Ein Batteriespeicher wird nicht stumpf geladen, nur weil die Sonne scheint. Er wird intelligent gesteuert, damit er voll ist, wenn dein E-Auto am Abend ankommt.

### 3. Intuitive Nutzersteuerung & Transparenz 📱
Technik, die man versteht, ohne Ingenieurstudium.
* **Anforderung:** Ein modernes, responsives Web-Interface, das dir in Echtzeit zeigt: "Wo fließt mein Strom gerade hin?".
* **Ziel:** Vertrauen. Du brauchst einfache Möglichkeiten, Präferenzen zu setzen, ohne dich durch komplexe Menüs zu wühlen.

### 4. Lokale Autonomie & Resilienz 🛡️
Cloud ist nett, lokal ist lebenswichtig.
* **Anforderung:** Die Kernfunktionen (Steuerung, Sicherheit) müssen vollständig lokal auf einem Edge-Device laufen.
* **Ziel:** Wenn das Internet ausfällt, optimiert BitGridAI weiter. Dein Haus bleibt intelligent.

---

## Kernanforderungen (Technical Deep Dive)

Jetzt wird es konkret. Damit die Vision funktioniert, gelten folgende harte technische Regeln:

![Hamster taktet die 10-Minuten-Blöcke](link_zum_block_takt_bild.png)

### Die Core-Logik
* **R1–R5 Deterministisch:** Das System folgt strengen Regeln für Start, Autarkie-Schutz, Thermo-Schutz, Prognose-Check und Anti-Flapping. Kein "Voodoo", sondern nachvollziehbare Logik.
* **Block-Scheduler:** Wir takten das System wie Bitcoin. Entscheidungen sind an den **10-Minuten-Block** gebunden. Das bringt Ruhe rein. Deadbands vergeben ein `valid_until`, um Flattern zu verhindern.
* **EnergyState (SSoT):** Es gibt genau eine "Single Source of Truth" für Messwerte, Prognosen, Preise, SoC und Temperaturen. Keine Daten-Duplikate.

### Architektur & Sicherheit
* **Explainability by Design:** Jede Aktion liefert `reason`, `trigger` und `params`. Dazu gibt es eine Timeline und eine "Next-Block-Preview". Wir wollen wissen, *warum* das System etwas tut.
* **Safety First:** Hardware-Schutz geht vor Profit. Bei Verletzung von SoC- oder Temperaturgrenzen gilt: **Stop → Safe**. Das Wiedereinschalten (Resume) erfolgt nur mit Hysterese.
* **Local-first / No Cloud:** Keine externen Abhängigkeiten für den Betrieb. Offline-Fähigkeit ist Pflicht.
* **Auditierbares Logging:** Wir schreiben Logs "Append-only" (z.B. SQLite oder Parquet). Configs sind versioniert (YAML). Damit ist alles für die Forschung reproduzierbar (Research-Toggle).

---

## MVP-Scope (Was ist in Version 1.0 drin?)

Für das Minimal Viable Product konzentrieren wir uns auf diese Komponenten:

1.  **Mining als flexible Last:** Erkennung von PV-Überschuss und entsprechende Steuerung (Start/Stop/Drosselung).
2.  **Explainability-Layer:** UI und ein On-Device "Explain-Agent" mit Timeline, Vorschau und manuellen Overrides (mit Block-TTL).
3.  **Lokale Adapter:** Volle Unterstützung für MQTT, REST und Modbus zur Anbindung von PV, Speicher, Smart Meter und Minern.
4.  **KPI-Tracking:** Wir messen Grid-Import (↓), Flapping-Rate (↓), Explanation Coverage, Trust-Score und stellen sicher, dass Thermal Incidents = 0 sind.
5.  **Replay & Forschung:** Tools für Log-Replay und "Was-wäre-wenn"-Simulationen inkl. Export-Bundles.

---

## Wesentliche Anwendungsfälle (Top Use Cases)

| ID | Titel | Beschreibung | Akteur |
| :--- | :--- | :--- | :--- |
| **UC-1** | **Maximierung Eigenverbrauch** | BitGridAI erkennt PV-Überschuss und entscheidet dynamisch, ob Speicher geladen oder Mining gestartet wird. | System |
| **UC-2** | **Netzdienliches Laden** | Anpassung an externe Signale (z.B. Tarif-Fenster), ohne den Nutzerkomfort zu gefährden. | System |
| **UC-3** | **Manueller Override** | Du brauchst "Boost"? Du kriegst Boost. Das System priorisiert sofort deinen Wunsch (z.B. Wallbox), auch wenn es unwirtschaftlich ist. | Nutzer |
| **UC-4** | **Sicherheitsüberwachung** | Kritische Temperatur? BitGridAI fährt das betroffene Subsystem sofort kontrolliert herunter (`Stop -> Safe`). | Safety |

---

## Abgrenzung (Was wir NICHT bauen) 🚫

Genauso wichtig wie das, was wir tun, ist das, was wir bewusst *nicht* tun:
* Wir bauen keine eigene Hardware (Wechselrichter, etc.).
* Wir bauen keine Abrechnungsplattform für Stromtarife (Billing).
* Wir sind kein SCADA-System für riesige Kraftwerke, sondern fokussieren uns auf "Residential & Small Commercial".
* Wir übernehmen keine **Verwahrung von Bitcoin (Custody)**. Wir steuern die Mining-Hardware lediglich an (Start/Stop), aber die Erträge fließen direkt in dein eigenes Wallet. Deine Keys, deine Coins.

---
> **Nächster Schritt:** Nachdem wir geklärt haben, *was* wir bauen, schauen wir uns an, nach welchen Maßstäben wir die Qualität messen.
>
> 👉 Weiter zu **[01.2 Qualitätsziele](./012_quality_goals.md)**
>
> 🔙 Zurück zur **[Kapitelübersicht](./README.md)**
