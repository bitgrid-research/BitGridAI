# 05.2.5.1  - Baustein: Security & Auth

Der Türsteher am Systemeingang.

Dieses Modul entscheidet nicht, **was** BitGridAI tut –  
sondern **wer es darf**.

Security & Auth schützt alle **schreibenden Pfade**:
Overrides, Exporte und Konfigurationsänderungen.
Alles bleibt lokal, kontrolliert und nachvollziehbar.

Kein Cloud-Login.  
Keine impliziten Identitäten.  
Nur klare Regeln im eigenen Netz.

*(Platzhalter für ein Bild: Der Hamster steht vor einer Tür mit Schloss und Klemmbrett.
Auf dem Schild: „LAN only“. Er prüft Ausweise.)*
![Hamster Security](../../../../media/bithamster_052.png)

&nbsp;

## Verantwortung

- Lokale Authentifizierung (LAN-first)
- Durchsetzung von Rollen und Policies
- Schutz aller schreibenden Endpunkte durch Rate Limits

&nbsp;

## Struktur

- **Auth Gate**  
  Token- und LAN-basierte Zugriffskontrolle,  
  optional gekoppelt an lokale Home-Assistant-User.

- **Role / Policy Check**  
  Durchsetzung von Rollen (*Operator*, *Observer*)  
  und Ressourcenscopes (Override, Export, Config).

- **Rate Limiter**  
  Begrenzt schreibende Aktionen zum Schutz vor
  Fehlbedienung, Loops oder Missbrauch.

&nbsp;

## Schnittstellen

**Provided**
- Auth- und Policy-Enforcement für API-, WebSocket- und Export-Pfade

**Required**
- Lokale User- und Rolleninformationen
- Netzkonfiguration (allowed hosts / Subnetze)
- Policy-Definitionen

&nbsp;

## Ablauf (vereinfacht)

1) Anfrage trifft ein → **Auth Gate** prüft Token und LAN-Herkunft  
2) **Role / Policy Check** validiert Rolle und Ressourcenscope  
3) **Rate Limiter** begrenzt schreibende Aktionen  
4) Anfrage wird freigegeben oder abgelehnt (inkl. Log-Eintrag)

&nbsp;

## Qualitäts- und Betriebsaspekte

- **Local-only**  
  Keine externen Auth-Provider, keine Cloud-Abhängigkeit.

- **Minimal offen**  
  Nur notwendige Ports und Endpoints sind erreichbar.

- **Nachvollziehbar**  
  Logs für Auth-Fails, Policy-Drops und Rate-Limit-Treffer.

---
> **Nächster Schritt:**  
> Zugriffe sind nun kontrolliert.  
> Als Nächstes kümmern wir uns um Konfiguration und Feature-Steuerung.
>
> 👉 Weiter zu **[5.2.5.2 - Baustein: Configuration & Feature Flags](./05252_config_feature_flags.md)**
>
> 🔙 Zurück zu **[5.2.5 - Whitebox: Operations (Security, Config & Observability)](./README.md)**
>
> 🔙 Zurück zu **[5.2 - Level-2-Whiteboxes](../README.md)**
