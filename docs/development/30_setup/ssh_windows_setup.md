# 30.1 – SSH unter Windows/Linux

SSH ist der sichere Kanal zwischen deinem Entwicklungsrechner und dem Edge-Gerät
(Umbrel, NUC, Raspberry Pi) auf dem BitGridAI läuft.

Dieses Kapitel zeigt, wie du SSH einrichtest, Schlüssel erzeugst und die Verbindung
bequem über eine `~/.ssh/config` erreichbar machst.

&nbsp;

## Voraussetzungen

| Plattform | Voraussetzung |
|-----------|---------------|
| **Windows 10/11** | OpenSSH-Client aktiviert (vorinstalliert ab Windows 10 1809) |
| **Linux / WSL** | `openssh-client` vorhanden (`ssh -V` zum Prüfen) |

### OpenSSH auf Windows prüfen / aktivieren

```powershell
# Prüfen ob OpenSSH-Client installiert ist
Get-WindowsCapability -Online | Where-Object Name -like 'OpenSSH.Client*'

# Falls nicht installiert:
Add-WindowsCapability -Online -Name OpenSSH.Client~~~~0.0.1.0
```

&nbsp;

## SSH-Schlüsselpaar erzeugen

```bash
# Ed25519-Schlüssel erzeugen (empfohlen)
ssh-keygen -t ed25519 -C "bitgridai-dev"

# Speicherort: Standard beibehalten (Enter)
# Passphrase: empfohlen (sicherer)
```

Das erzeugt:
- `~/.ssh/id_ed25519` – **privater Schlüssel** (niemals teilen)
- `~/.ssh/id_ed25519.pub` – **öffentlicher Schlüssel** (wird auf dem Server hinterlegt)

&nbsp;

## Öffentlichen Schlüssel auf das Edge-Gerät übertragen

### Option A – `ssh-copy-id` (Linux/WSL)

```bash
ssh-copy-id -i ~/.ssh/id_ed25519.pub user@umbrel.local
```

### Option B – Manuell (Windows PowerShell)

```powershell
# Öffentlichen Schlüssel ausgeben und kopieren
Get-Content ~/.ssh/id_ed25519.pub

# Dann auf dem Zielgerät einmalig per Passwort einloggen und einfügen:
# ssh user@umbrel.local
# mkdir -p ~/.ssh && echo "DEIN_PUBLIC_KEY" >> ~/.ssh/authorized_keys
# chmod 700 ~/.ssh && chmod 600 ~/.ssh/authorized_keys
```

&nbsp;

## SSH-Agent einrichten (Windows)

Der SSH-Agent speichert die entsperrte Passphrase für die Sitzungsdauer.

```powershell
# SSH-Agent-Dienst starten und auf automatisch setzen
Set-Service -Name ssh-agent -StartupType Automatic
Start-Service ssh-agent

# Schlüssel zum Agenten hinzufügen
ssh-add ~/.ssh/id_ed25519
```

&nbsp;

## `~/.ssh/config` einrichten

Eine Config-Datei erspart das Tippen langer Hostnamen und Optionen.

**Datei:** `~/.ssh/config` (anlegen falls nicht vorhanden)

```
# BitGridAI – Edge-Gerät (Umbrel / NUC / Pi)
Host bitgrid
    HostName umbrel.local
    User umbrel
    IdentityFile ~/.ssh/id_ed25519
    ServerAliveInterval 60

# Beispiel für Raspberry Pi direkt
Host bitgrid-pi
    HostName 192.168.1.42
    User pi
    IdentityFile ~/.ssh/id_ed25519
```

Danach einfach:

```bash
ssh bitgrid
```

&nbsp;

## Verbindung testen

```bash
# Verbindung prüfen
ssh bitgrid

# Oder einzeilig ohne Config
ssh -i ~/.ssh/id_ed25519 user@umbrel.local
```

Bei erfolgreicher Verbindung landet man direkt in der Shell des Edge-Geräts –
ohne Passwort, dafür mit Schlüssel.

&nbsp;

## SSH in VSCode nutzen

Die Extension **Remote - SSH** (Microsoft) erlaubt es, direkt im Edge-Gerät zu entwickeln:

1. `Ctrl+Shift+P` → **Remote-SSH: Connect to Host**
2. `bitgrid` wählen (aus der `~/.ssh/config`)
3. VSCode öffnet ein Remote-Fenster auf dem Gerät

&nbsp;

## Häufige Probleme

| Problem | Ursache | Lösung |
|---------|---------|--------|
| `Permission denied (publickey)` | Schlüssel nicht übertragen oder falscher Nutzer | Schritt "Schlüssel übertragen" wiederholen |
| `Host not found` | `umbrel.local` nicht auflösbar | IP-Adresse direkt verwenden |
| Verbindung bricht ab | Kein Keep-Alive | `ServerAliveInterval 60` in `~/.ssh/config` |
| Passwort wird trotzdem abgefragt | SSH-Agent läuft nicht | `ssh-add` erneut ausführen |

---

> 👉 Weiter zu **[30.2 – Entwicklungsumgebung](./dev_environment.md)**
>
> 🔙 Zurück zu **[30 – Setup & Umgebung](./README.md)**
>
> 🏠 Zurück zur **[Hauptübersicht](../../README.md)**
