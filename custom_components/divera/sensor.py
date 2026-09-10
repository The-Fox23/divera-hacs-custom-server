"""DIVERA 24/7 sensor entities."""
from __future__ import annotations

import hashlib
from datetime import datetime, timezone

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_BASE_URL, CONF_UCR_ID, CONF_UCR_NAME, DOMAIN
from .coordinator import DiveraCoordinator
from .route import DiveraRouteCoordinator

NO_ALARM_STATE = "Kein aktiver Einsatz"


def _fmt_ts(value) -> str | None:
    if value is None:
        return None
    try:
        return datetime.fromtimestamp(int(value), tz=timezone.utc).isoformat()
    except (TypeError, ValueError, OSError):
        return str(value)


def _ids(entry: ConfigEntry, prefix: str = "") -> tuple[str, str, str]:
    name = entry.data.get(CONF_UCR_NAME, "DIVERA")
    ucr = entry.data.get(CONF_UCR_ID, entry.entry_id)
    server = hashlib.sha1(entry.data.get(CONF_BASE_URL, "").encode()).hexdigest()[:8]
    uid = f"{server}_{ucr}"
    return name, uid, f"divera_{prefix}{uid}"


def _device(name: str, uid: str) -> DeviceInfo:
    return DeviceInfo(
        identifiers={(DOMAIN, uid)},
        name=f"DIVERA 24/7 – {name}",
        manufacturer="DIVERA GmbH",
        model="DIVERA 24/7",
    )


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: DiveraCoordinator = hass.data[DOMAIN][entry.entry_id]
    route: DiveraRouteCoordinator = hass.data[f"{DOMAIN}_route"][entry.entry_id]
    async_add_entities([
        DiveraAlarmSensor(coordinator, entry),
        DiveraAlarmTextSensor(coordinator, entry),
        DiveraAddressSensor(coordinator, entry),
        DiveraAlarmIdSensor(coordinator, entry),
        DiveraAlarmTimeSensor(coordinator, entry),
        DiveraDurationSensor(coordinator, entry),
        DiveraRecipientsSensor(coordinator, entry),
        DiveraReadSensor(coordinator, entry),
        DiveraReportSensor(coordinator, entry),
        DiveraLatitudeSensor(coordinator, entry),
        DiveraLongitudeSensor(coordinator, entry),
        DiveraRouteDistanceSensor(route, entry),
        DiveraRouteDurationSensor(route, entry),
        DiveraRouteStatusSensor(route, entry),
        DiveraRouteGeometrySensor(route, entry),
    ])


class _Base(CoordinatorEntity[DiveraCoordinator], SensorEntity):
    def __init__(self, coordinator: DiveraCoordinator, entry: ConfigEntry, prefix: str, name: str):
        super().__init__(coordinator)
        ucr_name, uid, entity_id = _ids(entry, prefix)
        self._attr_name = f"{name} {ucr_name}"
        self._attr_unique_id = entity_id
        self._attr_device_info = _device(ucr_name, uid)

    @property
    def alarm(self) -> dict | None:
        return self.coordinator.data if isinstance(self.coordinator.data, dict) else None


class DiveraAlarmSensor(_Base):
    def __init__(self, c, e): super().__init__(c, e, "", "DIVERA")
    @property
    def native_value(self): return (self.alarm or {}).get("title") or NO_ALARM_STATE
    @property
    def extra_state_attributes(self):
        a = self.alarm
        if not a: return {}
        known = {"title","text","address","id","priority","closed","date","lat","lng","vehicles"}
        attrs = {
            "stichwort": a.get("title"), "beschreibung": a.get("text"), "adresse": a.get("address"),
            "einsatz_id": a.get("id"), "prioritaet": a.get("priority"), "geschlossen": a.get("closed"),
            "alarmiert_am": _fmt_ts(a.get("date")), "latitude": a.get("lat"), "longitude": a.get("lng"),
            "fahrzeuge": a.get("vehicles"),
        }
        attrs.update({k:v for k,v in a.items() if k not in known})
        return {k:v for k,v in attrs.items() if v is not None}


class DiveraAlarmTextSensor(_Base):
    def __init__(self,c,e): super().__init__(c,e,"alarmtext_","DIVERA Alarmtext")
    @property
    def native_value(self): return str((self.alarm or {}).get("text") or "")[:255]
    @property
    def extra_state_attributes(self):
        a=self.alarm or {}; return {k:v for k,v in {"volltext":a.get("text"),"stichwort":a.get("title"),"adresse":a.get("address"),"einsatz_id":a.get("id")}.items() if v is not None}


