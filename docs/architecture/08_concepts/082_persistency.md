# 08.2 Persistenz (Datenhaltung)

Das Gedächtnis des Hamsters.

Da BitGridAI "Local-First" arbeitet, gibt es keine Cloud-Datenbank, die unsere Daten magisch sichert. Wir sind selbst dafür verantwortlich, dass Konfigurationen und historische Entscheidungen einen Neustart überleben und **auditierbar** bleiben.

Wir nutzen einen **hybriden Ansatz**, der die Stärken von relationalen Datenbanken mit modernen Big-Data-Formaten kombiniert.

*(Platzhalter für ein Bild: Ein Hamster als Bibliothekar, der Bücher in ein Regal sortiert (SQLite) und gleichzeitig große Kisten in ein Archiv stapelt (Parquet).)*
![Hamster sortiert Daten](../../media/pixel_art_hamster_librarian.png)

## Die Hybrid-Speicherstrategie

Wir trennen strikt nach Zweck und Charakteristik der Daten. Ein wichtiger Grundsatz ist **Append-only** für alle Log-Daten, um **Reproduzierbarkeit** und **Auditierbarkeit** zu gewährleisten.

| Datentyp | Technologie | Charakteristik | Zweck |
| :--- | :--- | :--- | :--- |
| **Operational State** 🔥 | **SQLite** | Schnell, transaktionssicher (ACID), Lese-/Schreibzugriff. | Aktueller Zustand (`EnergyState`), UI-Timeline-Daten, Session-Tokens, KPIs. |
| **Analytical Logs** ❄️ | **Apache Parquet / JSON** | Komprimiert, spaltenbasiert, **Append-only**. | Langzeit-Logs (`SensorLog`, `DecisionHistory`), Research-Export-Bundles. |
| **Configuration** ⚙️ | **YAML** | Menschenlesbar, versioniert, Checksums. | `config.yaml` (Regel-Parameter, Limits), Adapter-Einstellungen. |
| **Erklärungen** 💬 | **JSON** | Versionierte Prompt-/Result-Texte. | Gespeicherte `ExplainSessions` in DE/EN. |

---

## 1. SQLite (Das operative Gedächtnis)

Für alles, was die App *jetzt gerade* braucht, nutzen wir **SQLite**. Dies ist die Laufzeit-Datenbank (Runtime-DB).
* **Datei:** `data/bitgrid.db`
* **Modus:** Wir nutzen den **WAL-Mode (Write-Ahead Logging)**, da er robuster gegen Abstürze ist und die Performance auf Edge-Hardware verbessert.
* **Funktion:** Speichert den aktuellen `EnergyState`, um nach einem Neustart schnell wieder betriebsbereit zu sein.

## 2. Apache Parquet (Das Langzeit-Archiv)

Für alle historischen Sensordaten und getroffenen Entscheidungen nutzen wir das Big-Data-Format Parquet.
* **Pfad:** `data/parquet/YYYY/MM/day_DD.parquet`
* **Prinzip:** Die Dateien werden nur hinzugefügt, nicht mehr verändert.
* **Vorteile:**
    * **Auditierbarkeit:** Da Logs unveränderlich sind, können wir jederzeit prüfen, ob eine Entscheidung deterministisch (bei gleichem Input) korrekt war.
    * **Forschung/Replay:** Die spaltenbasierte Speicherung ermöglicht es dem **Research Node**, nur benötigte Daten (z.B. nur die SoC-Werte) extrem schnell und effizient zu laden, um Szenarien zu simulieren.

## 3. Konfigurations-Management

Die Konfiguration ist die DNA des Systems. Sie muss sicher und nachvollziehbar sein.
* **Format:** YAML (`config.yaml`).
* **Versionierung:** Jede Änderung an der Konfiguration muss mit einer Checksum versehen werden, die im Log gespeichert wird. Das stellt sicher, dass wir bei einem Replay wissen, welche Regeln galten ("Configuration-as-Data").

## 4. Prinzipien der Datensicherheit und Governance

* **Offline-fähig:** Alle Daten bleiben **on-prem** (on-premise). Es gibt keine Telemetrie oder Daten-Übertragung an externe Dienste (Privacy-by-Default).
* **Retention/Rotation:** Das System verwaltet die Daten selbst. Wir definieren Regeln für die Archivierung und Rotation von Parquet-Dateien (z.B. Löschung nach 5 Jahren). Ein Low-Disk-Alert (aus dem Risikokapitel) warnt den Nutzer rechtzeitig.
* **Checksums:** Export-Bundles für die Forschung erhalten einen Hash, um die Integrität beim Transfer zu sichern (Opt-in).

---
> **Nächster Schritt:** Die Daten sind sicher. Aber wie sieht das System für den Nutzer aus? Im nächsten Abschnitt klären wir die Prinzipien der Benutzeroberfläche.
>
> 👉 Weiter zu **[08.3 Benutzeroberfläche (UI)](./083_user_interface.md)**
>
> 🔙 Zurück zur **[Kapitelübersicht](./README.md)**
