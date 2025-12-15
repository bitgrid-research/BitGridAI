# 05.2.5 Whitebox Operations (Security / Config / Observability)

Der Rahmen, der alles zusammenhält.

Diese Whitebox kümmert sich um die **Querschnittsthemen**, die man oft erst bemerkt, wenn sie fehlen:
Sicherheit, Konfiguration und Beobachtbarkeit.

Sie entscheidet nicht über Energieflüsse.  
Aber sie sorgt dafür, dass **alles andere verlässlich, kontrollierbar und sichtbar bleibt**.

*(Platzhalter für ein Bild: Der Hamster trägt Helm und Klemmbrett.
Neben ihm ein Schloss, ein Zahnrad und ein Fernglas – Security, Config, Observability.)*
![Hamster Operations](../media/pixel_art_operations.png)

---

## Scope

- Lokale Security und Zugriffskontrolle
- Zentrale, versionierte Konfiguration
- Einheitliche Observability über alle Bausteine hinweg

Alles **local-first**, ohne externe Abhängigkeiten.

---

## Enthaltene Bausteine (Level 3)

| Baustein | Verantwortung | Hinweise |
| --- | --- | --- |
| **Security & Auth** | Lokale Authentifizierung, Rollen (Operator / Observer), Policies. | LAN-only, keine externen Provider, minimale Ports. |
| **Configuration & Feature Flags** | Zentrale YAML-Profile, Schema-Validierung, Reload zur Laufzeit. | Optionale Signatur/Checksum, Default-Profile. |
| **Observability & Monitoring** | Metriken, Logs, Health-Endpunkte, Alerts. | Konsolidiert Status aus Core, Adaptern und UI. |

---

## Level-3-Details

- [5.2.5.1 Security & Auth](./05251_security_auth.md)
- [5.2.5.2 Configuration & Feature Flags](./05252_config_feature_flags.md)
- [5.2.5.3 Observability & Monitoring](./05253_observability.md)

---

## Schnittstellen

**Provided**
- Auth- und Policy-Durchsetzung für API, Overrides und Exporte
- Health- und Metrik-Feeds
- Config-Reload-Events

**Required**
- Lokale User- und Rolleninformationen
- Konfigurationsdateien (`config/*.yaml`)
- Health-Signale aus Core, Adaptern und UI

---

## Hauptdatenflüsse

1) API-/Override-/Export-Requests → Security & Auth → Freigabe oder Ablehnung  
2) Config-Loader validiert Profile → verteilt Flags und Defaults an Core/Adapter/UI  
3) Health- und Metrik-Streams → zentraler Sammelpunkt → UI / Logs / Alerts  

---

## Qualitäts- und Betriebsaspekte

- **Minimalistisch:** kein externer Auth-Provider, keine unnötigen Abhängigkeiten.  
- **Nachvollziehbar:** jede Konfigurationsänderung ist versioniert und geloggt.  
- **Sichtbar:** ein zentraler Blick auf Systemzustand statt verteilter Checks.

---
> **Nächster Schritt:** Die Bausteine stehen, der Betrieb ist abgesichert.  
> Jetzt betrachten wir, **wie das System im laufenden Betrieb zusammenspielt**.
>
> 👉 Weiter zu **[06 Laufzeitsicht](../../../06_runtime_view/README.md)**
>
> 🔙 Zurück zu **[5.2 Level-2-Whiteboxes](./README.md)**
> 
> 🔙 Zurück zu **[5.1 Blackbox Gesamtsystem](../../051_blackbox/051_blackbox.md)**

