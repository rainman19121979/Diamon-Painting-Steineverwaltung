# 💎 Diamond Painting Organizer

Eine Web-Anwendung zur Verwaltung deiner Diamond Painting Steinchen-Sammlung mit deutscher Oberfläche.

## ✨ Features

- **DMC Steinchen-Verwaltung** mit automatischer Farberkennung
- **400+ DMC Farben** mit deutschen Namen und Farbvorschau
- **Flexible Mengeneingabe**: "Viele" / "Wenige" Buttons ODER genaue Stückzahl
- **Intelligente Suche** nach DMC-Nummer oder Farbname
- **Sortierbare Tabelle** nach allen Spalten
- **Aufbewahrungsort-Tracking** für organisierte Lagerung
- **Mobile-optimiert** für Nutzung am Smartphone (Hauptnutzung)
- **Desktop-kompatibel** für PC-Nutzung

## 📋 Voraussetzungen

- Python 3.8 oder höher
- pip (Python Package Manager)
- Linux-basiertes System (getestet auf Proxmox LXC, Ubuntu, Debian)

## 🚀 Installation

### Automatische Installation (empfohlen)

1. Repository klonen:
```bash
git clone https://github.com/rainman19121979/Diamon-Painting-Steineverwaltung.git
cd Diamon-Painting-Steineverwaltung
```

**Optional:** Verzeichnis umbenennen für einfacheren Zugriff:
```bash
mv Diamon-Painting-Steineverwaltung diamond-painting
cd diamond-painting
```

2. Installationsskript ausführen:
```bash
chmod +x install.sh
sudo ./install.sh    # Als root für systemd Service
# oder
./install.sh         # Ohne root für manuelle Nutzung
```

**Während der Installation wirst du gefragt:**
- **Port-Nummer** (Standard: 8080) - Wähle einen freien Port für die Anwendung

**Das Skript installiert automatisch:**
- Python Virtual Environment
- Alle benötigten Dependencies aus requirements.txt
- Erstellt die Verzeichnisstruktur und .env Konfigurationsdatei
- Initialisiert die Datenbank (data/stones.json)
- **Bei Ausführung als root:** Systemd Service für automatischen Start

### Manuelle Installation

```bash
# Virtual Environment erstellen
python3 -m venv venv

# Virtual Environment aktivieren
source venv/bin/activate

# Dependencies installieren
pip install -r requirements.txt

# Verzeichnisse erstellen
mkdir -p data app/static/{css,js} app/templates

# Leere Datenbank initialisieren
echo "[]" > data/stones.json
```

## 🎯 Verwendung

### Anwendung starten

```bash
# Mit Startskript (empfohlen)
./start.sh

# Oder manuell
source venv/bin/activate
export FLASK_APP=app.app
export FLASK_ENV=development
python app/app.py
```

Die Anwendung läuft dann auf:
- **Lokal**: http://localhost:8080 (oder dein gewählter Port)
- **Netzwerk**: http://[IP-ADRESSE]:8080

### Steinchen hinzufügen

1. **DMC Nummer** eingeben (z.B. "310" für Schwarz)
   - Farbname wird automatisch ausgefüllt
2. **Menge wählen**:
   - Entweder "Viele" oder "Wenige" Button drücken
   - ODER genaue Stückzahl eingeben (z.B. 250)
3. **Aufbewahrungsort** (optional, z.B. "Box 1, Regal A")
4. "Steinchen hinzufügen" klicken

### Steinchen suchen

- Nach **DMC Nummer** suchen (z.B. "310")
- Nach **Farbname** suchen (z.B. "braun" findet alle braunen Töne)
- Ergebnisse können direkt aus der Suche gelöscht werden

### Tabelle sortieren

Klicke auf die Spaltenüberschriften zum Sortieren:
- **DMC Nr.** - Numerisch sortieren
- **Farbname** - Alphabetisch sortieren
- **Menge** - Nach "Viele" / "Wenige" sortieren
- **Stück** - Numerisch nach Stückzahl sortieren
- **Ort** - Alphabetisch nach Aufbewahrungsort sortieren

