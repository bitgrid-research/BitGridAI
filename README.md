# BitGridAI

Lokale Energie‑Automatisierung. Ohne Cloud. Verständlich erklärt.

* [📚 Doku](./docs/README.md)

![Welcome](./docs/media/welcome.png)


---

## Fortschritt

![Status](https://img.shields.io/badge/Status-Konzeptphase_(MVP_Architektur)-blue)


![Status](./docs/media/status.png)


---

## Kurz erklärt
BitGridAI nutzt **PV-Überschuss** automatisch – z. B. für **Bitcoin-Mining als flexible Last**. Entscheidungen sind **nachvollziehbar**: Jede Aktion kommt mit Begründung und Parametern.

Das Projekt fokussiert sich auf lokale Energie-Automatisierung, transparente Entscheidungslogik und Selbstverwahrung.

![Overview](./docs/media/overview_hamster.png)


## Was umfasst das MVP?
- **Regeln (R1–R5):** Start/Stop, SoC-Schutz, Temperaturschutz, Prognose, Deadband
- **Erklärungen:** Verständliche Begründung zu jeder Entscheidung
- **Home Assistant/Docker:** Integration lokaler Sensoren und Aktoren zur Entscheidungs- und Steuerlogik
- **Steuerung:** Miner starten, stoppen, pausieren; Sperrzeiten berücksichtigen
- **Protokoll:** Entscheidungen dokumentiert, ergänzt um einfache Kennzahlen

## Kontext

Als **offenes Forschungs- und Lernprojekt** widmet sich BitGridAI der lokalen Energie-Automatisierung.
Im Mittelpunkt stehen **nachvollziehbare Entscheidungen** und **transparente Steuerlogik** – nicht Produktbetrieb oder wirtschaftliche Versprechen.

Die gezeigten Konzepte und Beispiele (z. B. Bitcoin-Mining als flexible Last) dienen der **Demonstration**.
Der praktische Einsatz elektrischer Verbraucher erfolgt **in eigener Verantwortung** unter Beachtung lokaler Vorgaben.

Die Software wird als Open Source im aktuellen Forschungsstand bereitgestellt.

<details>
<summary><strong>⚡ Transparenz & Unterstützung (optional)</strong></summary>
&nbsp;

Ein offenes Wort zur Entstehung: Da ich dieses Projekt noch alleine erforsche, setze ich bewusst auf KI-Unterstützung und generierte Grafiken, um meine Fähigkeiten am Projektzweck zu schulen und das Ergebnis mit viel Liebe zum Detail umzusetzen.

Ich freue mich, wenn dir meine Inhalte weiterhelfen. Falls du meine Projekt rund um Energie, Bitcoin und Selbstverwahrung unterstützen möchtest, findest du hier eine optionale Adresse und einen QR-Code. Alles selbstverständlich transparent und nachvollziehbar.
&nbsp;
<table border="0">
  <tr>
    <td>
      <img src="./docs/media/bitgrid_donation_qr.png" width="120" />
      <img src="./docs/media/bithamster.png" width="120" />
    </td>
    <td>
      <code>Ich mache Energie & Bitcoin verständlich.
Dein Support fließt in offene Lern- und Demo-Projekte 
zu Selbstverwahrung & Transparenz.</code>
    </td>
  </tr>
</table>

```text
bc1qvkdu9q8nprf4n52tmdx8p29xm40xxajwcgams2
```

 💡 **Hinweis zur Unterstützung**
 
 Die genannte Bitcoin-Adresse dient der **freiwilligen Unterstützung ohne Gegenleistung**. Es besteht kein Anspruch auf Funktionen, Support oder Einfluss auf das Projekt. Bitcoin-Transaktionen sind technisch **unumkehrbar**. Bitte prüfe die Zieladresse sorgfältig – idealerweise direkt auf deiner Hardware-Wallet. Der QR-Code ist ein **Lern- und Demonstrationselement** für transparente On-Chain-Selbstverwahrung.

&nbsp;

### Transparenzbeleg

Alle eingehenden Transaktionen kannst du öffentlich einsehen.
Sie erscheinen zunächst im Mempool, bevor sie dauerhaft in die Blockchain übernommen werden.

**Beispiele:**  
- [https://mempool.space/address/bc1qvkdu9q8nprf4n52tmdx8p29xm40xxajwcgams2](https://mempool.space/address/bc1qvkdu9q8nprf4n52tmdx8p29xm40xxajwcgams2)  
- [https://blockstream.info/address/bc1qvkdu9q8nprf4n52tmdx8p29xm40xxajwcgams2](https://blockstream.info/address/bc1qvkdu9q8nprf4n52tmdx8p29xm40xxajwcgams2)

 💡 **Hinweis zur On-Chain-Transparenz**  
 
 Custodial-Produkte („Paper Bitcoin“) ermöglichen oft keine echten On-Chain-Transaktionen. BitGridAI nutzt On-Chain-Transparenz bewusst, um Selbstverwahrung und Dezentralität im Forschungsumfeld sichtbar und nachvollziehbar zu machen.  

&nbsp;
</details>

---

![NoCloud](./docs/media/nocloud.png)

### Lizenz / Kontakt
AGPL-3.0 — **bitgrid.research@proton.me**
