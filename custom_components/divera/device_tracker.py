"""DIVERA 24/7 map entities."""
from __future__ import annotations

import hashlib

from homeassistant.components.device_tracker import SourceType, TrackerEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    CONF_BASE_URL,
    CONF_STATION_ADDRESS,
    CONF_STATION_LATITUDE,
    CONF_STATION_LONGITUDE,
    CONF_UCR_ID,
    CONF_UCR_NAME,
    DOMAIN,
)
from .coordinator import DiveraCoordinator


def _ids(entry: ConfigEntry, prefix: str) -> tuple[str, str, str]:
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
    async_add_entities(
        [
            DiveraStationTracker(entry),
            DiveraIncidentTracker(coordinator, entry),
        ]
    )


class DiveraStationTracker(TrackerEntity):
    """Permanent station position."""

    _attr_source_type = SourceType.GPS
    _attr_has_entity_name = True

    def __init__(self, entry: ConfigEntry) -> None:
        name, uid, entity_id = _ids(entry, "feuerwache_")
        self._attr_name = f"DIVERA Feuerwache {name}"
        self._attr_unique_id = entity_id
        self._attr_device_info = _device(name, uid)
        self._lat = entry.data.get(CONF_STATION_LATITUDE)
        self._lng = entry.data.get(CONF_STATION_LONGITUDE)
        self._address = entry.data.get(CONF_STATION_ADDRESS, "")

    @property
    def latitude(self) -> float | None:
        try:
            return float(self._lat)
        except (TypeError, ValueError):
            return None

    @property
    def longitude(self) -> float | None:
        try:
            return float(self._lng)
        except (TypeError, ValueError):
            return None

    @property
    def location_accuracy(self) -> int:
        return 0

    @property
    def extra_state_attributes(self) -> dict:
        return {"adresse": self._address}


class DiveraIncidentTracker(CoordinatorEntity[DiveraCoordinator], TrackerEntity):
    """Current DIVERA incident location."""

    _attr_source_type = SourceType.GPS
    _attr_has_entity_name = True

    def __init__(self, coordinator: DiveraCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        name, uid, entity_id = _ids(entry, "einsatzort_")
        self._attr_name = f"DIVERA Einsatzort {name}"
        self._attr_unique_id = entity_id
        self._attr_device_info = _device(name, uid)

    def _alarm(self) -> dict | None:
        alarm = self.coordinator.data
        if not isinstance(alarm, dict) or alarm.get("closed") is True:
            return None
        return alarm

    @property
    def latitude(self) -> float | None:
        alarm = self._alarm()
        try:
            return float(alarm.get("lat")) if alarm and alarm.get("lat") is not None else None
        except (TypeError, ValueError):
            return None

    @property
    def longitude(self) -> float | None:
        alarm = self._alarm()
        try:
            return float(alarm.get("lng")) if alarm and alarm.get("lng") is not None else None
        except (TypeError, ValueError):
            return None

    @property
    def location_accuracy(self) -> int:
        return 0

    @property
    def extra_state_attributes(self) -> dict:
        alarm = self._alarm()
        if not alarm:
            return {}
        return {
            key: value
            for key, value in {
                "einsatz_id": alarm.get("id"),
                "stichwort": alarm.get("title"),
                "beschreibung": alarm.get("text"),
                "adresse": alarm.get("address"),
                "prioritaet": alarm.get("priority"),
                "alarmiert_am": alarm.get("date"),
            }.items()
            if value is not None
        }