## 🔧 Systemd Service (Automatischer Start)

Bei Installation als **root** wird automatisch ein systemd Service erstellt:

```bash
# Service verwalten
systemctl start diamond-painting      # Service starten
systemctl stop diamond-painting       # Service stoppen
systemctl restart diamond-painting    # Service neustarten
systemctl status diamond-painting     # Status anzeigen

# Logs anzeigen
journalctl -u diamond-painting -f     # Live-Logs
journalctl -u diamond-painting        # Alle Logs

# Autostart
systemctl enable diamond-painting     # Autostart aktivieren
systemctl disable diamond-painting    # Autostart deaktivieren
```

**Vorteile:**
- ✅ Automatischer Start beim Systemboot
- ✅ Automatischer Neustart bei Fehler
- ✅ Läuft im Hintergrund (kein Terminal nötig)
- ✅ Integrierte Log-Verwaltung

## 📱 Mobile Nutzung

### Zugriff über Netzwerk

1. Finde die IP-Adresse deines Containers/Servers:
```bash
hostname -I | awk '{print $1}'
```

2. Öffne im Smartphone-Browser (im selben Netzwerk):
```
http://[SERVER-IP]:8080
```

**Beispiele:**
- Proxmox LXC: `http://192.168.1.100:8080`
- Lokales Netzwerk: `http://10.0.0.50:8080`

### Port ändern

Port kann in der `.env` Datei geändert werden:
```bash
nano .env
# FLASK_PORT=8080 ändern zu gewünschtem Port
```

Danach Service neustarten:
```bash
sudo systemctl restart diamond-painting
# oder
./start.sh
```

### Testen am Desktop

**Browser DevTools nutzen** (F12 → Device Toolbar) für mobile Ansicht ohne echtes Gerät

## 🔄 Anwendung aktualisieren

Wenn du die Anwendung via Git installiert hast:

```bash
./update.sh
```

**Das Update-Script:**
- ✅ Erstellt automatisch Backup von Daten und Konfiguration
- ✅ Lädt neueste Version von GitHub
- ✅ Zeigt Änderungen vor dem Update
- ✅ Aktualisiert Python Dependencies
- ✅ Startet Service automatisch neu (wenn als Service installiert)
- ✅ Behält deine Port-Konfiguration und Daten

**Manuelles Update ohne Git:**
1. Backup erstellen: `cp -r data data_backup && cp .env env_backup`
2. Neue Version von GitHub herunterladen
3. Dateien ersetzen (außer `data/` und `.env`)
4. Dependencies aktualisieren: `source venv/bin/activate && pip install -r requirements.txt`
5. Service neustarten: `sudo systemctl restart diamond-painting`

## 🗂️ Projektstruktur

```
diamond-painting/  (oder Diamon-Painting-Steineverwaltung)
├── app/
│   ├── app.py                 # Flask Backend / REST API
│   ├── dmc_colors_de.py       # 400+ Deutsche DMC Farben
│   ├── templates/
│   │   └── index.html         # Haupt-UI
│   └── static/
│       ├── css/
│       │   └── style.css      # Responsive Styling
│       └── js/
│           └── main.js        # Frontend-Logik
├── data/
│   └── stones.json            # Datenbank (JSON)
├── venv/                      # Virtual Environment
├── install.sh                 # Installationsskript (inkl. systemd)
├── update.sh                  # Update-Script
├── start.sh                   # Manueller Start
├── diamond-painting.service   # Systemd Service Template
├── requirements.txt           # Python Dependencies
└── README.md                  # Diese Datei
```

## 🛠️ Technologie-Stack

- **Backend**: Flask 3.0.0 (Python)
- **Frontend**: Vanilla JavaScript, HTML5, CSS3
- **Datenbank**: JSON-Datei (data/stones.json)
- **DMC Farben**: 400+ deutsche Farbnamen mit HEX-Codes
- **Responsive Design**: Mobile-First Approach

