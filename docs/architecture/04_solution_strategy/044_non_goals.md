# 04.4 - Abgrenzungen & bewusste Nicht-Ziele (Fokus)

Fokus durch Weglassen.

Eine gute Architektur erkennt man nicht nur daran, **was sie kann**, sondern vor allem daran, **was sie bewusst nicht versucht**.

In diesem Kapitel halten wir fest, welche Ziele **BitGridAI ausdrücklich nicht verfolgt**. Diese Abgrenzungen sind keine Schwächen, sondern notwendige Leitplanken, um Komplexität zu begrenzen, Qualität zu sichern und den Charakter des Systems zu bewahren.

Wir beantworten hier die Frage:

> **Was wird BitGridAI nicht sein – und warum ist das eine gute Entscheidung?**

*(Platzhalter für ein Bild: Der Hamster streicht auf einer Liste mehrere Optionen durch und zeigt zufrieden auf eine kurze, klare Auswahl.)*

&nbsp;

## Bewusste Nicht-Ziele – Überblick 🚫

| Nr. | Nicht-Ziel | Abgrenzung | Warum bewusst nicht | Stattdessen |
| :-- | :-- | :-- | :-- | :-- |
| 1 | **Keine Black-Box-KI**🤖❌ | Keine selbstlernenden, undurchsichtigen Modelle im Entscheidungskern | • Entscheidungen müssen erklärbar sein<br>• Ergebnisse müssen reproduzierbar bleiben<br>• Vertrauen entsteht durch Nachvollziehbarkeit | Deterministische Regeln (R1–R5) mit klaren Triggern und erklärbaren Decision-Events |
| 2 | **Keine Cloud-Abhängigkeit**☁️❌ | Kein cloud-zentrierter Betrieb, keine Pflichtanbindung | • Energiedaten sind sensibel<br>• Internet darf kein Single Point of Failure sein<br>• Resilienz vor Komfort | Local-First-Betrieb mit optionalen, klar begrenzten externen Schnittstellen |
| 3 | **Kein Smart-Home-Allzwecksystem**🏠⚙️❌ | Kein universelles Smart-Home-Framework | • Feature-Inflation gefährdet Wartbarkeit<br>• Energie & Mining haben spezielle Anforderungen | Fokussierte Energie- & Mining-Orchestrierung, Integration statt Ersatz (z.B. Home Assistant) |
| 4 | **Keine Hard-Real-Time-Steuerung**⏱️❌ | Kein Millisekunden- oder Echtzeitregelsystem | • Energieflüsse sind träge<br>• Echtzeit erhöht Komplexität und Fehleranfälligkeit | Ruhiger 10-Minuten-Takt mit klaren Entscheidungszyklen |
| 5 | **Keine Verwahrung von Geldern**💰❌ | Keine Wallets, keine Auszahlungen, kein Custody | • Hohe regulatorische Risiken<br>• Sicherheit durch Trennung von Verantwortung | Non-custodial Ansatz: Erträge fließen direkt vom Pool zum Nutzer |
| 6 | **Keine versteckten Automatiken**👻❌ | Keine stillen, nicht einsehbaren Entscheidungen | • Intransparenz untergräbt Vertrauen<br>• Nutzer müssen Kontrolle behalten | Jede Aktion ist sichtbar, erklärbar und übersteuerbar |


---
> **Nächster Schritt:** Die Strategie ist vollständig. Jetzt wird es konkret: Wir zerlegen BitGridAI in seine **konkreten Bausteine**.
>
> 👉 Weiter zu **[05 - Bausteinsicht](../05_building_block_view/README.md)**
>
> 🔙 Zurück zur **[Kapitelübersicht](./README.md)**
