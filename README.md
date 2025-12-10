# BitGridAI

Lokale Energie‑Automatisierung. Ohne Cloud. Verständlich erklärt.

Doku: [./docs/README.md](./docs/README.md)

![Welcome](./docs/media/welcome.png)


---

## Fortschritt

![Status](https://img.shields.io/badge/Status-Konzeptphase_(MVP_Architektur)-blue)


![Status](./docs/media/status.png)


---

## Kurz erklärt
BitGridAI nutzt **PV-Überschuss** automatisch – z. B. für **Bitcoin-Mining als flexible Last**.  
Entscheidungen sind **nachvollziehbar**: Jede Aktion kommt mit Begründung und Parametern.

![Overview](./docs/media/overview_hamster.png)


## Was umfasst das MVP?
- **Regeln (R1–R5):** Start/Stop, SoC-Schutz, Temperaturschutz, Prognose, Deadband
- **Erklärungen:** Verständliche Begründung zu jeder Entscheidung
- **Home Assistant/Docker:** Integration lokaler Sensoren und Aktoren zur Entscheidungs- und Steuerlogik
- **Steuerung:** Miner starten, stoppen, pausieren; Sperrzeiten berücksichtigen
- **Protokoll:** Entscheidungen dokumentiert, ergänzt um einfache Kennzahlen
  
---

<details>
<summary><strong>⚡ Transparenz & Unterstützung (optional)</strong></summary>
&nbsp;

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

&nbsp;

⚠️ **Kurzer Sicherheitshinweis** 

Damit alles zuverlässig funktioniert, lohnt sich ein schneller Blick auf ein paar bewährte Vorgehensweisen:

 - Prüfe die vollständige Empfangsadresse direkt auf deiner **Hardware-Wallet**.
 - Nutze eine Wallet-App, der du vertraust und die idealerweise quelloffen ist. 
- Vergleiche die angezeigte Adresse mit der hier angegebenen, bevor du fortfährst.  

 So wird sichergestellt, dass die Zieladresse **nicht durch UI-Fakes oder Schadsoftware manipuliert** wurde.  
**Fehleingaben oder manipulierte Adressen können zum unwiderruflichen Verlust von Mitteln führen.**  

Diese Hinweise sollen dir einfach helfen, Adressfehler oder Missverständnisse zu vermeiden.

Der QR-Code dient als Lern- und Demonstrationselement, um zu zeigen, wie sichere Selbstverwahrung und Transparenz praktisch funktionieren.

&nbsp;

### Transparenzbeleg

Alle eingehenden Transaktionen kannst du öffentlich einsehen.
Sie erscheinen zunächst im Mempool, bevor sie dauerhaft in die Blockchain übernommen werden.

**Beispiele:**  
- [https://mempool.space/address/bc1qvkdu9q8nprf4n52tmdx8p29xm40xxajwcgams2](https://mempool.space/address/bc1qvkdu9q8nprf4n52tmdx8p29xm40xxajwcgams2)  
- [https://blockstream.info/address/bc1qvkdu9q8nprf4n52tmdx8p29xm40xxajwcgams2](https://blockstream.info/address/bc1qvkdu9q8nprf4n52tmdx8p29xm40xxajwcgams2)

 💡 **Hinweis**  
 Custodial-Produkte („Paper Bitcoin“) ermöglichen oft keine echten On-Chain-Transaktionen. BitGridAI nutzt On-Chain-Transparenz bewusst, um Selbstverwahrung und Dezentralität im Forschungsumfeld sichtbar und nachvollziehbar zu machen.  

&nbsp;
</details>

---

![NoCloud](./docs/media/nocloud.png)

### Lizenz / Kontakt
AGPL-3.0 — **bitgrid.research@proton.me**
