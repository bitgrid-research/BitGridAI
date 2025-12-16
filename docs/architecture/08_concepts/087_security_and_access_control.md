# 8.7 Security & Zugriffskontrolle

Vertrauen braucht Schutz.

BitGridAI läuft lokal, trifft Entscheidungen autonom und steuert reale Hardware.  
Auch ohne Cloud-Anbindung ist Sicherheit kein „Nice-to-have“, sondern **Grundvoraussetzung**.

Dieses Kapitel beschreibt die **übergreifenden Sicherheitsprinzipien, Authentifizierungsmechanismen und Zugriffskontrollen** von BitGridAI.  
Ziel ist es, unautorisierte Eingriffe zu verhindern, ohne den lokalen Betrieb unnötig zu verkomplizieren.

*(Platzhalter für ein Bild: Ein Pixel-Art-Hamster als Türsteher mit Schlüsselbund und Firewall-Schild vor einer Tür mit der Aufschrift „Core“.)*

---

## Sicherheitsziele

Die Security-Architektur von BitGridAI verfolgt folgende Ziele:

1. **Schutz vor unautorisierten Aktionen**  
   Kein externer oder interner Akteur darf Steuerbefehle ohne Berechtigung ausführen.

2. **Begrenzung von Schäden**  
   Selbst bei kompromittierten Komponenten bleibt der Schaden lokal und begrenzt.

3. **Nachvollziehbarkeit**  
   Sicherheitsrelevante Ereignisse sind sichtbar, auditierbar und erklärbar.

4. **Einfachheit im LAN**  
   Sicherheit darf den lokalen Betrieb nicht unnötig verkomplizieren.

---

## Grundprinzipien

### Local-first Security
- keine externen Auth-Provider
- keine Cloud-Identitäten
- alle Schlüssel und Tokens verbleiben lokal

### Least Privilege
- Komponenten erhalten nur die Rechte, die sie benötigen
- Lesezugriffe sind vom Schreibzugriff getrennt

### Defense in Depth
- mehrere Schutzschichten (Netz, API, Anwendung)
- kein einzelner Schutzmechanismus ist allein kritisch

---

## Authentifizierung

### API-Zugriffe

- Schreibende Endpunkte (`/override`, `/research/export`, `/config/reload`) sind **authentifizierungspflichtig**
- Authentifizierung erfolgt über:
  - statische Tokens
  - oder lokale Credentials
- Tokens sind konfigurierbar, rotierbar und widerrufbar

Lesezugriffe (z.B. Status, Explain-Events) können optional offen oder eingeschränkt sein.

---

### UI-Zugriff

- UI ist standardmäßig **nicht direkt exponiert**
- Zugriff erfolgt über:
  - lokalen Reverse Proxy
  - optional Umbrel-Auth
- Kritische Aktionen erfordern zusätzliche Bestätigung

---

## Autorisierung

BitGridAI unterscheidet funktional zwischen Rollen:

- **Observer**
  - Lesen von Status, Erklärungen, Logs
- **Operator**
  - Auslösen von Overrides
  - Starten von Exports
- **Admin**
  - Konfiguration
  - Feature-Flags
  - Token-Verwaltung

Die konkrete Rollenabbildung ist konfigurationsgetrieben.

---

## Rate-Limiting & Schutz vor Missbrauch

- Schreibende Endpunkte sind rate-limitiert
- Überschreitungen führen zu:
  - klaren HTTP-Fehlercodes (`429`)
  - Events (`rate_limited`)
- Abgelehnte Requests haben **keine Seiteneffekte**

Dies schützt sowohl vor Fehlbedienung als auch vor automatisierten Angriffen im LAN.

---

## Netzwerksicherheit

- Betrieb ausschließlich im LAN
- keine eingehenden WAN-Verbindungen
- optionale Segmentierung:
  - IoT / PV
  - Edge / Core
  - UI / Clients
- MQTT-Ports nur freigeben, wenn nötig

TLS wird empfohlen für:
- UI-Zugriffe
- optionale MQTT-Verbindungen

---

## Schlüssel- & Geheimnisverwaltung

- Tokens und Secrets liegen in:
  - `config/`
  - oder geschützten Umgebungsvariablen
- keine Secrets im Code oder in Images
- Backups enthalten Secrets nur verschlüsselt

---

## Security & Fail-safe

Sicherheitsverletzungen führen **nicht** zu automatischen Systemstopps.

Stattdessen:
- Aktionen werden blockiert
- Events werden erzeugt
- Health-Status kann auf `warn` wechseln

Der laufende Betrieb bleibt stabil und kontrolliert.

---

## Abgrenzungen

Nicht Bestandteil dieses Kapitels sind:
- konkrete Firewall-Regeln
- TLS-Zertifikatsmanagement
- OS-Hardening-Details

Diese gehören in Betriebs- und Infrastruktur-Dokumentation.

---

## Zusammenfassung

Die Security-Architektur von BitGridAI stellt sicher, dass:

- nur autorisierte Akteure eingreifen können,
- Schäden lokal begrenzt bleiben,
- sicherheitsrelevante Ereignisse nachvollziehbar sind.

BitGridAI ist kein Cloud-System – aber **es nimmt Sicherheit ernst**.

---

> **Nächster Schritt:** Sicherheit erzeugt Daten – Logs, Events, Metriken.  
> Im nächsten Abschnitt betrachten wir **Logging, Events & Observability**.
>
> 👉 Weiter zu **[8.8 Logging & Observability](./088_logging_and_observability.md)**
>
> 🔙 Zurück zur **[Kapitelübersicht](./README.md)**
