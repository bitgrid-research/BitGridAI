# BitGridAI

Lokale Energie‑Automatisierung. Ohne Cloud. Verständlich erklärt.

Doku: [./docs/README.md](./docs/README.md)

---

## Status
- [x] ~~Scoping & Research~~
- [x] ~~Ideation & Synthese~~
- [ ] Konzept (MVP Architektur)
- [ ] Prototyping: HA-Adapter, R1–R5 Basis
- [ ] Validierung: Aufgaben & KPIs
- [ ] Roadmap/Backlog finalisieren
- [ ] Delivery: Sprint 0
- [ ] Delivery: Sprint 1


---

## Kurz erklärt
BitGridAI nutzt **PV-Überschuss** automatisch – z. B. für **Bitcoin-Mining als flexible Last**.  
Entscheidungen sind **nachvollziehbar**: Jede Aktion kommt mit Begründung und Parametern.

![Core-Prinzip](./docs/media/core_principle.png)

---

## Was kann’s (MVP)
- **Regeln (R1–R5):** Start/Stop, SoC-Schutz, Temperaturschutz, Prognose, Deadband
- **Erklärungen:** Klarer Grundtext zu jeder Entscheidung
- **Home Assistant:** Lokale Sensoren/Aktoren, kein Cloud-Zwang
- **Steuerung:** Miner an/aus/pause, Sperrzeiten
- **Protokoll:** Entscheidungen & einfache Kennzahlen
  
---

## Schnellzugriffe
- Architektur → [./docs/architecture](./docs/architecture/01_introduction_and_goals.md)
- Prinzipien → [./docs/media/...](./docs/research/bitgrid_principles.md)
- Datenmodell → `...`
- Home-Assistant Setup → `...`
---

<details>
<summary><strong>Transparenz & Unterstützung (optional)</strong></summary>

Offenes Forschungsprojekt an der Schnittstelle von Energieoptimierung und HCI.  
Freiwillige Beiträge dienen Lern- und Demonstrationszwecken (Selbstverwahrung, On-Chain-Transparenz).

<img src="./docs/media/bitgrid_donation_qr.png" alt="Bitcoin QR" width="120" style="border:1px solid #ddd; border-radius:8px; padding:4px;"/>

```text
bc1qvkdu9q8nprf4n52tmdx8p29xm40xxajwcgams2
```

⚠️ **Sicherheitshinweis / Security Disclaimer**  
Adresse niemals abtippen. Gesamte Empfangsadresse, besonders Anfang und Ende, direkt auf der Hardware-Wallet prüfen.

 - Verwende **ausschließlich eine Hardware-Wallet mit eigenem Display**, um die Empfangsadresse visuell zu verifizieren.  
 - Scanne den QR-Code nur mit **vertrauenswürdiger, quelloffener Wallet-Software**.  
- Vergleiche die Adresse auf dem Display deiner Hardware-Wallet mit der hier angegebenen Adresse.  

 So wird sichergestellt, dass die Zieladresse **nicht durch UI-Fakes oder Schadsoftware manipuliert** wurde.  
**Fehleingaben oder manipulierte Adressen können zum unwiderruflichen Verlust von Mitteln führen.**  

Der QR-Code dient ausschließlich als **Lern- und Demonstrationselement**, um  
sichere Selbstverwahrung und überprüfbare Transparenz praktisch zu vermitteln.  


### Transparenzbeleg / Transparency Reference

Alle eingehenden Transaktionen sind öffentlich einsehbar.  
Sie erscheinen zunächst im **Mempool** (Memory Pool) – dem globalen Wartebereich  
für unbestätigte Transaktionen – bevor sie dauerhaft in die Blockchain geschrieben werden.


**Beispiele / Examples:**  
- [https://mempool.space/address/bc1qvkdu9q8nprf4n52tmdx8p29xm40xxajwcgams2](https://mempool.space/address/bc1qvkdu9q8nprf4n52tmdx8p29xm40xxajwcgams2)  
- [https://blockstream.info/address/bc1qvkdu9q8nprf4n52tmdx8p29xm40xxajwcgams2](https://blockstream.info/address/bc1qvkdu9q8nprf4n52tmdx8p29xm40xxajwcgams2)

 💡 **Hinweis / Note:**  
 Custodial-Produkte („Paper Bitcoin“) ermöglichen oft keine echten On-Chain-Transaktionen.  
 BitGridAI nutzt On-Chain-Transparenz bewusst, um Selbstverwahrung und Dezentralität im  
 Forschungsumfeld sichtbar und nachvollziehbar zu machen.  


</details>

---

### Lizenz / License
AGPL-3.0 — **bitgrid.research@proton.me**
