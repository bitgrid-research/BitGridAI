# 05.2.1.4 Override Handler

Verantwortung: verarbeitet manuelle Eingriffe (Boost/Stop/Limit), setzt Geltungsdauer (TTL) und Scope, stellt Konsistenz mit Safety- und Autarkie-Regeln sicher.

## Struktur

- **Override Validator:** prueft Auth, Scope (Geraet/Cluster), Parameterbereiche.
- **TTL Manager:** setzt Ablaufzeit (z.B. in Blocks), erneuert oder verwirft abgelaufene Overrides.
- **Conflict Checker:** gleicht Overrides mit Safety/Autarkie ab; kann kuerzen oder ablehnen.
- **Feedback Builder:** bestaetigt Annahme oder Ablehnung mit `command_id` und `valid_until`.

## Schnittstellen

- **Provided:** aktiver Override-Status, Rueckmeldung an UI (`accepted`, `valid_until`, `command_id`), Events fuer Data/Explain.
- **Required:** User-Requests (`POST /override`), Regel- und Safety-Status, Zeitquelle/Block-ID, Policy-Konfiguration (wer darf was).

## Ablauf (vereinfacht)

1) UI/REST schickt Override-Request -> Validator prueft Auth/Parameter.  
2) Conflict Checker bewertet gegen Safety/Autarkie; ggf. Anpassung oder Ablehnung.  
3) TTL Manager traegt Override ein, plant Ablauf; Decision-Pfad bekommt aktiven Override.  
4) Feedback Builder liefert Bestaetigung an UI/Data/Explain.

## Qualitaet und Betrieb

- Safety first: Safety/Autarkie koennen Override sofort beenden oder abschwaechen.  
- Transparenz: jedes Override bekommt `command_id`, `created_at`, `valid_until`, Status.  
- Grenzen: Rate Limits fuer Override-Requests, optionale Rollen (Operator vs. Observer).

---
> Zurueck zu **[5.2.1.x Core-Orchestrierung (Level 3)](./README.md)**  
> Zurueck zu **[5.2.1 Core-Orchestrierung](../0521_core_whitebox.md)**
