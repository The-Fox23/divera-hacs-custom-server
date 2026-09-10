# DIVERA 24/7 – Home Assistant Integration with configurable Server URL

Eine inoffizielle Home Assistant Integration für **DIVERA 24/7**, die Einsätze in Echtzeit über eine WebSocket-Verbindung empfängt.

Die Integration unterstützt sowohl den offiziellen DIVERA-Server als auch **eigene, private oder selbst gehostete DIVERA-Server**, da die Server-URL frei konfiguriert werden kann.

---

## Funktionen

* 🔗 **Frei konfigurierbare DIVERA-Server-URL**
* 🔑 Verbindung über DIVERA Accesskey
* 🚒 Auswahl der gewünschten Einheit / UCR während der Einrichtung
* ⚡ Echtzeit-Aktualisierung über WebSocket
* 🔄 REST-API als Initialisierung und Fallback
* 🚨 Anzeige des aktuellen Einsatzes
* 🏷️ Alarmstichwort
* 📝 Alarmtext / Einsatzbeschreibung
* 📍 Einsatzadresse
* 🆔 Einsatz-ID
* 🕐 Alarmierungszeitpunkt
* 🚒 Alarmierte Fahrzeuge
* 📍 GPS-Koordinaten des Einsatzortes
* 🗺️ Einsatzort als Home-Assistant Device Tracker
* 🏠 Konfigurierbare Feuerwache als dauerhafter Kartenpunkt
* 🛣️ Automatische Berechnung der Fahrstrecke zwischen Feuerwache und Einsatzort
* 📏 Anzeige der Entfernung
* ⏱️ Anzeige der voraussichtlichen Fahrzeit
* 💾 Routing-Cache zur Vermeidung unnötiger Routing-Anfragen
* 🧹 Route und Einsatzort werden nach Einsatzende automatisch entfernt
* 🏠 Die Feuerwache bleibt auch ohne aktiven Einsatz sichtbar
* 🗺️ Unterstützung für die optionale `ha-map-card` zur Darstellung der Fahrroute

---

## Funktionsweise

Die Integration verbindet sich dauerhaft per **WebSocket** mit dem konfigurierten DIVERA-Server.

Sobald DIVERA einen neuen Alarm meldet, werden die Einsatzdaten aktualisiert.

Die Kommunikation funktioniert grundsätzlich nach folgendem Schema:

```text
DIVERA Server
     │
     ├── WebSocket
     │       │
     │       ▼
     │   Home Assistant
     │       │
     │       ├── Alarm-Sensoren
     │       ├── Einsatzort
     │       └── Routing
     │
     └── REST API
             │
             └── Initialisierung / Aktualisierung
```

Bei bestimmten WebSocket-Ereignissen werden die Daten zusätzlich über die REST-API aktualisiert.

Dadurch ist im normalen Betrieb **kein dauerhaftes, unnötiges Polling der kompletten DIVERA-Daten erforderlich**.

---

# Voraussetzungen

* Home Assistant OS, Supervised oder Core
* DIVERA 24/7 Server Account
* Gültiger DIVERA Accesskey
* Eine konfigurierte DIVERA-Einheit / UCR
* HACS für die empfohlene Installation

Für die Routing-Funktion ist zusätzlich eine Internetverbindung zum verwendeten Routing-Dienst erforderlich.

---

# Installation über HACS

## Benutzerdefiniertes Repository

Da dieses Projekt aktuell nicht Bestandteil des offiziellen HACS-Repository-Katalogs ist, muss es als benutzerdefiniertes Repository hinzugefügt werden.

1. HACS in Home Assistant öffnen
2. Oben rechts auf die **drei Punkte** klicken
3. **Benutzerdefinierte Repositories** auswählen
4. Folgendes Repository eintragen:

```text
https://github.com/The-Fox23/divera-hacs-custom-server
```

5. Kategorie:

```text
Integration
```

6. **Hinzufügen** auswählen
7. Nach **DIVERA 24/7 with Server URL** suchen
8. Integration herunterladen
9. Home Assistant vollständig neu starten

---

# Manuelle Installation

1. Den Ordner

```text
custom_components/divera/
```

aus diesem Repository herunterladen.

2. In das Home-Assistant-Konfigurationsverzeichnis kopieren:

