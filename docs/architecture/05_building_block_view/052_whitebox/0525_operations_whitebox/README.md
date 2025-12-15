# 05.2.5 Whitebox Operations (Security/Config/Observability)

Scope: Security/Auth, Policies, Konfiguration und Observability als Querschnitt.

## Enthaltene Bausteine (Level 3)

| Baustein | Verantwortung | Hinweise |
| --- | --- | --- |
| **Security & Auth** | Lokale Auth, Rollen (Operator/Observer), Token/LAN-Only, Rate Limits. | Kein externer Provider, minimale Ports. |
| **Configuration & Feature Flags** | Zentrale Profile/YAML, Schema-Validierung, Reload. | Signatur/Checksum optional, Default-Profile. |
| **Observability & Monitoring** | Metriken, Logs, Health-Endpoints, Alerts. | Konsolidiert Health aus Core/Adaptern/UI. |

## Level-3-Details

- [5.2.5.1 Security & Auth](./0525_operations_whitebox/05251_security_auth.md)
- [5.2.5.2 Configuration & Feature Flags](./0525_operations_whitebox/05252_config_feature_flags.md)
- [5.2.5.3 Observability & Monitoring](./0525_operations_whitebox/05253_observability.md)

## Schnittstellen

- **Provided:** Auth/Policy-Durchsetzung, Health/Metriken-Feeds, Config-Reload-Events.
- **Required:** User/Rollen-Infos (lokal), Config-Files (`config/*.yaml`), Health-Signale aus Bausteinen.

## Hauptdatenfluesse

1) Auth/Policy wird auf API/Override/Export angewendet.  
2) Config-Loader validiert/reloadet Profile -> verteilt Defaults/Flags an Core/Adapter/UI.  
3) Health/Metrik-Streams aus Core/Adaptern/UI -> Sammelpunkt -> Anzeige/Alerts/Logs.

## Qualitaets- und Betriebsaspekte

- Lokal und minimal: kein externer Auth-Provider, nur noetige Ports.  
- Nachvollziehbarkeit: Config-Versionen und Reloads werden geloggt.  
- Sichtbarkeit: zentrale Health/Metriken statt verstreuter Einzel-Checks.

---
> Zurueck zu **[5.2 Level-2-Whiteboxes](./README.md)**  
> Zurueck zu **[5.1 Whitebox Gesamtsystem](../051_blackbox/051_blackbox.md)**
