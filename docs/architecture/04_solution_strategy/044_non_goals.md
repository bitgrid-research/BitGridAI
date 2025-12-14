# 04.4 Abgrenzungen & bewusste Nicht-Ziele

Fokus durch Weglassen.

Eine gute Architektur erkennt man nicht nur daran, **was sie kann**, sondern vor allem daran, **was sie bewusst nicht versucht**.

In diesem Kapitel halten wir fest, welche Ziele **BitGridAI ausdrücklich nicht verfolgt**. Diese Abgrenzungen sind keine Schwächen, sondern notwendige Leitplanken, um Komplexität zu begrenzen, Qualität zu sichern und den Charakter des Systems zu bewahren.

Wir beantworten hier die Frage:

> **Was wird BitGridAI nicht sein – und warum ist das eine gute Entscheidung?**

*(Platzhalter für ein Bild: Der Hamster streicht auf einer Liste mehrere Optionen durch und zeigt zufrieden auf eine kurze, klare Auswahl.)*

---

## Nicht-Ziel 1: Keine autonome Black-Box-KI

**Abgrenzung:**
BitGridAI ist **keine selbstlernende, undurchsichtige KI**, die Entscheidungen ohne erklärbare Regeln trifft.

**Warum nicht:**

* Black-Box-Modelle sind schwer erklärbar und kaum überprüfbar.
* Vertrauen entsteht nicht durch Optimierung, sondern durch Nachvollziehbarkeit.
* Forschung erfordert reproduzierbare, deterministische Ergebnisse.

**Stattdessen:**
Explizite Regeln, klare Trigger und erklärbare Decision-Events.

---

## Nicht-Ziel 2: Keine Cloud-Abhängigkeit

**Abgrenzung:**
BitGridAI ist **kein Cloud-zentrierter Service** und benötigt keine permanente Internetverbindung.

**Warum nicht:**

* Energiedaten sind sensibel und gehören dem Nutzer.
* Abhängigkeiten von externen Diensten reduzieren Resilienz.
* Offline-Betrieb ist ein Muss, kein Nice-to-have.

**Stattdessen:**
Local-First-Betrieb mit optionalen, klar abgegrenzten externen Schnittstellen.

---

## Nicht-Ziel 3: Kein universelles Smart-Home-Framework

**Abgrenzung:**
BitGridAI ist **kein generisches Smart-Home-Betriebssystem**.

**Warum nicht:**

* Breite Plattformen verlieren schnell Fokus.
* Energieoptimierung und Mining-Steuerung haben sehr spezifische Anforderungen.
* Wartbarkeit leidet unter Feature-Inflation.

**Stattdessen:**
Klare Integration in bestehende Systeme (z.B. Home Assistant), ohne diese ersetzen zu wollen.

---

## Nicht-Ziel 4: Keine Echtzeit-Millisekunden-Steuerung

**Abgrenzung:**
BitGridAI ist **kein Hard-Real-Time-System**.

**Warum nicht:**

* Energieflüsse ändern sich nicht im Millisekundenbereich.
* Echtzeit-Garantien erhöhen Komplexität und Fehleranfälligkeit.
* Der Fokus liegt auf Stabilität, nicht auf maximaler Reaktionsgeschwindigkeit.

**Stattdessen:**
Ein bewusster, ruhiger 10-Minuten-Takt mit klaren Entscheidungszyklen.

---

## Nicht-Ziel 5: Kein finanzieller Verwahrer oder Broker

**Abgrenzung:**
BitGridAI verwaltet **keine Gelder, Wallets oder Auszahlungen**.

**Warum nicht:**

* Finanzielle Verwahrung erhöht regulatorische Risiken erheblich.
* Trennung von Steuerung und Auszahlung erhöht Sicherheit.
* Nutzer behalten volle Kontrolle über ihre Erträge.

**Stattdessen:**
Non-custodial Ansatz: Mining-Erträge fließen direkt vom Pool zum Nutzer.

---

## Nicht-Ziel 6: Keine versteckten Automatiken

**Abgrenzung:**
BitGridAI trifft **keine stillen Entscheidungen im Hintergrund**, die nicht einsehbar oder erklärbar sind.

**Warum nicht:**

* Intransparente Automatiken untergraben Vertrauen.
* Nutzer müssen jederzeit verstehen können, was passiert.

**Stattdessen:**
Jede relevante Aktion ist sichtbar, erklärbar und bei Bedarf übersteuerbar.

---

## Einordnung (arc42)

Dieses Kapitel definiert die **bewussten Systemgrenzen** von BitGridAI.

Es ergänzt:

* **04.1 Leitende Architekturprinzipien** (Werte)
* **04.2 Grobe Systemstruktur** (Form)
* **04.3 Zentrale Architekturentscheidungen** (Weichenstellungen)

Zusammen bilden diese Kapitel den strategischen Rahmen, innerhalb dessen alle weiteren Architekturentscheidungen getroffen werden.

---

> **Nächster Schritt:** Die Strategie ist vollständig. Jetzt wird es konkret: Wir zerlegen BitGridAI in seine **konkreten Bausteine**.
>
> 👉 Weiter zu **[05 Bausteinsicht](../05_building_block_view/README.md)**
>
> 🧭 Zurück zur **[Kapitelübersicht](./README.md)**
