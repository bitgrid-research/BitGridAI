# ₿itsy-Dev

₿itsy-Dev ist der technische KI-Sparringspartner im BitGridAI-Projekt. Er läuft lokal auf Umbrel (`umbrel.local:18789`) auf Basis von Qwen3:14b und analysiert das Repository eigenständig — ohne Schreibzugriff auf den produktiven Code.

Seine Hauptaufgabe ist das arc42-Review: Er liest die Architekturdokumentation, erkennt Inkonsistenzen oder fehlende Abschnitte und schreibt seine Befunde nach `FINDINGS.md` in diesem Verzeichnis. Claude Code prüft die Findings und setzt berechtigte Korrekturen um.

Mehr zum Kollaborationsprotokoll: [`../COLLABORATION.md`](../COLLABORATION.md)
