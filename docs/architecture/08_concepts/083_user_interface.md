# 08.3 Benutzeroberfläche & Explainability UI

Die Brücke zwischen Mensch und Maschine.

Die Benutzeroberfläche (UI) ist das zentrale Vertrauensinstrument von **BitGridAI**. Sie muss die Komplexität der Regel-Engine (R1–R5) in einfache, verständliche Antworten übersetzen.

Das zentrale Designprinzip ist **"Explainability by Design"**. Der Nutzer muss die Entscheidung der Automatik nicht nur sehen, sondern verstehen. Unser Ansatz folgt dem **HCI-Prinzip**: **Explain → Act → Confirm**.

*(Platzhalter für ein Bild: Der Hamster mit Brille steht vor einem aufgeräumten Dashboard. Ein roter Pfeil zeigt von der Aufschrift "Warum jetzt?" auf einen grünen "Bestätigen"-Button.)*
![Hamster am Dashboard](../../media/pixel_art_hamster_dashboard.png)

## 1. Übergreifende Designziele & Prinzipien

| Prinzip | Zielsetzung | Beispiel-Baustein |
| :--- | :--- | :--- |
| **Explainability** | Jede Aktion muss erklären: **Warum jetzt?** Schwellenwerte, Trigger und die aktive Regel müssen sichtbar sein. | **Why-Now? Panel**, **Decision-Toast** |
| **Control & Reversibility** | **Manuelle Eingriffe** sind jederzeit möglich, aber klar begrenzt (TTL). Sie müssen leicht rücknehmbar sein. | **Override-Chip**, **Countdown** |
| **Prediction & Trust** | Das System darf keine Blackbox sein. Biete eine **Vorschau** auf die nächste Entscheidung (Next-Block Preview) und bestätige die Wirkung. | **Timeline**, **Next-Block Preview** |
| **Privacy-by-Default** | Die UI funktioniert vollständig **lokal** (Local-First UI). Datensammlung (Research-Toggle) erfordert aktives Opt-in. | **Research-Toggle**, **KPI-Widget** |
| **Accessibility** | Einhaltung von Standards (Keyboard-Bedienung, ARIA) und Kontrast. (Option: "Bewegung reduzieren"). | ARIA-Labeling |

## 2. Der Frontend Tech Stack

Die Wahl des Stacks ist auf Performance auf schwacher Hardware (Edge Device) optimiert:

| Aspekt | Technologie | Grund für die Wahl |
| :--- | :--- | :--- |
| **Framework** | **Svelte / SvelteKit** | Geringe Bundle-Größe, schnelle Initialisierung, minimale Runtime-Last (gut für Raspberry Pi). |
| **Echtzeit** | **WebSockets** | Live-Update des `EnergyState` und des `DecisionEvent`-Streams für minimalen Netzwerk-Overhead. |
| **Visualisierung** | **D3.js / ECharts** | Darstellung der Zeitreihen und der Timeline-Vorschau. |
| **Integration** | **MQTT-Schnittstelle** | Ermöglicht die Darstellung der UI-Elemente als native Lovelace-Karten in Home Assistant. |

## 3. Die zentralen UI-Bausteine

Die folgenden Bausteine sind auf die Entscheidungs- und Kontrollfunktionen von BitGridAI zugeschnitten.

| Baustein | Zweck | Mikrotexte (Beispiele) |
| :--- | :--- | :--- |
| **Decision-Toast** | Sofort-Erklärung bei einem Schaltvorgang. Enthält Link zur detaillierten **Timeline**. | **Start (R1):** „Surplus 1.8 kW ≥ 1.5 kW, Preis 16 ct ≤ 18 ct.“ |
| **Why-Now? Panel** | **Die Haupt-Erklärung.** Zeigt die aktuell aktive Regel (R1–R5) mit den relevanten Schwellenwerten (`trigger_metrics` des DecisionEvent). | **Stop (R2/R3):** „Stop: SoC 24 % ≤ 25 % (R2). Sicherheit geht vor.“ |
| **Next-Block Preview** | Vorschau auf die nächste Entscheidung (nächster 10-Minuten-Block). Berücksichtigt R4 (Forecast). | **Preview:** „Nächster Block: voraussichtlich weiterlaufen; Prognose stabil (R4).“ |
| **Timeline** | Graphischer Verlauf aller `DecisionEvents` und `Overrides` in der Vergangenheit. Ermöglicht Filterung, Annotation und Daten-Export. | **Hold (R5):** „Stabilisierung aktiv (R5): bis Block +1.“ |
| **Override-Chip** | Element zur Steuerung des **Manuellen Overrides**. Zeigt die aktive Aktion (Start/Stop/Level) und die verbleibende Gültigkeitsdauer (TTL). | **Override:** „Manueller Start aktiv – läuft ab in 14 Min.“ |
| **Health-Banner** | System-Gesundheit. Meldet Probleme, die nichts mit den Regeln zu tun haben (z.B. MQTT-Broker nicht erreichbar, Zeitversatz (Drift) oder Sensor-Daten veraltet). | **Alert:** „Sensor-Daten seit 30s veraltet. Vorsicht bei Overrides.“ |
| **KPI-Widget** | Zeigt Metriken für die Vertrauensbildung: `Coverage` (Wie oft Miner lief, obwohl er konnte), `Flapping` (Wie oft R5 intervenieren musste). Lokal berechnet. | **KPI:** „Vertrauensindex: 92 %. Flapping: 1x/Tag.“ |

---
> **Nächster Schritt:** Wir haben die Regeln und die Oberfläche definiert. Nun klären wir die letzten übergreifenden Konzepte, bevor wir zu den Design-Entscheidungen kommen.
>
> 👉 Weiter zu **[08.4 Weitere Querschnittliche Konzepte](./084_other_concepts.md)**
>
> 🔙 Zurück zur **[Kapitelübersicht](./README.md)**
