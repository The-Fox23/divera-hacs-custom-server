"""DIVERA 24/7 device tracker entities."""
from __future__ import annotations

import hashlib

from homeassistant.components.device_tracker import (
    SourceType,
    TrackerEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers import entity_registry as er
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


def _get_server_hash(base_url: str) -> str:
    """Eindeutigen Hash für den DIVERA Server erzeugen."""
    return hashlib.sha1(
        base_url.encode("utf-8")
    ).hexdigest()[:8]


def _get_unique_id(
    entry: ConfigEntry,
    prefix: str = "",
) -> tuple[str, str, str]:
    """Eindeutige IDs und Namen erzeugen."""
    ucr_name = entry.data.get(
        CONF_UCR_NAME,
        "DIVERA",
    )

    ucr_id = entry.data.get(
        CONF_UCR_ID,
        entry.entry_id,
    )

    base_url = entry.data.get(
        CONF_BASE_URL,
        "",
    )

    server_hash = _get_server_hash(
        base_url
    )

    unique_id = (
        f"{server_hash}_{ucr_id}"
    )

    return (
        ucr_name,
        unique_id,
        f"divera_{prefix}{unique_id}",
    )


def _get_device_info(
    ucr_name: str,
    unique_id: str,
) -> DeviceInfo:
    """Gemeinsame Geräteinformationen erzeugen."""
    return DeviceInfo(
        identifiers={
            (DOMAIN, unique_id)
        },
        name=(
            f"DIVERA 24/7 – {ucr_name}"
        ),
        manufacturer="DIVERA GmbH",
        model="DIVERA 24/7",
    )


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """DIVERA Tracker erstellen."""
    coordinator: DiveraCoordinator = (
        hass.data[DOMAIN][entry.entry_id]
    )

    async_add_entities(
        [
            DiveraStationTracker(
                entry
            ),
            DiveraIncidentLocationTracker(
                coordinator,
                entry,
            ),
        ]
    )

    vehicle_manager = DiveraVehicleTrackerManager(coordinator, entry, async_add_entities)
    hass.data.setdefault(f"{DOMAIN}_vehicle_trackers", {})[entry.entry_id] = vehicle_manager
    vehicle_manager.start()


class DiveraStationTracker(TrackerEntity):
    """Fester Standort der Feuerwache."""

    _attr_source_type = SourceType.GPS
    _attr_has_entity_name = True

    def __init__(
        self,
        entry: ConfigEntry,
    ) -> None:
        """Tracker initialisieren."""
        ucr_name, unique_id, tracker_id = (
            _get_unique_id(
                entry,
                "feuerwache_",
            )
        )

        self._attr_name = (
            f"DIVERA Feuerwache {ucr_name}"
        )

        self._attr_unique_id = tracker_id

        self._attr_device_info = (
            _get_device_info(
                ucr_name,
                unique_id,
            )
        )

        self._latitude = _to_float(
            entry.data.get(
                CONF_STATION_LATITUDE
            )
        )

        self._longitude = _to_float(
            entry.data.get(
                CONF_STATION_LONGITUDE
            )
        )

        self._address = entry.data.get(
            CONF_STATION_ADDRESS,
            "",
        )

    @property
    def latitude(self) -> float | None:
        """Breitengrad der Feuerwache."""
        return self._latitude

    @property
    def longitude(self) -> float | None:
        """Längengrad der Feuerwache."""
        return self._longitude

    @property
    def location_accuracy(self) -> int:
        """Genauigkeit der Position."""
        return 0

    @property
    def extra_state_attributes(self) -> dict:
        """Informationen zur Feuerwache."""
        return {
            "adresse": self._address,
        }


class DiveraVehicleTrackerManager:
    """Manages dynamic vehicle location trackers."""

    def __init__(self, coordinator, entry, async_add_entities) -> None:
        self.coordinator = coordinator
        self.entry = entry
        self.hass = coordinator.hass
        self._add = async_add_entities
        self._known: set[str] = set()
        self._unsub = None

    def start(self) -> None:
        if self._unsub is None:
            self._unsub = self.coordinator.async_add_listener(self._sync)
            self._sync()

    @callback
    def _sync(self) -> None:
        vehicles = self.coordinator.data.get("vehicles", {}) if self.coordinator.data else {}
        vehicles = vehicles if isinstance(vehicles, dict) else {}
        current = {str(v) for v in vehicles}
        removed = self._known - current
        registry = er.async_get(self.hass)
        for vehicle_id in removed:
            _, uid, _ = _get_unique_id(self.entry, f"fahrzeug_{vehicle_id}_")
            unique_id = f"divera_fahrzeug_{vehicle_id}_{uid}"
            entity_id = registry.async_get_entity_id("device_tracker", DOMAIN, unique_id)
            if entity_id:
                registry.async_remove(entity_id)
        self._known -= removed
        new_ids = current - self._known
        if new_ids:
            self._add(
                [DiveraVehicleTracker(self.coordinator, self.entry, v) for v in new_ids],
                update_before_add=False,
            )
            self._known |= new_ids


class DiveraVehicleTracker(CoordinatorEntity[DiveraCoordinator], TrackerEntity):
    """Current GPS position of one DIVERA vehicle."""

    _attr_source_type = SourceType.GPS
    _attr_has_entity_name = True

    def __init__(self, coordinator, entry, vehicle_id: str) -> None:
        super().__init__(coordinator)
        self.vehicle_id = str(vehicle_id)
        ucr_name, uid, _ = _get_unique_id(entry, f"fahrzeug_{self.vehicle_id}_")
        self._attr_name = f"DIVERA Fahrzeug {self.vehicle_id} {ucr_name}"
        self._attr_unique_id = f"divera_fahrzeug_{self.vehicle_id}_{uid}"
        self._attr_device_info = _get_device_info(ucr_name, uid)

    @property
    def vehicle(self) -> dict:
        vehicles = self.coordinator.data.get("vehicles", {}) if self.coordinator.data else {}
        value = vehicles.get(self.vehicle_id, {})
        return value if isinstance(value, dict) else {}

    @property
    def available(self) -> bool:
        return super().available and bool(self.vehicle)

    @property
    def latitude(self) -> float | None:
        return _to_float(self.vehicle.get("lat"))

    @property
    def longitude(self) -> float | None:
        return _to_float(self.vehicle.get("lng"))

    @property
    def location_accuracy(self) -> int:
        return _to_int(self.vehicle.get("gps_accuracy"), 0)

    @property
    def icon(self) -> str:
        return "mdi:fire-truck"

    @property
    def extra_state_attributes(self) -> dict:
        vehicle = dict(self.vehicle)
        status_id = vehicle.get("fmsstatus_id")
        statuses = self.coordinator.data.get("fms_status", {}) if self.coordinator.data else {}
        items = statuses.get("items", statuses) if isinstance(statuses, dict) else {}
        status = items.get(str(status_id), {}) if isinstance(items, dict) and status_id is not None else {}
        if isinstance(status, dict):
            vehicle["fms_status_name"] = status.get("name")
            vehicle["fms_status_color"] = status.get("color_hex")
        vehicle["fahrzeug_id"] = self.vehicle_id
        return vehicle


class DiveraIncidentLocationTracker(
    CoordinatorEntity[DiveraCoordinator],
    TrackerEntity,
):
    """DIVERA Einsatzort als Kartenposition."""

    _attr_source_type = SourceType.GPS
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: DiveraCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Device Tracker initialisieren."""
        super().__init__(coordinator)

        ucr_name, unique_id, tracker_id = (
            _get_unique_id(
                entry,
                "einsatzort_",
            )
        )

        self._attr_name = (
            f"DIVERA Einsatzort {ucr_name}"
        )

        self._attr_unique_id = tracker_id

        self._attr_device_info = (
            _get_device_info(
                ucr_name,
                unique_id,
            )
        )

    @property
    def latitude(self) -> float | None:
        """Breitengrad des Einsatzortes."""
        alarm = self.coordinator.data

        if not _is_active_alarm(alarm):
            return None

        return _to_float(
            alarm.get("lat")
        )

    @property
    def longitude(self) -> float | None:
        """Längengrad des Einsatzortes."""
        alarm = self.coordinator.data

        if not _is_active_alarm(alarm):
            return None

        return _to_float(
            alarm.get("lng")
        )

    @property
    def location_accuracy(self) -> int:
        """Genauigkeit der Einsatzposition."""
        return 0

    @property
    def extra_state_attributes(self) -> dict:
        """Zusätzliche Einsatzinformationen."""
        alarm = self.coordinator.data

        if not _is_active_alarm(alarm):
            return {}

        attributes = {
            "einsatz_id": alarm.get("id"),
            "stichwort": alarm.get("title"),
            "beschreibung": alarm.get("text"),
            "adresse": alarm.get("address"),
            "prioritaet": alarm.get("priority"),
            "alarmiert_am": alarm.get("date"),
        }

        return {
            key: value
            for key, value in attributes.items()
            if value is not None
        }


def _to_int(value, default: int = 0) -> int:
    try:
        return int(value) if value is not None else default
    except (TypeError, ValueError):
        return default


def _to_float(value) -> float | None:
    """Wert sicher in float umwandeln."""
    try:
        return (
            float(value)
            if value is not None
            else None
        )
    except (TypeError, ValueError):
        return None


def _is_active_alarm(
    alarm: dict | None,
) -> bool:
    """Prüfen, ob ein gültiger aktiver Einsatz vorhanden ist."""
    if not isinstance(alarm, dict):
        return False

    if alarm.get("closed") is True:
        return False

    lat = _to_float(
        alarm.get("lat")
    )

    lng = _to_float(
        alarm.get("lng")
    )

    if lat is None or lng is None:
        return False

    return (
        -90 <= lat <= 90
        and -180 <= lng <= 180
    )