```text
config/custom_components/divera/
```

Die Verzeichnisstruktur sollte anschließend ungefähr so aussehen:

```text
config/
└── custom_components/
    └── divera/
        ├── __init__.py
        ├── config_flow.py
        ├── const.py
        ├── coordinator.py
        ├── device_tracker.py
        ├── route.py
        ├── route_sensor.py
        ├── manifest.json
        ├── sensor.py
        ├── strings.json
        └── translations/
            ├── de.json
            └── en.json
```

3. Home Assistant vollständig neu starten.

---

# Einrichtung

Nach der Installation:

**Einstellungen → Geräte & Dienste → Integration hinzufügen**

Nach

```text
DIVERA
```

suchen.

---

## 1. Server-URL

Zuerst wird die DIVERA-Server-URL abgefragt.

Beispiel für den offiziellen Server:

```text
https://app.divera247.com
```

Es können aber auch andere DIVERA-Server verwendet werden.

Die URL muss vollständig angegeben werden:

```text
https://server.example.de
```

oder

```text
http://192.168.1.100
```

---

## 2. API-Schlüssel

Den DIVERA Accesskey eingeben.

Der Accesskey wird in DIVERA unter:

```text
Einstellungen → DEBUG → Accesskey
```

bereitgestellt.

---

## 3. Einheit auswählen

Nach erfolgreicher Verbindung werden die verfügbaren Einheiten / UCRs geladen.

Die gewünschte Einheit auswählen.

Die Einheit wird anschließend dauerhaft mit dem Home-Assistant-Konfigurationseintrag verknüpft.

---

# Feuerwache konfigurieren

Nach der Auswahl der Einheit wird die **Feuerwache** konfiguriert.

Die vollständige Adresse sollte im folgenden Format eingegeben werden:

```text
Straße Hausnummer, PLZ Ort
```

Beispiel:

```text
Vogelsangweg 14, 34346 Hann. Münden
```

Die Adresse wird während der Einrichtung einmalig geocodiert.

Dabei werden folgende Daten gespeichert:

```text
station_address
station_latitude
station_longitude
```

Die Koordinaten werden anschließend aus dem Home-Assistant-Konfigurationseintrag verwendet.

Dadurch ist **keine permanente Geocodierung erforderlich**.

> Hinweis: Die Genauigkeit der automatisch ermittelten Position hängt vom verwendeten Geocoding-Dienst und dessen Kartendaten ab.

---

# Entitäten

Die Integration stellt verschiedene Sensoren und Device Tracker zur Verfügung.

## Alarm-Sensoren

Je nach Konfiguration werden unter anderem folgende Informationen bereitgestellt:

| Information       | Beschreibung                       |
| ----------------- | ---------------------------------- |
| Alarm / Stichwort | Aktuelles Einsatzstichwort         |
| Alarmtext         | Einsatzbeschreibung / Meldungstext |
| Alarmierte        | Alarmierte Einheiten / Fahrzeuge   |
| Alarmdatum        | Zeitpunkt der Alarmierung          |
| Alarm-ID          | Interne DIVERA Einsatz-ID          |
| Alarmadresse      | Einsatzadresse                     |
| Einsatzort        | GPS-Position des Einsatzortes      |

Ist kein Einsatz aktiv, wird als Zustand verwendet:

```text
Kein aktiver Einsatz
```

---

# Einsatzort

Der aktuelle Einsatzort wird als eigener Home-Assistant **Device Tracker** bereitgestellt.

Beispiel:

```text
device_tracker.divera_24_7_03_hann_munden_divera_einsatzort_03_hann_munden
```

Bei einem aktiven Einsatz enthält der Tracker die von DIVERA gelieferten Koordinaten.

Beispiel:

```text
latitude: 51.4114777
longitude: 9.6507931
```

Nach Beendigung des Einsatzes wird die Position des Einsatzortes entfernt.

Dadurch kann Home Assistant erkennen, dass aktuell kein Einsatzort vorhanden ist.

---

# Feuerwache

Die konfigurierte Feuerwache wird ebenfalls als eigener Device Tracker bereitgestellt.

Beispiel:

```text
device_tracker.divera_24_7_03_hann_munden_divera_feuerwache_03_hann_munden
```