class DiveraAddressSensor(_Base):
    def __init__(self,c,e): super().__init__(c,e,"adresse_","DIVERA Einsatzadresse")
    @property
    def native_value(self): return str((self.alarm or {}).get("address") or "")


class DiveraAlarmIdSensor(_Base):
    def __init__(self,c,e): super().__init__(c,e,"einsatz_id_","DIVERA Einsatz ID")
    @property
    def native_value(self):
        v=(self.alarm or {}).get("id"); return str(v) if v is not None else ""


class DiveraAlarmTimeSensor(_Base):
    def __init__(self,c,e): super().__init__(c,e,"alarmzeit_","DIVERA Alarmzeit")
    @property
    def native_value(self): return _fmt_ts((self.alarm or {}).get("date")) or ""


class DiveraDurationSensor(_Base):
    def __init__(self,c,e): super().__init__(c,e,"einsatzdauer_","DIVERA Einsatzdauer")
    @property
    def native_value(self): return str((self.alarm or {}).get("duration") or "")


class DiveraRecipientsSensor(_Base):
    def __init__(self,c,e):
        super().__init__(c,e,"alarmierte_","DIVERA Alarmierte"); self._attr_native_unit_of_measurement="Personen"
    @property
    def native_value(self): return int((self.alarm or {}).get("count_recipients") or 0)


class DiveraReadSensor(_Base):
    def __init__(self,c,e):
        super().__init__(c,e,"gelesen_","DIVERA Gelesen"); self._attr_native_unit_of_measurement="Personen"
    @property
    def native_value(self): return int((self.alarm or {}).get("count_read") or 0)


class DiveraReportSensor(_Base):
    def __init__(self,c,e): super().__init__(c,e,"bericht_","DIVERA Einsatzbericht")
    @property
    def native_value(self): return str((self.alarm or {}).get("report") or "")


class _CoordinateSensor(_Base):
    key = ""
    unit = "°"
    def __init__(self,c,e,prefix,name):
        super().__init__(c,e,prefix,name); self._attr_native_unit_of_measurement=self.unit
    @property
    def native_value(self):
        value=(self.alarm or {}).get(self.key)
        try: return float(value) if value is not None else None
        except (TypeError,ValueError): return None


class DiveraLatitudeSensor(_CoordinateSensor):
    key="lat"
    def __init__(self,c,e): super().__init__(c,e,"latitude_","DIVERA Latitude")


class DiveraLongitudeSensor(_CoordinateSensor):
    key="lng"
    def __init__(self,c,e): super().__init__(c,e,"longitude_","DIVERA Longitude")


class _RouteSensor(CoordinatorEntity[DiveraRouteCoordinator], SensorEntity):
    def __init__(self, coordinator: DiveraRouteCoordinator, entry: ConfigEntry, prefix: str, name: str):
        super().__init__(coordinator)
        ucr_name, uid, entity_id = _ids(entry, prefix)
        self._attr_name=f"{name} {ucr_name}"
        self._attr_unique_id=entity_id
        self._attr_device_info=_device(ucr_name, uid)

    @property
    def route(self): return self.coordinator.data


class DiveraRouteDistanceSensor(_RouteSensor):
    def __init__(self,c,e):
        super().__init__(c,e,"routenentfernung_","DIVERA Routenentfernung"); self._attr_native_unit_of_measurement="km"
    @property
    def native_value(self):
        r=self.route; return round(r["distance_m"]/1000,1) if r else None


class DiveraRouteDurationSensor(_RouteSensor):
    def __init__(self,c,e):
        super().__init__(c,e,"routenfahrzeit_","DIVERA Fahrzeit")
        self._attr_native_unit_of_measurement="min"
    @property
    def native_value(self):
        r=self.route; return round(r["duration_s"]/60,1) if r else None


class DiveraRouteStatusSensor(_RouteSensor):
    def __init__(self,c,e): super().__init__(c,e,"routenstatus_","DIVERA Routenstatus")
    @property
    def native_value(self): return "Route vorhanden" if self.route else "Keine aktive Route"
    @property
    def extra_state_attributes(self):
        r=self.route or {}; return {k:v for k,v in r.items() if k != "geometry"}


class DiveraRouteGeometrySensor(_RouteSensor):
    def __init__(self,c,e): super().__init__(c,e,"route_geojson_","DIVERA Route GeoJSON")
    @property
    def native_value(self): return "Route vorhanden" if self.route else "Keine aktive Route"
    @property
    def extra_state_attributes(self):
        r=self.route
        if not r: return {}
        return {"geometry": {"type":"LineString","coordinates":r.get("geometry",[])}}
