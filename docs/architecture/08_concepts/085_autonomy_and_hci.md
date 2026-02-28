# 8.5 - Autonomie, HCI & menschliche Kontrolle

Kontrolle bewusst gestalten.

BitGridAI ist kein reines Automatisierungssystem und kein manuelles Tool.  
Es ist ein **kooperatives System**, in dem Mensch und Software gemeinsam Entscheidungen tragen.

Dieses Kapitel beschreibt die **systemweiten Leitlinien zur Autonomie und Mensch-Maschine-Interaktion (HCI)**.  
Sie legen fest, **wer wann entscheidet**, wie Kontrolle sichtbar bleibt und wie Selbstbestimmung und Komfort in Balance gehalten werden.

![Hamster teilt sich die Kontrolle](../../media/architecture/08_concepts/bithamster_08.png)

&nbsp;

## Ziel der Autonomiegestaltung

Die Autonomiegestaltung von BitGridAI verfolgt vier Hauptziele:

1. **Selbstbestimmung ermöglichen**  
   Der Nutzer behält jederzeit die Kontrolle über das System.

2. **Komfort bieten**  
   Automatisierung soll entlasten, nicht bevormunden.

3. **Vertrauen aufbauen**  
   Entscheidungen sind erklärbar und vorhersehbar.

4. **Sicherheit garantieren**  
   Autonomie darf niemals Sicherheitsprinzipien unterlaufen.

&nbsp;

## Grundprinzipien

Die Mensch-Maschine-Interaktion in BitGridAI folgt klaren Regeln:

- **Explizite Autonomie**  
  Der Autonomiegrad ist immer sichtbar und bewusst gewählt.

- **Kein Alles-oder-Nichts**  
  Automatisierung erfolgt abgestuft, nicht binär.

- **Eingriff bleibt möglich**  
  Der Mensch kann jederzeit eingreifen – innerhalb sicherer Grenzen.

- **Sicherheit ist orthogonal**  
  Sicherheitsregeln gelten unabhängig vom Autonomie-Level.

&nbsp;

## Autonomie-Stufen

BitGridAI unterscheidet mehrere Autonomie-Stufen, die systemweit gelten:

### Stufe 0 – Manuell  
Der Nutzer trifft alle Entscheidungen selbst.  
Das System beobachtet und sichert ab.

### Stufe 1 – Assistiert  
Das System analysiert und macht Vorschläge.  
Der Nutzer entscheidet.

### Stufe 2 – Halbautomatisch  
Das System darf Aktionen auslösen (z.B. Start),  
der Nutzer behält kritische Kontrolle (z.B. Stop).

### Stufe 3 – Vollautomatisch  
Das System steuert Start und Stop autonom.  
Der Nutzer definiert nur noch Rahmenbedingungen.

Diese Stufen sind fachliche Konzepte; konkrete Abläufe sind in Kapitel 6 beschrieben.

&nbsp;

## Manuelle Eingriffe (Overrides)

Manuelle Eingriffe sind ein zentrales HCI-Element.

**Grundsätze:**
- Overrides haben immer eine zeitliche Begrenzung (TTL).
- Overrides übersteuern Optimierungsregeln, nicht aber Safety.
- Aktive Overrides sind jederzeit sichtbar.

Overrides sind **bewusste Entscheidungen**, keine versteckten Schalter.

&nbsp;

## Rückmeldungen & Transparenz

Gute Autonomie erfordert klare Rückmeldungen:

- aktueller Autonomie-Modus ist sichtbar
- aktive Overrides werden deutlich angezeigt
- blockierte Aktionen werden begründet
- Sicherheitszustände sind klar erkennbar

Der Nutzer soll jederzeit wissen:
> *Was passiert gerade – und warum?*

&nbsp;

## Fehlervermeidung durch HCI

Viele Fehler entstehen durch Missverständnisse.

BitGridAI reduziert Fehlbedienung durch:
- klare Begriffe statt technischer Codes
- bestätigungspflichtige kritische Aktionen
- konservative Defaults
- erklärende Hinweise statt stiller Ablehnung

&nbsp;

## Autonomie & Lernen

BitGridAI lernt **nicht eigenmächtig** aus Nutzerverhalten.

- keine stillen Policy-Änderungen
- keine schleichende Autonomieerhöhung
- Änderungen erfolgen nur explizit

Das System bleibt vorhersehbar und kontrollierbar.

&nbsp;

## Abgrenzungen

Nicht Bestandteil dieses Kapitels sind:
- konkrete UI-Layouts
- Button-Beschriftungen
- Interaktionsdetails einzelner Screens

Diese werden in der UI-Dokumentation behandelt.

&nbsp;

## Zusammenfassung

Die Autonomie- und HCI-Prinzipien von BitGridAI stellen sicher, dass:

- Automatisierung unterstützend wirkt,
- menschliche Kontrolle erhalten bleibt,
- Sicherheit niemals kompromittiert wird.

BitGridAI automatisiert nicht *anstelle* des Menschen, sondern *mit* ihm.

---

> **Nächster Schritt:** Autonomie braucht klare Grenzen für Fehlerfälle.  
> Im nächsten Abschnitt betrachten wir die **Fehler-, Degradations- & Fail-safe-Prinzipien**.
>
> 👉 Weiter zu **[8.6 - Fehler-, Degradations- & Fail-safe-Prinzipien](./086_fail_safe_and_degradation.md)**
>
> 🔙 Zurück zur **[Kapitelübersicht](./README.md)**
