# 06.11 Szenario: Export & Replay

Wissen mitnehmen – aber kontrolliert.

BitGridAI erzeugt wertvolle Daten: Logs, KPIs, Entscheidungsbegründungen und Explain-Sessions.  
Dieses Szenario beschreibt, wie diese Informationen **gezielt, nachvollziehbar und ausschließlich per Opt-in** exportiert werden können – ohne den laufenden Betrieb zu gefährden oder ungewollt Daten preiszugeben.

Der Export ist dabei kein „Dump“, sondern ein **reproduzierbares Forschungsartefakt**.

*(Platzhalter für ein Bild: Ein Pixel-Art-Hamster packt sorgfältig Datenkisten in eine beschriftete Box. Auf dem Deckel stehen „Manifest“, „Hash“, „Read-only“.)*

---

## Das Ziel: Reproduzierbarkeit ohne Kontrollverlust

Grundprinzip:
> **Kein Export ohne Zustimmung, kein Replay ohne Integrität.**

Der Export- und Replay-Mechanismus stellt sicher:
- explizites Nutzer-Opt-in,
- klare Definition von Umfang und Zeitraum,
- technische Nachvollziehbarkeit durch Manifest und Hash,
- strikt read-only beim Replay.

---

## Der Ablauf beim Export (vereinfacht)

1. **Auslösung (Trigger):**  
   Der Nutzer oder eine lokale API triggert einen Export und definiert:
   - Scope (Logs, KPIs, Explain-Sessions)
   - Zeitfenster  
   Vor dem Start wird das Opt-in geprüft.

2. **Sammlung (Bundle):**  
   Der Export-Service sammelt die angeforderten Daten und erstellt:
   - ein konsistentes Daten-Bundle,
   - ein Manifest (Inhalt, Versionen, Metadaten),
   - einen kryptografischen Hash.

3. **Bestätigung (Integrity):**  
   Hash und Manifest werden bereitgestellt.  
   Der Export steht lokal zum Download oder als Datei-Link zur Verfügung.

4. **Replay (optional):**  
   Ein Replay-Runner kann das Bundle nutzen, um Abläufe lokal nachzustellen.  
   Der Zugriff erfolgt **read-only** und hat keinen Einfluss auf das Live-System.

---

## Verhalten im Fehlerfall

- Fehlendes Opt-in → Export wird abgelehnt.
- Validierungs- oder Speicherfehler → kein unvollständiger Export.
- Fehler werden explizit signalisiert:
  - Event
  - Health-Status (`warn` / `error`)
  - UI-/Log-Hinweis

Ein fehlgeschlagener Export verändert weder den Systemzustand noch laufende Entscheidungen.

---

## Schnittstellen & Signale

- **API-Endpoint (lokal):**  
  `POST /research/export`
- **Response:**  
  Status, Hash, Manifest-Referenz
- **Health-/Event-Signale:**  
  bei Exportfehlern (Speicher, Opt-in, Validierung)

Alle Exporte sind nachvollziehbar und auditierbar.

---

> **Nächster Schritt:** Die Laufzeit ist vollständig beschrieben – inklusive Normalbetrieb, Eingriffen, Fehlerfällen und Analysepfaden.  
> Jetzt wechseln wir die Perspektive und betrachten, **wie und wo BitGridAI deployt wird**.
>
> 👉 Weiter zu **[07 Verteilungssicht](../07_deployment_view/README.md)**
> 
> 🔙 Zurück zur **[Kapitelübersicht](./README.md)**
