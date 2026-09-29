# DIVERA 24/7 – Custom Server Integration
## Project Status

**Repository:** `The-Fox23/divera-hacs-custom-server`  
**Integration:** DIVERA 24/7 with Server URL  
**Prepared manifest version:** `1.1.2`  
**Status:** 🟢 Vehicle status/position support implemented; practical HA test pending

---

## 1. Project goal

This Home Assistant integration extends DIVERA 24/7 with a configurable server URL and current operational data for alarms and vehicles.

Goals:
- support the public DIVERA server
- support self-hosted/private DIVERA servers
- configure DIVERA units/UCRs
- provide alarm information and sensors
- provide fire-station and incident locations
- provide vehicle status and vehicle positions
- calculate a route from the fire station to the incident

**Important:** The stable backend/WebSocket connection remains the baseline and should not be changed unnecessarily.

---

## 2. Current functional status

### Server configuration
Implemented:
- configurable server URL
- API key
- DIVERA unit/UCR selection
- fire-station address

Default server:
`https://app.divera247.com`

### DIVERA API
Implemented:
- JWT authentication
- `/api/v2/auth/jwt`
- `/api/v2/pull/all`
- UCR selection
- extraction of vehicle data from `cluster.vehicle`
- extraction of FMS status definitions from `cluster.fms_status`

### WebSocket
**Status: 🟢 Stable / unchanged architecture**

Existing WebSocket authentication, reconnect handling and fallback polling remain in place.

A `cluster-vehicle` event now triggers the existing REST refresh so the vehicle entities receive current API data.

Current values:
- reconnect delay: 10 seconds
- maximum reconnect delay: 300 seconds
- fallback polling: 60 seconds

---

## 3. Alarm data

Implemented:
- alarm title/stichwort
- alarm text
- incident address
- incident ID
- priority
- closed/open status
- alarm time
- duration
- recipient count
- read count
- incident report
- latitude/longitude
- alarm vehicle data
- additional DIVERA fields as attributes

---

## 4. Vehicle support

Vehicle data from `cluster.vehicle` is now retained by the coordinator instead of being discarded.

For every vehicle returned by the API, dynamic entities are created.

### Vehicle sensor

The vehicle sensor provides:
- current `fmsstatus_id`
- vehicle ID
- vehicle name/short name and other API fields as attributes
- FMS status name when supplied by the API
- FMS status color when supplied by the API

The sensor is created dynamically when a vehicle appears and removed when it disappears from the API data.

### Vehicle device tracker

A dynamic device tracker is created for every vehicle.

It provides:
- latitude
- longitude
- GPS accuracy when available
- vehicle information as attributes
- FMS status information as attributes

This provides the technical basis for displaying vehicles on a Home Assistant map.

**Status:** 🟢 Implemented / practical Home Assistant test pending

---

## 5. Fire station

The fire-station address is entered during setup and geocoded through Nominatim.

Example:
`Vogelsangweg 14, 34346 Hann. Münden`

Stored values:
- `station_address`
- `station_latitude`
- `station_longitude`

Known point: geocoding may return a point somewhere along a street rather than the exact building.

---

## 6. Device trackers

### Fire station tracker
Provides the stored fire-station coordinates and address.

### Incident location tracker
Provides the current incident coordinates when:
- an active incident exists
- valid latitude/longitude are available
- the incident is not closed

### Vehicle trackers
Provide the current API position of each DIVERA vehicle.

---

## 7. Routing

**Status: 🟢 Existing implementation retained**

Routing continues to use the current `DiveraRouteCoordinator` and OSRM implementation.

The newer vehicle functionality does **not** reintroduce the old Route Sensor implementation from DiveraControl.

Current routing service:
`https://router.project-osrm.org`

The route contains:
- distance
- duration
- GeoJSON geometry
- incident ID
- incident coordinates

---

## 8. Planned map behaviour

### No active incident
- fire-station marker remains
- no incident marker
- no incident route
- vehicle trackers can still provide vehicle positions

### Active incident
- fire-station marker
- red incident marker
- route
- distance
- travel time
- vehicle positions
- map centered on incident

### Incident closed
- incident marker removed
- route removed
- fire-station marker remains
- vehicle positions remain available according to the API

---

## 9. Translations

Files:
- `strings.json`
- `translations/de.json`
- `translations/en.json`

**Status: 🟡 Review required**

The fire-station address description should clearly explain:
`Straße Hausnummer, PLZ Ort`

Example:
`Vogelsangweg 14, 34346 Hann. Münden`

---

## 10. HACS / release 1.1.2

The manifest is prepared with version:

`1.1.2`

The HACS display name and Home Assistant integration name are aligned as:

**DIVERA 24/7 with Server URL**

Before publishing:
- test Home Assistant startup
- verify existing alarm sensors
- verify vehicle sensors
- verify vehicle trackers
- verify WebSocket vehicle updates
- verify route sensors
- verify incident close behaviour
- create Git tag `v1.1.2`
- create GitHub release `1.1.2`
- test HACS update

---

## 11. Development rules

1. Do not change stable backend/WebSocket logic without a concrete reason.
2. Keep the current route implementation; do not reintroduce the incompatible old Route Sensor approach.
3. Add dynamic vehicle entities without changing existing alarm entity IDs.
4. Keep vehicle status and vehicle position data read-only.
5. Update translations together.
6. Avoid unnecessary changes to existing unique IDs.
7. Test Home Assistant startup/reload behaviour before releases.
8. Test new functionality before increasing the version.

---

## 12. Current overall status

| Area | Status |
|---|---|
| DIVERA backend | 🟢 Stable |
| WebSocket | 🟢 Stable |
| Fallback polling | 🟢 Implemented |
| Config Flow | 🟢 Functional |
| Alarm sensors | 🟢 Implemented |
| Fire station tracker | 🟢 Implemented |
| Incident tracker | 🟢 Implemented |
| Vehicle sensors | 🟢 Implemented / HA test pending |
| Vehicle trackers | 🟢 Implemented / HA test pending |
| Vehicle WebSocket refresh | 🟢 Implemented |
| Current routing | 🟢 Retained |
| Old incompatible Route Sensor | 🔴 Not reintroduced |
| Map presentation | 🟡 Next development step |
| Translations | 🟡 Review required |
| Release 1.1.2 | 🟡 Ready for user tag/release after testing |

---

## 13. Reference implementation

The vehicle entity design was based on the relevant parts of `moehrem/DiveraControl`.

DiveraControl documents vehicle data, vehicle positions and status as part of its APIv2 functionality. The current implementation intentionally takes only the relevant read-side vehicle functionality and does **not** copy its older route-sensor approach.

---

## 14. Guiding principle

The repository remains a **working technical baseline**.

Priority:

**Stability → alarm/vehicle data → sensor/tracker testing → routing → map → UI/translations → release**
