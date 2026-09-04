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

NO_ALARM_STATE = "Kein aktiver Einsatz"


def _fmt_ts(unix: int | None) -> str | None:
    """Unix-Zeitstempel in ISO-Zeit umwandeln."""
    if unix is None:
        return None

    try:
        return datetime.fromtimestamp(
            unix,
            tz=timezone.utc,
        ).isoformat()
    except (TypeError, ValueError, OSError):
        return str(unix)


def _get_server_hash(base_url: str) -> str:
    """Eindeutigen Hash für den DIVERA Server erzeugen."""
    return hashlib.sha1(
        base_url.encode("utf-8")
    ).hexdigest()[:8]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """DIVERA Sensoren erstellen."""
    coordinator: DiveraCoordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities(
        [
            DiveraSensor(coordinator, entry),
            DiveraAlarmTextSensor(coordinator, entry),
        ]
    )


class DiveraSensor(
    CoordinatorEntity[DiveraCoordinator],
    SensorEntity,
):
    """DIVERA Alarm Sensor."""

    def __init__(
        self,
        coordinator: DiveraCoordinator,
        entry: ConfigEntry,
    ) -> None:
        super().__init__(coordinator)

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

        self._attr_name = f"DIVERA {ucr_name}"

        self._attr_unique_id = (
            f"divera_{unique_id}"
        )

        self._attr_device_info = DeviceInfo(
            identifiers={
                (DOMAIN, unique_id)
            },
            name=f"DIVERA 24/7 – {ucr_name}",
            manufacturer="DIVERA GmbH",
            model="DIVERA 24/7",
        )

    @property
    def native_value(self) -> str:
        """Aktuellen Alarm als Sensorwert zurückgeben."""
        alarm = self.coordinator.data

        if alarm is None:
            return NO_ALARM_STATE

        return alarm.get(
            "title"
        ) or NO_ALARM_STATE

    @property
    def extra_state_attributes(self) -> dict:
        """Alarmdaten als Sensorattribute bereitstellen."""
        alarm = self.coordinator.data

        if alarm is None:
            return {}

        attrs: dict = {}

        # Bekannte Felder mit deutschen Bezeichnungen.
        attrs["stichwort"] = alarm.get("title")
        attrs["beschreibung"] = alarm.get("text")
        attrs["adresse"] = alarm.get("address")
        attrs["einsatz_id"] = alarm.get("id")
        attrs["prioritaet"] = alarm.get("priority")
        attrs["geschlossen"] = alarm.get("closed")
        attrs["alarmiert_am"] = _fmt_ts(
            alarm.get("date")
        )
        attrs["latitude"] = alarm.get("lat")
        attrs["longitude"] = alarm.get("lng")
        attrs["fahrzeuge"] = alarm.get("vehicles")

        # Alle übrigen API-Felder übernehmen.
        bekannte = {
            "title",
            "text",
            "address",
            "id",
            "priority",
            "closed",
            "date",
            "lat",
            "lng",
            "vehicles",
        }

        for key, value in alarm.items():
            if key not in bekannte:
                attrs[key] = value

        # None-Werte entfernen.
        return {
            key: value
            for key, value in attrs.items()
            if value is not None
        }


class DiveraAlarmTextSensor(
    CoordinatorEntity[DiveraCoordinator],
    SensorEntity,
):
    """Sensor für den Alarmtext."""

    def __init__(
        self,
        coordinator: DiveraCoordinator,
        entry: ConfigEntry,
    ) -> None:
        super().__init__(coordinator)

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

        self._attr_name = f"DIVERA Alarmtext {ucr_name}"

        self._attr_unique_id = (
            f"divera_alarmtext_{unique_id}"
        )

        self._attr_device_info = DeviceInfo(
            identifiers={
                (DOMAIN, unique_id)
            },
            name=f"DIVERA 24/7 – {ucr_name}",
            manufacturer="DIVERA GmbH",
            model="DIVERA 24/7",
        )

    @property
    def native_value(self) -> str:
        """Alarmtext als Sensorwert zurückgeben."""
        alarm = self.coordinator.data

        if alarm is None:
            return ""

        text = alarm.get("text")

        if text is None:
            return ""

        # Sensorzustände sollten nicht unnötig lang werden.
        return str(text)[:255]

    @property
    def extra_state_attributes(self) -> dict:
        """Zusätzliche Informationen zum Alarmtext."""
        alarm = self.coordinator.data

        if alarm is None:
            return {}

        text = alarm.get("text")

        if text is None:
            return {}

        return {
            "volltext": str(text),
            "stichwort": alarm.get("title"),
            "adresse": alarm.get("address"),
            "einsatz_id": alarm.get("id"),
        }
