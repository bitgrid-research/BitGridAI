# 05.2.5.1 Security & Auth

Der Türsteher am Systemeingang.

Dieses Modul sorgt dafür, dass **nur berechtigte Akteure schreiben dürfen** –  
Overrides, Exporte und Konfigurationsänderungen sind geschützt, lokal und kontrolliert.

Kein Cloud-Login.  
Keine versteckten Identitäten.  
Nur klare Regeln im eigenen Netz.

*(Platzhalter für ein Bild: Der Hamster steht vor einer Tür mit Schloss und Klemmbrett.
Auf dem Schild: „LAN only“. Er prüft Ausweise.)*
![Hamster Security](../media/pixel_art_security_auth.png)

---

## Verantwortung

- Lokale Authentifizierung (LAN-first)
- Durchsetzung von Rollen und Policies
- Rate Limits für alle schreibenden Pfade

---

## Struktur

- **Auth Gate**  
  Token- und LAN-basierte Zugriffskontrolle, optional gekoppelt an Home-Assistant-User.

- **Role / Policy Check**  
  Rollen (Operator / Observer) und Ressourcenscopes (Override, Export, Config).

- **Rate Limiter**  
  Schutz kritischer Endpoints vor Missbrauch oder Fehlbedienung.

---

## Schnittstellen

**Provided**
- Auth- und Policy-Enforcement für API, WebSocket und Export-Pfade

**Required**
- Lokale User- und Rolleninformationen
- Netzkonfiguration (allowed hosts / Subnetze)
- Policy-Definitionen

---

## Ablauf (vereinfacht)

1) Request trifft ein → **Auth Gate** prüft Token und LAN-Herkunft  
2) **Role / Policy Check** validiert Rolle und Scope  
3) **Rate Limiter** begrenzt schreibende Aktionen  
4) Anfrage wird freigegeben oder abgelehnt (mit Log-Eintrag)

---

## Qualitäts- und Betriebsaspekte

- **Local-only:** keine externen Auth-Provider, keine Cloud-Abhängigkeit  
- **Minimal offen:** nur notwendige Ports und Endpoints  
- **Nachvollziehbar:** Logs für Auth-Fails, Policy-Drops und Rate-Limit-Treffer  

---
> 🔙 Zurück zu **[5.2.5.x Operations (Level 3)](./README.md)**  
> 🔙 Zurück zu **[5.2.5 Whitebox Operations](../0525_operations_whitebox.md)**
