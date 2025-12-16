# 06.12 Szenario: Authentifizierung & Rate-Limit (Fehlpfade)

Kein Zugriff, keine Wirkung.

Nicht jeder Request darf Wirkung entfalten.  
BitGridAI schützt schreibende Endpunkte konsequent vor unautorisierten Zugriffen und Überlastung. Dieses Szenario beschreibt, wie das System auf fehlende Authentifizierung oder überschrittene Rate-Limits reagiert – **klar, sichtbar und ohne Seiteneffekte**.

*(Platzhalter für ein Bild: Ein Pixel-Art-Hamster steht vor einer Schranke mit Schloss und Stoppuhr. Ein Schild: „Access denied“.)*

---

## Das Ziel: Schutz ohne Nebenwirkungen

Grundprinzip:
> **Ein abgelehnter Request darf keinen Zustand verändern.**

Auth- und Rate-Limit-Prüfungen liegen **vor** jeder fachlichen Verarbeitung.  
Fehler werden eindeutig signalisiert, aber niemals „halb“ ausgeführt.

---

## Der Ablauf bei Auth- und Rate-Limit-Fehlern (vereinfacht)

1. **Eingang (Request):**  
   Ein schreibender Request trifft ein, z.B.:
   - `/override`
   - `/research/export`

2. **Authentifizierung (Auth):**  
   Die Authentifizierung oder Autorisierung schlägt fehl.  
   → Response `401` oder `403`  
   → Event `auth_failed`

3. **Drosselung (Rate-Limit):**  
   Das definierte Rate-Limit ist erreicht.  
   → Response `429`  
   → Event `rate_limited`

4. **Abbruch (No Side Effects):**  
   - Keine Aktion auf Geräte
   - Keine Änderung von Zuständen
   - Keine Persistenz

   Das UI zeigt eine verständliche Fehlermeldung inkl. Retry-Hinweis.

---

## Verhalten des Systems

- Fachlogik (Rule Engine, Core) wird **nicht** aufgerufen.
- Adapter erhalten **keine** Befehle.
- Der laufende Blockbetrieb bleibt unbeeinflusst.
- Fehler sind explizit sichtbar, aber nicht eskalierend.

---

## Schnittstellen & Signale

- **HTTP-Statuscodes:**  
  `401 Unauthorized`, `403 Forbidden`, `429 Too Many Requests`
- **Events:**  
  - `auth_failed`
  - `rate_limited`
- **Optional Metrics:**  
  - Anzahl Auth-Fehlschläge
  - Rate-Limit-Hits pro Endpoint

Diese Informationen stehen für UI, Monitoring und Audit zur Verfügung.

---

> **Nächster Schritt:** Alle relevanten Laufzeitpfade – inklusive Schutz- und Fehlerszenarien – sind nun beschrieben.  
> Jetzt betrachten wir, **wie BitGridAI technisch verteilt und betrieben wird**.
>
> 👉 Weiter zu **[07 Verteilungssicht](../07_deployment_view/README.md)**
> 
> 🔙 Zurück zur **[Kapitelübersicht](./README.md)**