Die Feuerwache bleibt **dauerhaft vorhanden**, auch wenn momentan kein Einsatz aktiv ist.

Beispielattribute:

```text
latitude: 51.4114777
longitude: 9.6507931
adresse: Vogelsangweg 14, 34346 Hann. Münden
```

Damit kann die Feuerwache als fester Ausgangspunkt für die Karte und für die Routenberechnung verwendet werden.

---

# Routing

Bei einem aktiven Einsatz kann automatisch eine Fahrroute zwischen der konfigurierten Feuerwache und dem Einsatzort berechnet werden.

Die Route wird über den konfigurierten Routing-Dienst ermittelt.

Standardmäßig wird **OSRM (Open Source Routing Machine)** verwendet.

```text
Feuerwache
     │
     │
     │  berechnete Fahrroute
     │
     ▼
Einsatzort
```

---

## Routing nur bei aktivem Einsatz

Eine Route wird nur berechnet, wenn:

* ein aktiver Einsatz vorhanden ist,
* der Einsatz gültige GPS-Koordinaten besitzt,
* eine gültige Feuerwachenposition vorhanden ist.

Wenn kein Einsatz aktiv ist, wird keine Routing-Anfrage durchgeführt.

---

# Routing-Cache

Um unnötige Routing-Anfragen zu vermeiden, werden bereits berechnete Routen zwischengespeichert.

Der Cache orientiert sich an den Zielkoordinaten des Einsatzortes.

Dadurch wird bei wiederholten Aktualisierungen desselben Einsatzes nicht jedes Mal eine neue Route angefordert.

Beispiel:

```text
Einsatz 123
51.412000 / 9.651000
        │
        ▼
Route berechnen
        │
        ▼
Cache
```

Bei einer erneuten Aktualisierung mit denselben Koordinaten kann die bereits vorhandene Route wiederverwendet werden.

---

# Routing-Entitäten

Die Integration stellt Informationen zur Route als eigene Sensoren bereit.

Beispiele:

```text
sensor.divera_24_7_03_hann_munden_divera_route_geojson_03_hann_munden
```

```text
sensor.divera_24_7_03_hann_munden_divera_routenstatus_03_hann_munden
```

```text
sensor.divera_24_7_03_hann_munden_divera_fahrzeit_03_hann_munden
```

Je nach aktueller Version können zusätzlich Entfernungssensoren vorhanden sein.

---

# Route GeoJSON

Für die Darstellung der Route wird die berechnete Geometrie als **GeoJSON LineString** bereitgestellt.

Beispiel:

```json
{
  "type": "LineString",
  "coordinates": [
    [9.6507931, 51.4114777],
    [9.6512345, 51.4121234],
    [9.6523456, 51.4134567]
  ]
}
```

Dabei gilt bei GeoJSON:

```text
[Longitude, Latitude]
```

also:

```text
[9.6507931, 51.4114777]
```

---

# Darstellung auf einer Home-Assistant-Karte

Die normale Home-Assistant-Map kann die Device Tracker anzeigen.

Für die Darstellung der **tatsächlichen Fahrroute als Linie** wird die optionale Custom-Lovelace-Karte `ha-map-card` empfohlen.

Repository:

https://github.com/nathan-gs/ha-map-card

Die Karte unterstützt unter anderem GeoJSON-Elemente wie `LineString`.

---

## Installation von ha-map-card

Die Karte kann über HACS installiert werden.

In HACS nach:

```text
Map Card
```

suchen.

Alternativ kann die Karte manuell installiert werden.

---

# Beispiel für die Einsatzkarte

Nach Installation der `ha-map-card` kann beispielsweise folgende Lovelace-Karte verwendet werden:

