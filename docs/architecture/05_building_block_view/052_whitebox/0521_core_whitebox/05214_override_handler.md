# 05.2.1.4 Override Handler

Der menschliche Eingriff.

Der Override Handler verarbeitet **manuelle Eingriffe** wie *Boost*, *Stop* oder *Limit*.  
Er gibt dem Nutzer gezielt Kontrolle – ohne dabei **Safety** und **Autarkie** zu kompromittieren.

*(Platzhalter für ein Bild: Der Hamster greift mit einer Hand an einen großen roten Hebel „Override“. Daneben hängen Schilder „Safety“ und „Autarkie“, die den Hebel notfalls abbremsen.)*
![Hamster setzt Override](../media/pixel_art_override_handler.png)

---

## Verantwortung

- Verarbeitung manueller Eingriffe (Boost / Stop / Limit)
- Setzen von Geltungsdauer (TTL) und Scope
- Prüfung auf Konflikte mit Safety- und Autarkie-Regeln
- Transparente Rückmeldung an Nutzer und Explain-Layer

---

## Struktur

- **Override Validator**  
  Prüft Authentifizierung, Scope (Gerät / Cluster) und Parameterbereiche.

- **TTL Manager**  
  Setzt Ablaufzeit (z.B. in Blocks), erneuert oder verwirft abgelaufene Overrides.

- **Conflict Checker**  
  Gleichen Overrides mit Safety- und Autarkie-Regeln ab.  
  Kann Overrides kürzen, abschwächen oder ablehnen.

- **Feedback Builder**  
  Bestätigt Annahme oder Ablehnung mit `command_id` und `valid_until`.

---

## Schnittstellen

**Provided**
- Aktiver Override-Status
- Rückmeldung an UI (`accepted`, `valid_until`, `command_id`)
- Events für Data- und Explain-Layer

**Required**
- User-Requests (`POST /override`)
- Regel- und Safety-Status
- Zeitquelle / Block-ID
- Policy-Konfiguration (wer darf was)

---

## Ablauf (vereinfacht)

1. UI oder REST sendet Override-Request → Validator prüft Auth und Parameter.
2. Conflict Checker bewertet den Eingriff gegen Safety und Autarkie.
3. TTL Manager trägt Override ein und plant den Ablauf.
4. Feedback Builder sendet Bestätigung oder Ablehnung an UI, Data und Explain.

---

## Qualität und Betrieb

- **Safety first**  
  Safety- und Autarkie-Regeln dürfen Overrides jederzeit beenden oder abschwächen.

- **Transparenz**  
  Jedes Override trägt `command_id`, `created_at`, `valid_until` und Status.

- **Begrenzung**  
  Rate Limits für Override-Requests, optionale Rollen (Operator vs. Observer).

---
> 🔙 Zurück zu **[5.2.1 Core-Orchestrierung](../0521_core_whitebox.md)**
> 
> 🔙 Zurück zu **[5.2 Level-2-Whiteboxes](./README.md)**
