# 05.2.5.3 Observability & Monitoring

Sehen, was wirklich los ist.

Dieses Modul sorgt dafür, dass BitGridAI **nicht im Blindflug läuft**.
Zustände, Metriken und Warnungen aus allen Bausteinen werden gesammelt,
zusammengeführt und verständlich sichtbar gemacht.

Nicht für Buzzwords – sondern für Betriebssicherheit.

*(Platzhalter für ein Bild: Der Hamster steht mit Fernglas und Klemmbrett vor mehreren Anzeigen.
Diagramme zeigen Health, Last und Warnsymbole.)*
![Hamster Observability](../media/pixel_art_observability_monitoring.png)

---

## Verantwortung

- Sammeln von Health-, Metrik- und Log-Signalen
- Konsolidierte Sicht auf den Systemzustand
- Auslösen und Weiterleiten von Warnungen

---

## Struktur

- **Health Aggregator**  
  Konsolidiert Health-Signale aus Core, Adaptern, UI und Operations.

- **Metrics Collector**  
  Erfasst zentrale Betriebsmetriken wie Latenzen, Durchsatz, Fehlerquoten und Queue-Zustände.

- **Alert Router**  
  Bewertet Schwellen und leitet Warnungen an UI und Logs weiter.

---

## Schnittstellen

**Provided**
- Health-Status (ok / warn / error)
- Metrik-Feeds und Trenddaten
- Alerts und Warnmeldungen

**Required**
- Health- und Metrik-Signale aus allen Bausteinen
- Optional: Log- oder Export-Senken

---

## Ablauf (vereinfacht)

1) Bausteine senden Health- und Metrik-Events  
2) Aggregator und Collector bereiten Daten auf  
3) Alert Router prüft Schwellen und meldet Auffälligkeiten  
4) UI und Logs zeigen aktuellen Zustand und Historie

---

## Qualitäts- und Betriebsaspekte

- **Zentral:** ein Blick statt vieler Einzelchecks  
- **Konfigurierbar:** Schwellen und Alarmregeln anpassbar  
- **Local-first:** keine Abhängigkeit von externen APM-Diensten  

---

> 🔙 Zurück zu **[5.2.5.x Operations (Level 3)](./README.md)**  
> 🔙 Zurück zu **[5.2.5 Whitebox Operations](../0525_operations_whitebox.md)**