```yaml
type: custom:map-card
title: DIVERA – Einsatzkarte

x: 9.6507931
y: 51.4114777
zoom: 14

card_size: 6

tile_layer_url: "https://tile.openstreetmap.org/{z}/{x}/{y}.png"
tile_layer_attribution: "&copy; OpenStreetMap contributors"

focus_follow: contains

entities:

  # --------------------------------------------------
  # Feuerwache
  # --------------------------------------------------

  - entity: device_tracker.divera_24_7_03_hann_munden_divera_feuerwache_03_hann_munden
    display: icon
    icon: mdi:fire-station
    label: Feuerwache
    size: 50
    z_index_offset: 100

  # --------------------------------------------------
  # Aktueller Einsatzort
  # --------------------------------------------------

  - entity: device_tracker.divera_24_7_03_hann_munden_divera_einsatzort_03_hann_munden
    display: icon
    icon: mdi:fire-alert
    label: Einsatzort
    size: 50
    z_index_offset: 200

  # --------------------------------------------------
  # Fahrroute
  # --------------------------------------------------

  - entity: sensor.divera_24_7_03_hann_munden_divera_route_geojson_03_hann_munden
    display: marker
    geojson:
      attribute: route_geojson
      weight: 6
      opacity: 0.9
      fill_opacity: 0
      hide_marker: true
```

> Die Koordinaten `x` und `y` müssen bei dieser Karte korrekt zugeordnet werden: `x` ist Longitude und `y` ist Latitude.

---

# Verhalten der Karte

## Kein aktiver Einsatz

Die Karte zeigt:

```text
🏠 Feuerwache
```

Es werden keine Einsatzposition und keine Route angezeigt.

---

## Aktiver Einsatz

Die Karte zeigt:

```text
🏠 Feuerwache
       │
       │
       │ Fahrroute
       │
       ▼
🚨 Einsatzort
```

Zusätzlich können Entfernung und Fahrzeit als eigene Sensoren in Dashboards dargestellt werden.

---

## Einsatz beendet

Nach Abschluss des Einsatzes:

* 🚨 Einsatzort wird entfernt
* 🛣️ Route wird entfernt
* 📏 Routendaten werden zurückgesetzt
* ⏱️ Fahrzeit wird zurückgesetzt
* 🏠 Feuerwache bleibt sichtbar

Die Karte fällt damit automatisch wieder auf den festen Standort der Feuerwache zurück.

---

# Beispiel-Automation

Eine einfache Benachrichtigung bei einem neuen Einsatz kann beispielsweise so aussehen:

```yaml
alias: DIVERA – Einsatzbenachrichtigung

trigger:
  - platform: state
    entity_id: sensor.divera_alarm

action:
  - service: notify.mobile_app
    data:
      title: "{{ states('sensor.divera_alarm') }}"
      message: >
        {{ states('sensor.divera_alarmtext') }}

        Einsatzort:
        {{ state_attr('sensor.divera_alarm', 'adresse') }}

mode: single
```

Die tatsächlichen Entity-IDs können abhängig von der konfigurierten Einheit abweichen.

---

# Beispiel für Fahrzeit und Route

Die Routing-Sensoren können beispielsweise in einem Dashboard angezeigt werden:

```yaml
type: entities
title: DIVERA Einsatz
entities:
  - entity: sensor.divera_24_7_03_hann_munden_divera_routenstatus_03_hann_munden
    name: Routenstatus

  - entity: sensor.divera_24_7_03_hann_munden_divera_fahrzeit_03_hann_munden
    name: Fahrzeit
```

---

# Fehlerbehebung

## Integration erscheint nicht

Home Assistant vollständig neu starten.

Nicht nur:

```text
Konfiguration neu laden
```

sondern einen vollständigen Neustart durchführen.

---

## Ungültiger API-Schlüssel

Den Accesskey in DIVERA überprüfen:

```text
DIVERA
→ Einstellungen
→ DEBUG
→ Accesskey
```

---

## Keine Einheit verfügbar

Überprüfen:

* Server-URL korrekt?
* Accesskey korrekt?
* API-Zugriff auf dem DIVERA-Server verfügbar?
* Hat der Accesskey Zugriff auf die gewünschte Einheit?

---

## Einsatz wird nicht angezeigt

Debug-Logging aktivieren:

```yaml
logger:
  default: warning
  logs:
    custom_components.divera: debug
```

Anschließend die Logs unter:

```text
Einstellungen
→ System
→ Protokolle
```

prüfen.

---

## Einsatzort wird nicht angezeigt

Überprüfen, ob DIVERA für den Einsatz gültige Koordinaten liefert.

Der Device Tracker benötigt:

```text
latitude
longitude
```

und einen aktiven Einsatz.

---