## 🎨 Unterstützte DMC Farben

Die Anwendung enthält alle 400+ offiziellen DMC Farben:
- Nummernbereich: 150 - 3866
- Spezialfarben: B5200, ECRU, WHITE
- Deutsche Farbnamen
- Exakte HEX-Farbcodes für Vorschau

Beispiele:
- 310: Schwarz (#000000)
- 3865: Edelweis (#FFFFF8)
- 610: Braun Biber (#950F0F)

## 📝 API Endpunkte

- `GET /api/stones` - Alle Steinchen abrufen
- `POST /api/stones` - Neues Steinchen hinzufügen
- `GET /api/stones/<id>` - Einzelnes Steinchen abrufen
- `PUT /api/stones/<id>` - Steinchen aktualisieren
- `DELETE /api/stones/<id>` - Steinchen löschen
- `GET /api/dmc/<number>` - DMC Farbinformationen abrufen

## 🔒 Datensicherheit

- Benutzerdaten werden lokal in `data/stones.json` gespeichert
- Keine Cloud-Verbindung erforderlich
- Datei ist in `.gitignore` ausgeschlossen

## Troubleshooting

### Issue: "Python 3 is not installed"

**Solution:**
```bash
apt-get update
apt-get install -y python3 python3-pip python3-venv
```

### Issue: "Virtual environment not found"

**Solution:**
```bash
./install.sh  # Run installation script again
```

### Issue: "Permission denied" when running scripts

**Solution:**
```bash
chmod +x install.sh start.sh
```

### Issue: "Port already in use"

**Solution:**
```bash
# Find process using port 5000
lsof -i :5000

# Kill the process
kill -9 <PID>

# Or change port in start.sh
```

### Issue: Application not accessible from network

**Solution:**
1. Check LXC firewall settings
2. Verify container IP: `hostname -I`
3. Ensure Flask is binding to 0.0.0.0 (not 127.0.0.1)
4. Check Proxmox firewall rules

### Issue: "ModuleNotFoundError" when starting

**Solution:**
```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

## Accessing from Host Machine

1. Get your LXC container IP:
```bash
hostname -I
```

2. Access from browser on any device in the network:
```
http://<LXC_IP>:5000
```

## Updating the Application

```bash
# Navigate to application directory
cd /opt/diamond-painting

# Pull latest changes (if using git)
git pull

# Reinstall dependencies
source venv/bin/activate
pip install -r requirements.txt

# Restart application
./start.sh
```

## Security Recommendations

1. **Change default credentials** if authentication is implemented
2. **Use HTTPS** in production with a reverse proxy (nginx/Apache)
3. **Restrict network access** using Proxmox firewall rules
4. **Regular updates**: Keep Python and dependencies updated
5. **Backup data**: Regular backups of `app/data/` directory

## Backup and Restore

### Backup

```bash
# Backup data directory
tar -czf diamond-painting-backup-$(date +%Y%m%d).tar.gz app/data/

# Or backup entire application
tar -czf diamond-painting-full-backup-$(date +%Y%m%d).tar.gz /opt/diamond-painting/
```

### Restore

```bash
# Restore data
tar -xzf diamond-painting-backup-20231203.tar.gz -C /opt/diamond-painting/

# Restore full application
tar -xzf diamond-painting-full-backup-20231203.tar.gz -C /opt/
```

## Performance Tuning

For better performance in production:

1. **Use Gunicorn** with multiple workers:
```bash
gunicorn -w 4 -b 0.0.0.0:5000 --timeout 120 app.server:app
```

2. **Set up systemd service** for auto-start:
```bash
# Create service file
sudo nano /etc/systemd/system/diamond-painting.service
```

3. **Configure reverse proxy** (nginx) for static files and SSL

## Support

For issues, questions, or contributions:
- Create an issue in the repository
- Check troubleshooting section above
- Review Flask documentation: https://flask.palletsprojects.com/

## License

[Specify your license here]

## Acknowledgments

Built with Flask and designed for easy deployment in Proxmox LXC environments.
