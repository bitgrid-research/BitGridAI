# 8.2 Sicherheits- & Vertrauenskonzept

Sicherheit vor Optimierung.

BitGridAI trifft Entscheidungen, die reale Auswirkungen auf Hardware, Energieflüsse und Kosten haben.  
Deshalb ist Sicherheit kein optionales Feature, sondern eine **zentrale Systemeigenschaft**, die alle anderen Ziele überlagert.

Dieses Kapitel beschreibt die **systemweiten Sicherheits- und Vertrauensprinzipien** von BitGridAI.  
Sie gelten unabhängig von Autonomie-Stufe, Betriebsmodus oder Deployment-Variante.

*(Platzhalter für ein Bild: Ein Pixel-Art-Hamster mit Schutzhelm steht vor einem großen roten Not-Aus-Schalter. Ein Schild: „Safety First“. )*  
![Hamster schützt das System](link_zum_safety_hamster.png)

---

## Grundprinzipien

Das Sicherheitskonzept von BitGridAI folgt vier übergeordneten Grundsätzen:

1. **Safety sticht alles**  
   Sicherheitsregeln haben stets Vorrang vor Optimierung, Komfort und Nutzerwünschen.

2. **Kein Vertrauen ohne Prüfung**  
   Externe Signale, Nutzeraktionen und Konfigurationsänderungen werden immer validiert.

3. **Klare Vertrauensgrenzen**  
   Das System unterscheidet explizit zwischen vertrauenswürdigen und nicht-vertrauenswürdigen Zonen.

4. **Deterministisches Fehlverhalten**  
   Bei Unsicherheit wird nicht improvisiert, sondern konservativ gehandelt.

---

## Sicherheitsregel R3 – Die oberste Instanz

Die Sicherheitsregel **R3 (Safety)** ist die höchste Autorität im System.

**Eigenschaften von R3:**
- nicht deaktivierbar
- nicht konfigurierbar
- nicht durch Autonomie-Stufen oder Overrides übersteuerbar

R3 greift immer dann, wenn:
- Hardware-Grenzwerte überschritten werden (z.B. Temperatur),
- Pflichtsignale fehlen,
- der Systemzustand nicht eindeutig bewertbar ist.

**Konsequenz:**  
R3 darf den Betrieb jederzeit stoppen oder in einen sicheren Zustand versetzen.

---

## Vertrauenszonen

BitGridAI arbeitet bewusst mit klar abgegrenzten Vertrauenszonen:

### Lokale Systemzone (Trusted)

- Core
- Rule Engine
- Persistenz
- Explain-Agent

Diese Komponenten:
- laufen auf demselben Host oder im selben LAN,
- sind integraler Bestandteil des Systems,
- gelten als vertrauenswürdig.

---

### Geräte- & Adapterzone (Semi-Trusted)

- Sensoren
- Inverter
- Miner
- externe Adapter

Diese Quellen:
- liefern Daten oder führen Aktionen aus,
- können fehlerhaft, verzögert oder manipuliert sein,
- werden niemals blind vertraut.

Alle eingehenden Signale werden:
- validiert,
- plausibilisiert,
- bei Bedarf verworfen.

---

### Nutzer- & Integrationszone (Untrusted)

- UI-Eingaben
- Home Assistant
- REST-Clients
- Research-Exporte

Diese Zugriffe:
- erfordern Authentifizierung,
- unterliegen Autorisierung und Rate-Limits,
- haben keinen direkten Zugriff auf Hardware.

---

## Authentifizierung & Autorisierung

Schreibende Zugriffe auf BitGridAI sind grundsätzlich geschützt.

**Grundregeln:**
- Lesezugriffe sind restriktiv, aber niedrigschwellig.
- Schreibzugriffe erfordern explizite Berechtigung.
- Authentifizierung erfolgt lokal (keine Cloud-Abhängigkeit).

**Typische geschützte Aktionen:**
- manuelle Overrides
- Konfigurations-Reloads
- Exporte

Fehlgeschlagene Authentifizierung:
- verändert keinen Systemzustand,
- erzeugt nachvollziehbare Events (siehe Kap. 6.12).

---

## Rate-Limiting & Missbrauchsschutz

Zur Vermeidung von Fehlbedienung und Missbrauch gelten:

- Rate-Limits für alle schreibenden Endpunkte
- klare Fehlermeldungen bei Überschreitung
- keine teilweise Ausführung

Ein abgelehnter Request:
- löst keine Aktionen aus,
- verändert keine Zustände,
- hinterlässt einen Audit-Eintrag.

---

## Umgang mit Unsicherheit & Ausfällen

Unsicherheit wird in BitGridAI explizit behandelt:

- fehlende Pflichtsignale → Degradation
- Kommunikationsabbrüche → Safe- oder Stop-Zustand
- inkonsistente Konfiguration → Verwerfen & Rollback

**Wichtig:**  
Unsichere Situationen führen niemals zu aggressiver Optimierung.

---

## Sicherheit & Autonomie

Autonomie-Stufen verändern, **wer entscheidet**, nicht **was erlaubt ist**.

Unabhängig vom Autonomie-Level gilt:
- R3 bleibt aktiv
- Safety kann nicht übersteuert werden
- manuelle Eingriffe sind zeitlich begrenzt

Das Sicherheitskonzept ist damit **orthogonal** zur Autonomie-Logik.

---

## Sichtbarkeit & Nachvollziehbarkeit

Sicherheitsrelevante Ereignisse sind immer sichtbar:

- Safety-Events werden geloggt
- Entscheidungen enthalten Begründungen
- UI signalisiert aktive Safety-Zustände eindeutig

Es gibt keine „stillen“ Sicherheitsaktionen.

---

## Abgrenzungen

Nicht Bestandteil dieses Kapitels sind:
- konkrete Firewall-Regeln
- TLS-Konfigurationen
- Container-Hardening im Detail

Diese Aspekte werden in der Verteilungssicht (Kap. 07) oder im Betriebshandbuch behandelt.

---

## Zusammenfassung

Das Sicherheits- und Vertrauenskonzept von BitGridAI stellt sicher, dass:

- keine Entscheidung ohne belastbare Grundlage getroffen wird,
- Sicherheit immer Vorrang hat,
- menschliche Kontrolle möglich bleibt, ohne Risiken zu erhöhen.

Sicherheit ist kein Sonderfall – sie ist der Normalzustand.

---

> **Nächster Schritt:** Sicherheit schafft Vertrauen – aber Verständnis schafft Akzeptanz.  
> Im nächsten Abschnitt betrachten wir **Explainability & Transparenz**.
>
> 👉 Weiter zu  **[8.3 Datenhaltung & Datenlebenszyklus](./083_data_persistence.md)**  
>
> 🔙 Zurück zur **[Kapitelübersicht](./README.md)**
