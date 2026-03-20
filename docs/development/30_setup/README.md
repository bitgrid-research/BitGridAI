# 30 – Setup & Umgebung

Wer neu ins Projekt einsteigt, beginnt hier.

Dieses Kapitel führt durch alles, was nötig ist, um **BitGridAI lokal zum Laufen zu bringen** –
vom SSH-Zugang zum Edge-Gerät bis zur vollständigen Entwicklungsumgebung auf dem eigenen Rechner.

Das Ziel: Nach Kapitel 30 kannst du Code schreiben, den Stack starten und Änderungen testen –
ohne Internetverbindung, ohne Cloud, ohne Umwege.

&nbsp;

## Inhalt dieses Kapitels

* **[30.1 – SSH unter Windows/Linux](./ssh_windows_setup.md)**
    * SSH-Schlüssel erzeugen, zum Edge-Gerät (Umbrel/NUC/Pi) verbinden,
      `~/.ssh/config` für bequemen Zugriff einrichten.

* **[30.2 – Entwicklungsumgebung](./dev_environment.md)**
    * Voraussetzungen, Repository klonen, Python-Umgebung, Docker-Stack starten,
      VSCode und Claude Code konfigurieren.

---

## Voraussetzungen auf einen Blick

| Was | Wozu |
|-----|------|
| **Windows 10/11** oder Linux | Entwicklungsrechner |
| **Python 3.11+** | Kernlogik, Tests, Tooling |
| **Docker Desktop** (Windows) / Docker Engine (Linux) | Stack lokal starten |
| **Git** | Repository-Zugriff |
| **VSCode + Claude Code Extension** | Entwicklungsumgebung |
| **Edge-Gerät im LAN** (Pi, NUC, Umbrel) | Ziel-Deployment für Integrationstests |

&nbsp;

## Reihenfolge empfohlen

```
30.1  →  SSH einrichten
30.2  →  Entwicklungsumgebung aufsetzen
31    →  Projektstruktur verstehen
32    →  Mit dem ersten Branch loslegen
```

---

<img src="../../media/setup/setup.png" alt="Setup" width="1000" />

---

> **Nächster Schritt:** Umgebung eingerichtet.
> Jetzt die Projektstruktur kennenlernen.
>
> 👉 Weiter zu **[31 – Projektstruktur](../31_project_structure/README.md)**
>
> 🔙 Zurück zu **[3 – Entwicklung](../README.md)**
>
> 🏠 Zurück zur **[Hauptübersicht](../../README.md)**
