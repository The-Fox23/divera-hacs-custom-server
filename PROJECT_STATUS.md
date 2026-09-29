# DIVERA 24/7 – Custom Server Integration
## Project Status

**Repository:** `The-Fox23/divera-hacs-custom-server`  
**Integration:** DIVERA 24/7  
**Current manifest version:** `1.1.0`  
**Status:** 🟢 Functional development baseline

---

## 1. Project goal

This Home Assistant integration is based on the DIVERA 24/7 integration and extends it so that the DIVERA server URL can be configured freely.

Goals:
- support the public DIVERA server
- support self-hosted/private DIVERA servers
- configure DIVERA units/UCRs
- provide alarm information and sensors
- provide fire-station and incident locations
- calculate a route from the fire station to the incident

**Important:** The currently stable backend/WebSocket communication should not be changed without a concrete reason.

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

### WebSocket
**Status: 🟢 Stable / do not change unnecessarily**

Implemented:
- JWT retrieval
- WebSocket authentication
- `init`
- `cluster-pull`
- `jwtExpired`
- automatic reconnect
- exponential reconnect delay
- fallback polling

Current values:
- reconnect delay: 10 seconds
- maximum reconnect delay: 300 seconds
- fallback polling: 60 seconds

When WebSocket is active, fallback polling is disabled. When it is unavailable, 60-second polling is enabled.

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
- vehicle data
- additional DIVERA fields as attributes

---

## 4. Sensors

Current sensors include:
- DIVERA alarm/stichwort
- DIVERA alarm text
- DIVERA incident address
- DIVERA incident ID
- DIVERA alarm time
- DIVERA incident duration
- DIVERA alerted persons
- DIVERA read persons
- DIVERA incident report
- DIVERA latitude
- DIVERA longitude
- DIVERA route distance
- DIVERA route duration
- DIVERA route status
- DIVERA route GeoJSON

---

## 5. Fire station

The fire-station address is entered during setup and geocoded through Nominatim.

Example:
`Vogelsangweg 14, 34346 Hann. Münden`

Stored values:
- `station_address`
- `station_latitude`
- `station_longitude`

The coordinates are stored in the config entry.

### Known point
Geocoding may return a point somewhere along a street rather than the exact building. This is a limitation of the geocoding result and should be reviewed separately if greater precision is required.

---

## 6. Device trackers

### Fire station tracker
Provides the stored fire-station coordinates and address.

### Incident location tracker
Provides the current incident coordinates when:
- an active incident exists
- valid latitude/longitude are available
- the incident is not closed

Without a valid active incident, no incident position is exposed.

---

## 7. Routing

**Status: 🟢 Implemented / practical testing still required**

Routing is handled by a separate `DiveraRouteCoordinator`.

Current routing service:
`https://router.project-osrm.org`

Profile:
`driving`

The route contains:
- distance
- duration
- GeoJSON geometry
- incident ID
- incident coordinates

Routes are cached using rounded incident coordinates to avoid unnecessary repeated routing requests.

---

## 8. Planned map behaviour

### No active incident
- fire-station marker remains
- no incident marker
- no route

### Active incident
- fire-station marker
- red incident marker
- route
- distance
- travel time
- map centered on incident

### Incident closed
- incident marker removed
- route removed
- fire-station marker remains

The preferred presentation is a flexible Leaflet/Home Assistant map solution rather than putting unnecessary UI logic into the backend integration.

---

## 9. Translations

Files:
- `strings.json`
- `translations/de.json`
- `translations/en.json`

**Status: 🟡 Review required**

There is currently an inconsistency between `strings.json` and `translations/de.json` regarding the fire-station address description.

The German UI should clearly explain the expected format:

`Straße Hausnummer, PLZ Ort`

Example:

`Vogelsangweg 14, 34346 Hann. Münden`

Translations should remain synchronized across the supported languages.

---

## 10. HACS / release

Current manifest version:
`1.1.0`

HACS metadata is present.

Before the next release:
- review repository metadata
- review manifest version
- validate HACS structure
- update README if required
- test installation/update
- create commit
- create Git tag
- create GitHub release

---

## 11. Development rules

1. Do not change stable backend/WebSocket logic without a concrete reason.
2. Add new sensors primarily through `sensor.py`.
3. Keep routing separate from the DIVERA core.
4. Change the Config Flow only when required.
5. Update translations together.
6. Avoid unnecessary changes to entity IDs and unique IDs.
7. Test Home Assistant startup/reload behaviour before releases.
8. Test new functionality before increasing the version.
9. Avoid broad refactoring of already working functionality.

---

## 12. Next steps

### Phase 1 – Repository review
- [ ] review complete file structure
- [ ] review all Python files
- [ ] review Home Assistant compatibility
- [ ] review HACS configuration
- [ ] compare translations
- [ ] review entity structure
- [ ] identify potential bugs

### Phase 2 – Stabilization
- [ ] fix identified issues
- [ ] leave stable WebSocket/backend logic untouched
- [ ] test sensors
- [ ] test device trackers
- [ ] test routing
- [ ] test incident close behaviour

### Phase 3 – Map
- [ ] decide final map solution
- [ ] show fire station
- [ ] show incident
- [ ] show route
- [ ] show distance
- [ ] show travel time
- [ ] center on incident
- [ ] remove route/incident after closure

### Phase 4 – Release
- [ ] finalize README
- [ ] finalize translations
- [ ] increase version
- [ ] commit
- [ ] tag
- [ ] GitHub release
- [ ] HACS update test

---

## 13. Current overall status

| Area | Status |
|---|---|
| DIVERA backend | 🟢 Stable |
| WebSocket | 🟢 Stable |
| Fallback polling | 🟢 Implemented |
| Config Flow | 🟢 Functional / review pending |
| Alarm sensors | 🟢 Implemented |
| Fire station tracker | 🟢 Implemented |
| Incident tracker | 🟢 Implemented |
| Routing | 🟢 Implemented / practical test pending |
| Route sensors | 🟢 Implemented |
| Map presentation | 🟡 Technical basis available |
| Translations | 🟡 Review required |
| HACS / release | 🟡 Review required |

---

## 14. Guiding principle

The current repository should be treated as a **working technical baseline**.

The next development step is therefore a complete repository review before making further functional changes.

Priority:

**Stability → bug fixing → data/sensors → routing → map → UI/translations → release**
