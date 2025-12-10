# 02.3 Leitplanken & Konventionen (Conventions)

Damit aus Software kein Chaos wird.

Wir haben ein gemeinsames Ziel und nutzen die gleiche Technik. Aber wie arbeiten wir *wirklich* zusammen? In diesem Kapitel definieren wir unsere "internen Gesetze". Das sind die Spielregeln für Code, Kommunikation und Struktur.

Sie existieren nicht, um uns zu gängeln, sondern damit wir uns im Code des anderen zurechtfinden, Fehler vermeiden und effizient vorankommen. Kurz gesagt: Damit das Ganze wie aus einem Guss wirkt und nicht wie ein Flickenteppich.

*(Platzhalter für ein Bild: Ein Pixel-Art-Hamster mit einer strengen Brille hält ein dickes Regelbuch und einen Stempel in der Hand. Neben ihm ein Zollstock.)*
![Hamster mit dem Regelwerk](link_zum_konventionen_bild.png)

## Unsere Konventionen

Diese Standards gelten für jeden, der Code oder Dokumentation zu BitGridAI beiträgt:

| Bereich & ID | Konvention | Beschreibung & Tools |
| :--- | :--- | :--- |
| **Code-Style (Python)** 🐍 | **PEP 8 & Black** | Wir folgen dem offiziellen Python Style Guide (PEP 8).<br>**Tooling:** Wir nutzen den `Black` Auto-Formatter ("The Uncompromising Code Formatter"), um Diskussionen über Formatierung zu beenden. Check im CI-Prozess. |
| **Typisierung** 🏷️ | **Strikte Type Hints** | Moderner Python-Code muss typisiert sein. Jede Funktionssignatur sollte Type Hints für Argumente und Rückgabewerte haben.<br>**Tooling:** `mypy` im strikten Modus zur statischen Analyse. |
| **Dokumentation im Code** 📝 | **Google Style Docstrings** | Jede öffentliche Klasse und Funktion benötigt einen Docstring, der Zweck, Parameter, Rückgabewerte und mögliche Exceptions erklärt. Wir nutzen das "Google Style" Format.<br>**Sprache:** Englisch. |
| **Sprache & Benennung** 🗣️ | **English Only & Sprechende Namen** | Code (Variablen, Funktionen, Klassen) und Kommentare sind zwingend auf Englisch.<br>**Prinzip:** Namen müssen selbsterklärend sein. Lieber `calculate_average_power_consumption()` als `calc_avg_p()`. |
| **Git Workflow** 🌳 | **Feature Branches & Conventional Commits** | Direkte Pushes auf `main` sind verboten. Arbeit passiert in Feature-Branches. Wir nutzen "Conventional Commits" für klare Commit-Nachrichten (z.B. `feat: add modbus tcp adapter for SMA inverters` oder `fix: resolve deadband flapping bug`). |
| **Architektur-Regeln** 🏛️ | **Schichten einhalten!** | Die in Kapitel 4 und 5 definierte Schichtenarchitektur ist bindend. Beispiel: Ein Hardware-Adapter darf niemals direkt in die Datenbank schreiben, sondern muss immer über die definierte Schnittstelle des Kern-Systems gehen. |
| **MQTT Topic-Struktur** 📡 | **Hierarchisch & Konsistent** | MQTT Topics folgen dem Schema: `bitgridai/<location>/<device_type>/<device_id>/<measurement>`.<br>Beispiel: `bitgridai/home/inverter/sma_sunnyboy_1/active_power_w`. |

---
> **Nächster Schritt:** Puh, das waren viele Regeln. Aber jetzt, wo das Fundament steht, können wir den Blick heben. Im nächsten Kapitel malen wir das große Bild und schauen uns an, wie BitGridAI in seine Umwelt eingebettet ist.
>
> 👉 Weiter zu **[03 Kontextabgrenzung](../03_context)**
>
> 🔙 Zurück zur **[Kapitelübersicht](./README.md)**