## Feuerwache wird falsch positioniert

Die Feuerwachenposition wird beim Einrichten anhand der eingegebenen Adresse geocodiert.

Die Genauigkeit hängt von den verfügbaren Kartendaten ab.

Über die Home-Assistant-Entwicklerwerkzeuge kann die gespeicherte Position kontrolliert werden.

Beispiel:

```text
Entwicklerwerkzeuge
→ Zustände
→ device_tracker.divera_..._feuerwache_...
```

Dort sollten unter anderem vorhanden sein:

```text
latitude
longitude
adresse
```

---

## Route wird nicht angezeigt

Zunächst überprüfen, ob der Routing-Sensor ein Attribut

```text
route_geojson
```

besitzt.

Das GeoJSON sollte ungefähr folgende Struktur haben:

```json
{
  "type": "LineString",
  "coordinates": [
    [9.6507931, 51.4114777],
    [9.6512345, 51.4121234]
  ]
}
```

Wenn das Attribut fehlt, kann die `ha-map-card` keine Route zeichnen.

---

## Keine Route trotz aktivem Einsatz

Überprüfen:

1. Ist ein aktiver Einsatz vorhanden?
2. Sind Latitude und Longitude des Einsatzes vorhanden?
3. Sind Latitude und Longitude der Feuerwache vorhanden?
4. Ist der Routing-Dienst erreichbar?
5. Zeigt der Routenstatus einen Fehler?

---

# Datenschutz und externe Dienste

Die eigentliche DIVERA-Kommunikation erfolgt mit dem in der Integration konfigurierten DIVERA-Server.

Für die zusätzlichen Funktionen können externe OpenStreetMap-basierte Dienste verwendet werden:

### Geocoding

Die eingegebene Feuerwachenadresse wird während der Einrichtung einmalig über einen Geocoding-Dienst verarbeitet.

Die ermittelten Koordinaten werden anschließend gespeichert.

### Routing

Für die Berechnung der Fahrroute wird standardmäßig ein OSRM-Routing-Dienst verwendet.

Dabei werden die Koordinaten von:

```text
Feuerwache
```

und

```text
Einsatzort
```

an den Routing-Dienst übertragen.

Die Routing-Anfrage wird nur bei einem aktiven Einsatz und gültigen Koordinaten durchgeführt.

---

# Technischer Aufbau

Die Integration besteht aus mehreren Komponenten:

| Datei                  | Funktion                                        |
| ---------------------- | ----------------------------------------------- |
| `__init__.py`          | Initialisierung der Integration                 |
| `config_flow.py`       | Einrichtung, Server-URL, Einheit und Feuerwache |
| `const.py`             | Konstanten und Konfiguration                    |
| `coordinator.py`       | DIVERA REST/WebSocket Kommunikation             |
| `sensor.py`            | Alarm- und Einsatzsensoren                      |
| `device_tracker.py`    | Feuerwache und Einsatzort                       |
| `route.py`             | Routing und Routing-Cache                       |
| `route_sensor.py`      | Route, Fahrzeit und Routing-Informationen       |
| `strings.json`         | Übersetzungen / Konfigurationsdialog            |
| `translations/de.json` | Deutsche Übersetzung                            |
| `translations/en.json` | Englische Übersetzung                           |

---

# Stabilität und Kommunikation

Die eigentliche DIVERA-Kommunikation basiert auf einer dauerhaften WebSocket-Verbindung.

Bei einem Verbindungsabbruch versucht die Integration automatisch, die Verbindung wiederherzustellen.

Zusätzlich existiert ein REST-basierter Fallback.

Dadurch bleibt die Integration auch bei kurzzeitigen Netzwerkproblemen möglichst verfügbar.

---

# Lizenz

Dieses Projekt steht unter der **Creative Commons Attribution-NonCommercial 4.0 (CC BY-NC 4.0)** Lizenz.

Nutzung und Weitergabe sind erlaubt, jedoch **keine kommerzielle Nutzung** ohne ausdrückliche Genehmigung.

---

# Hinweis

Dieses Projekt ist **nicht offiziell mit der DIVERA GmbH verbunden**.

DIVERA und DIVERA 24/7 sind Marken bzw. Produkte der jeweiligen Rechteinhaber.
