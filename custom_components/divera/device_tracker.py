"""DIVERA 24/7 device tracker entities."""
from __future__ import annotations

from homeassistant.components.device_tracker import (
    SourceType,
    TrackerEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_BASE_URL, CONF_UCR_ID, CONF_UCR_NAME, DOMAIN
from .coordinator import DiveraCoordinator


def _get_server_hash(base_url: str) -> str:
    """Eindeutigen Hash für den DIVERA Server erzeugen."""
    import hashlib

    return hashlib.sha1(
        base_url.encode("utf-8")
    ).hexdigest()[:8]


def _get_unique_id(
    entry: ConfigEntry,
    prefix: str = "",
) -> tuple[str, str, str]:
    """Eindeutige IDs und Namen erzeugen."""
    ucr_name: str = entry.data.get(
        CONF_UCR_NAME,
        "DIVERA",
    )

    ucr_id: str = entry.data.get(
        CONF_UCR_ID,
        entry.entry_id,
    )

    base_url: str = entry.data.get(
        CONF_BASE_URL,
        "",
    )

    server_hash = _get_server_hash(base_url)
    unique_id = f"{server_hash}_{ucr_id}"

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
        name=f"DIVERA 24/7 – {ucr_name}",
        manufacturer="DIVERA GmbH",
        model="DIVERA 24/7",
    )


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """DIVERA Einsatzort als Device Tracker erstellen."""
    coordinator: DiveraCoordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities(
        [
            DiveraIncidentLocationTracker(
                coordinator,
                entry,
            )
        ]
    )


class DiveraIncidentLocationTracker(
    CoordinatorEntity[DiveraCoordinator],
    TrackerEntity,
):
    """Einsatzort als Kartenposition."""

    _attr_source_type = SourceType.GPS
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: DiveraCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Device Tracker initialisieren."""
        super().__init__(coordinator)

        ucr_name, unique_id, tracker_id = _get_unique_id(
            entry,
            "einsatzort_",
        )

        self._attr_name = (
            f"DIVERA Einsatzort {ucr_name}"
        )

        self._attr_unique_id = tracker_id

        self._attr_device_info = _get_device_info(
            ucr_name,
            unique_id,
        )

    @property
    def latitude(self) -> float | None:
        """Breitengrad des Einsatzortes."""
        alarm = self.coordinator.data

        if alarm is None:
            return None

        value = alarm.get("lat")

        try:
            return float(value) if value is not None else None
        except (TypeError, ValueError):
            return None

    @property
    def longitude(self) -> float | None:
        """Längengrad des Einsatzortes."""
        alarm = self.coordinator.data

        if alarm is None:
            return None

        value = alarm.get("lng")

        try:
            return float(value) if value is not None else None
        except (TypeError, ValueError):
            return None

    @property
    def location_accuracy(self) -> int:
        """Genauigkeit der Einsatzposition."""
        return 0

    @property
    def extra_state_attributes(self) -> dict:
        """Zusätzliche Einsatzinformationen."""
        alarm = self.coordinator.data

        if alarm is None:
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
