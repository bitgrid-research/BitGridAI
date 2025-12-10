# 023 – Leitplanken & Konventionen / Conventions

TODO: Unsere internen Gesetze. Wie schreiben wir Code? Wie benennen wir Dinge? An welche Standards halten wir uns, damit alle im Team effizient zusammenarbeiten?

> **Kurzüberblick:**  
> Datenschutz (DSGVO), Open-Source-Lizenz **AGPLv3**, Sicherheit & Umwelt, Explainability-Pflicht, keine Cloud-Abhängigkeit.

> **TL;DR (EN):**  
> GDPR-friendly, AGPLv3, safety & sustainability guardrails, explainability duty, no cloud dependence.

---

## Rechtlich & Ethisch / Legal & Ethical

| Bereich | Beschreibung |
| --- | --- |
| **Datenschutz (DSGVO)** | Keine Cloud-Verarbeitung personenbezogener Daten; **Datenminimierung** & lokale Aufbewahrung. |
| **Einwilligung & Anonymisierung** | Informierte Einwilligung für Studien; Pseudonymisierung der Logs. |
| **Transparenzpflicht** | Entscheidungen erklärbar (UI, Timeline, DecisionEvents). |
| **Open-Source-Lizenz** | **AGPLv3**; Third-Party-Lizenzen beachten. |
| **Sicherheitsnormen** | Zertifizierte Schaltkomponenten; keine Arbeiten an Netzspannung im Projektumfang. |
| **Keine Zentralabhängigkeit** | Grundfunktionen ohne Drittanbieter-Cloud oder API-Keys. |

---

## Umwelt & Nachhaltigkeit

| Bereich | Beschreibung |
| --- | --- |
| **Energieverbrauch** | Deadband, Blocktakt und Leistungsstufen minimieren Dauerlasten. |
| **Hardwarelebensdauer** | Thermo-/Lüfter-Policies schützen Komponenten. |
| **Materialeinsatz** | Reparierbare/refurb Hardware bevorzugt. |
| **PV-Überschussnutzung** | Lokal verbrauchen (Mining/Heat/Hodl), optional Wärmenutzung. |

---

## HCI & Explainability

| Bereich | Beschreibung |
| --- | --- |
| **User Autonomy** | Manuelle Overrides mit klarer Rücknahme-Logik (Timeout/Next-Block). |
| **Erklärungspflicht** | Jede Decision liefert **Reason/Trigger/Params**; Explainability-UI ist Pflicht. |
| **Vorhersage-Feedback** | UI zeigt „Was passiert im nächsten Block?“ inkl. Schwellen. |
| **Audit-Trail** | Timeline mit DecisionEvents, EnergyState-Snapshots, Was-wäre-wenn, KPI-Hinweisen. |

> GDPR + AGPLv3, sustainability guardrails, explainability duty, user autonomy, no cloud requirement.
