# 05.2.5.3 Observability & Monitoring

Verantwortung: sammelt Health/Metriken/Logs aus Core, Adaptern, UI und macht sie sichtbar/alertbar.

## Struktur

- **Health Aggregator:** konsolidiert Health-Signale aus Bausteinen.
- **Metrics Collector:** sammelt Kernmetriken (z.B. Latenzen, Durchsatz, Buffer, Fehler).
- **Alert Router:** leitet Warnungen/Alarme an UI/Logs weiter.

## Schnittstellen

- **Provided:** Health- und Metrik-Feeds, Alerts/Warnings.
- **Required:** Health/Metrik-Signale aus Bausteinen, optional Export/Log-Senke.

## Ablauf (vereinfacht)

1) Health/Metrik-Events kommen rein.  
2) Aggregator/Collector bereitet sie auf.  
3) Alert Router meldet Warnungen/Errors an UI/Logs.

## Qualitaet und Betrieb

- Ein zentraler Blick auf Zustand und Trends.  
- Schwellen/Alarme konfigurierbar.  
- Keine Abhaengigkeit von externen APM-Diensten.

---
> Zurueck zu **[5.2.5.x Operations (Level 3)](./README.md)**  
> Zurueck zu **[5.2.5 Whitebox Operations](../0525_operations_whitebox.md)**
