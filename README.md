# DIVERA 24/7 – Home Assistant Integration with Divera Server URL



Eine inoffizielle Home Assistant Integration für DIVERA 24/7 Server, die Einsätze in Echtzeit über eine WebSocket-Verbindung empfängt.

---

## Funktionsweise

Die Integration verbindet sich dauerhaft per **WebSocket** mit den eigenen DIVERA-Servern. Sobald DIVERA einen neuen Alarm meldet, wird einmalig die REST-API abgefragt und der Sensor in Home Assistant aktualisiert – ohne unnötiges Polling.

---

## Voraussetzungen

- Home Assistant OS, Supervised oder Core
- DIVERA 24/7 Server Account mit API-Zugang
- HACS installiert (für die empfohlene Installation)

---

## Installation über HACS (empfohlen)

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=lassefactory&repository=divera-hacs)

1. HACS in Home Assistant öffnen
2. Oben rechts auf die **drei Punkte** klicken → **Benutzerdefinierte Repositories**
3. Folgendes eintragen:
   - **Repository:** `https://github.com/The-Fox23/divera-hacs-custom-server`
   - **Kategorie:** Integration
4. **Hinzufügen** klicken
5. In HACS nach **DIVERA 24/7 with Server URL** suchen und **Herunterladen** klicken
6. Home Assistant neu starten

---

## Manuelle Installation

1. Den Ordner `custom_components/divera/` aus diesem Repository herunterladen
2. In das Home Assistant Konfigurationsverzeichnis kopieren:
   ```
   config/custom_components/divera/
   ```
3. Home Assistant neu starten

Die fertige Verzeichnisstruktur sollte so aussehen:
```
config/
└── custom_components/
    └── divera/
        ├── __init__.py
        ├── config_flow.py
        ├── const.py
        ├── coordinator.py
        ├── manifest.json
        ├── sensor.py
        ├── strings.json
        └── translations/
            ├── de.json
            └── en.json
```

---

## Einrichtung

1. In Home Assistant: **Einstellungen → Geräte & Dienste → Integration hinzufügen**
2. Nach **DIVERA** suchen und auswählen
3. **API-Schlüssel eingeben**
   - Den Accesskey aus DIVERA eintragen
   - DIVERA → Einstellungen → DEBUG → Accesskey kopieren
4. **Einheit auswählen** aus der Liste der verfügbaren Einheiten
5. Fertig – der Sensor erscheint automatisch

---

## Sensor

Nach der Einrichtung wird ein Sensor erstellt:

**`sensor.divera_<einheitname>`**
**`sensor.divera_<alarmtext>`**
**`sensor.divera_<alarmierte>`**
**`sensor.divera_<alarmdatum>`**
**`sensor.divera_<alarmid>`**
**`sensor.divera_<alarmadresse>`**
**`sensor.divera_<Position>`**

| | |
|---|---|
| **State** | Stichwort des aktiven Alarms oder `Kein aktiver Einsatz` |

### Attribute

| Attribut | Beschreibung |
|---|---|
| `stichwort` | Alarmstichwort |
| `beschreibung` | Freitext / Meldungstext |
| `adresse` | Einsatzadresse |
| `einsatz_id` | Interne DIVERA Alarm-ID |
| `prioritaet` | Sonderrechte (true/false) |
| `alarmiert_am` | Alarmierungszeitpunkt (ISO 8601) |
| `geschlossen` | true wenn Einsatz abgeschlossen |
| `fahrzeuge` | Alarmierte Fahrzeuge |
| `latitude` / `longitude` | GPS-Koordinaten (werden automatisch auf der Karte angezeigt) |
| + weitere | Alle weiteren Felder aus der DIVERA API |

---


### Beispiel-Automation

trigger:
  - platform: state
    entity_id: sensor.divera_alarmtext

action:
  - service: notify.mobile_app
    data:
      title: "{{ states('sensor.divera_alarm') }}"
      message: >
        {{ states('sensor.divera_alarmtext') }}
        Einsatzort: {{ state_attr('sensor.divera_alarm',
        'adresse') }}
```


## Debugging

Debug-Logging in `configuration.yaml` aktivieren:

```yaml
logger:
  default: warning
  logs:
    custom_components.divera: debug
```

Logs einsehen unter: **Einstellungen → System → Protokolle**

---

## Fehlerbehebung

| Problem | Lösung |
|---|---|
| Integration erscheint nicht | HA vollständig neu starten, nicht nur neu laden |
| `Kein aktiver Einsatz` trotz Alarm | Debug-Logging aktivieren und Logs prüfen |
| Ungültiger API-Schlüssel | Neuen Accesskey in DIVERA unter Einstellungen → DEBUG generieren |
| Automation löst nicht aus | Prüfen ob Stichwort-Filter das Stichwort ausschließt |

---

## Lizenz

Dieses Projekt steht unter der **Creative Commons Attribution-NonCommercial 4.0 (CC BY-NC 4.0)** Lizenz.
Nutzung und Weitergabe erlaubt, jedoch **keine kommerzielle Nutzung** ohne ausdrückliche Genehmigung.

Dieses Projekt ist nicht offiziell mit DIVERA GmbH verbunden.
