# 06.10 - Szenario: Config- & Feature-Flag-Reload

Umbauen im laufenden Betrieb.

BitGridAI soll anpassbar bleiben, ohne dafür neu gestartet werden zu müssen.  
Konfigurationsänderungen und Feature-Flags müssen **kontrolliert, nachvollziehbar und sicher** zur Laufzeit übernommen werden – oder im Fehlerfall sauber verworfen werden.

Dieses Szenario beschreibt, wie das System auf Änderungen an YAML-Konfigurationen oder Profilen reagiert und wie ein konsistenter Zustand erhalten bleibt.

*(Platzhalter für ein Bild: Ein Pixel-Art-Hamster tauscht im laufenden Betrieb Zahnräder aus. Ein Schild daneben: „Hot Reload – geprüft & sicher“.)*

&nbsp;

## Das Ziel: Dynamische Anpassung ohne Kontrollverlust

Grundprinzip:
> **Neue Konfigurationen werden entweder vollständig übernommen – oder gar nicht.**

Ein Reload darf:
- keinen inkonsistenten Zustand erzeugen,
- keine stillen Teilupdates verursachen,
- den laufenden Betrieb nicht unbemerkt destabilisieren.

&nbsp;

## Der Ablauf beim Config-Reload (vereinfacht)

1. **Erkennung (Trigger):**  
   Eine Konfigurationsänderung wird erkannt – entweder über File-Watch oder durch einen manuellen Trigger (z.B. API-Aufruf).

2. **Validierung (Check):**  
   Der Config-Loader validiert die neue Konfiguration:
   - Schema-Prüfung
   - optionale Checksumme oder Versionsprüfung

   **Ergebnis:**
   - **OK:** Neue Flags und Default-Werte werden vorbereitet.
   - **FAIL:** Reload wird verworfen, die vorherige Konfiguration bleibt aktiv.

3. **Verteilung (Apply):**  
   Core, Adapter und UI erhalten die neuen Konfigurationswerte.  
   Jede Komponente bestätigt die erfolgreiche Übernahme oder meldet einen Fehler zurück.

4. **Protokollierung (Audit):**  
   Der Reload-Vorgang wird als Event mit Version und Status dokumentiert.  
   Der Health-Status bleibt stabil oder wechselt bei Fehlern auf `warn` bzw. `error`.

&nbsp;

## Verhalten im Fehlerfall

- Bei Schema- oder Validierungsfehlern:
  - keine Übernahme der neuen Konfiguration
  - aktiver Rollback auf die letzte gültige Version
- Fehler werden explizit sichtbar gemacht:
  - Health-Event
  - Log- und UI-Hinweis
- Der laufende Blockbetrieb bleibt unbeeinflusst.

&nbsp;

## Schnittstellen & Signale

- **Reload-Event** mit:
  - Konfigurationsversion
  - Status (`success` / `failed`)
- **Health-Event** `config_error` bei Validierungsfehlern
- **Optionaler API-Endpoint:**  
  `POST /config/reload`

Alle Events sind extern beobachtbar (UI, Monitoring, Logs).

---

> **Nächster Schritt:** Konfiguration ist nun zur Laufzeit anpassbar.  
> Jetzt betrachten wir, **wie Daten kontrolliert exportiert und reproduzierbar analysiert werden können**.
>
> 👉 Weiter zu **[06.11 Export & Replay](./0611_export_replay.md)**
> 
> 🔙 Zurück zur **[Kapitelübersicht](./README.md)**
