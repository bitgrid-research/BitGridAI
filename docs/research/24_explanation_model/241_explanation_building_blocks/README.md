# 24.1 – Bausteine einer Erklärung

Dieses Unterkapitel beschreibt die **elementaren Bestandteile**, aus denen sich eine verständliche und konsistente Erklärung zusammensetzt.
Die Bausteine sind **konzeptionell definiert** und unabhängig von konkreten Interfaces oder Darstellungsformen.

Ziel ist es, sicherzustellen, dass jede Erklärung:

* aus der Entscheidungslogik ableitbar ist,
* für Nutzer:innen verständlich bleibt,
* und über Logs, UI und Analyse hinweg konsistent verwendet werden kann.

&nbsp;

## Auslöser und Regelbezug

Der erste Baustein einer Erklärung ist der **Auslöser** in Verbindung mit dem **Regelbezug**.

Der Auslöser beschreibt, **welche Bedingung oder Regelkonstellation** zu einer Entscheidung geführt hat.
Er verweist explizit auf die zugrunde liegende Entscheidungsregel (z. B. R1–R5).

Typische Auslöser sind:

* das Erreichen oder Unterschreiten eines Schwellenwerts,
* das Eintreten eines zeitlichen Ereignisses (z. B. Ablauf eines Deadbands),
* ein Sicherheitsereignis (Override).

Der Regelbezug beantwortet die Frage:

> *Welche Regel war ausschlaggebend für diese Entscheidung?*

Durch den expliziten Regelbezug bleibt die Erklärung überprüfbar und nicht interpretationsabhängig.

&nbsp;

## Relevante Datenbasis

Der zweite Baustein benennt die **konkreten Zustands- und Messdaten**, auf die sich die Entscheidung stützt.

Die Datenbasis umfasst ausschließlich jene Informationen, die **entscheidungsrelevant** waren, nicht den vollständigen Systemzustand.

Beispiele für relevante Daten:

* aktueller PV-Überschuss,
* Ladezustand des Speichers (SoC),
* Temperatur oder Health-Zustand,
* Prognose- oder Stabilitätsstatus.

Die Datenbasis beantwortet die Frage:

> *Worauf hat sich das System bei dieser Entscheidung gestützt?*

Eine begrenzte, selektive Datenbasis reduziert kognitive Belastung und verhindert Erklärungsüberfrachtung.

&nbsp;

## Wirkung

Der Wirkungs-Baustein beschreibt, **was das System entschieden hat**.

Mögliche Wirkungen sind:

* Starten einer Aktion,
* Stoppen einer Aktion,
* Drosselung,
* bewusstes Nicht-Handeln (`NOOP`).

Die Wirkung wird **klar und eindeutig** formuliert und vermeidet technische Detailtiefe.

Sie beantwortet die Frage:

> *Was hat das System getan – oder bewusst nicht getan?*

&nbsp;

## Mögliche Alternativen

Der Alternativen-Baustein beschreibt, **welche Handlungsoptionen prinzipiell bestanden hätten**, auch wenn sie nicht gewählt wurden.

Alternativen können explizit oder implizit kommuniziert werden und dienen insbesondere:

* dem Aufbau realistischer mentaler Modelle,
* der Nachvollziehbarkeit von Restriktionen,
* der späteren Analyse und Optimierung.

Beispiele:

* Start wäre ohne aktives Deadband möglich gewesen,
* Weiterbetrieb wäre ohne Sicherheitslimit erlaubt gewesen.

Der Alternativen-Baustein beantwortet die Frage:

> *Was hätte das System grundsätzlich auch tun können?*

&nbsp;

## Zusammenspiel der Bausteine

Eine vollständige Erklärung ergibt sich aus der **Kombination aller Bausteine**:

1. **Auslöser / Regelbezug** – warum jetzt?
2. **Datenbasis** – auf welcher Grundlage?
3. **Wirkung** – was (nicht) getan wurde?
4. **Alternativen** – was grundsätzlich möglich gewesen wäre?

Nicht jeder Baustein muss in jeder Situation vollständig dargestellt werden.
Die zugrunde liegende Struktur bleibt jedoch stets erhalten und bildet die **semantische Basis** aller Erklärungen.

&nbsp;

## Einordnung

Die hier definierten Bausteine bilden das **fundamentale Vokabular des Erklärungsmodells**.
Im nächsten Unterkapitel wird gezeigt, **wie diese Bausteine systematisch aus den Entscheidungsregeln abgeleitet** und in verständliche Aussagen überführt werden.




---

> **Nächster Schritt:** Im nächsten Unterkapitel folgt die Ableitung aus Regeln.
>
> 👉 Weiter zu **[24.2 - Ableitung von Regeln zu erklärbaren Aussagen](../242_rule_to_statement_mapping/README.md)**
>
> 🔙 Zurück zu **[24 - Erklärungsmodell](../README.md)**
>
> 🔙 Zurück zu **[2 - Forschung](../../README.md)**
>
> 🏠 Zurück zur **[Hauptübersicht](../../../README.md)**
