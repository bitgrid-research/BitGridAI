# 05.2.5.1 Security & Auth

Verantwortung: lokale Authentifizierung, Rollen/Policies und Rate Limits fuer alle schreibenden Pfade (Override, Export, Config).

## Struktur

- **Auth Gate:** Token/LAN-Only, optionale Integration mit Home-Assistant-Usern.
- **Role/Policy Check:** Rollen (Operator/Observer) und Ressource-Scopes.
- **Rate Limiter:** Write-Limits fuer kritische Endpoints.

## Schnittstellen

- **Provided:** Auth/Policy-Enforcement fuer API/WS/Exports.
- **Required:** User/Rollen (lokal), Netzkonfiguration (allowed hosts), Policy-Definition.

## Ablauf (vereinfacht)

1) Request kommt rein -> Auth Gate prueft Token/LAN.  
2) Role/Policy Check prueft Scope.  
3) Rate Limiter setzt Grenzen fuer Writes.

## Qualitaet und Betrieb

- Lokal, keine externen Provider.  
- Minimal geoeffnete Ports.  
- Logs fuer Auth-Fails und Policy-Drops.

---
> Zurueck zu **[5.2.5.x Operations (Level 3)](./README.md)**  
> Zurueck zu **[5.2.5 Whitebox Operations](../0525_operations_whitebox.md)**
