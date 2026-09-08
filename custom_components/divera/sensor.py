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
    """DIVERA Sensoren erstellen."""
    coordinator: DiveraCoordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities(
        [
            DiveraSensor(coordinator, entry),
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

        ucr_name, unique_id, sensor_id = _get_unique_id(
            entry
        )

        self._attr_name = f"DIVERA {ucr_name}"
        self._attr_unique_id = sensor_id
        self._attr_device_info = _get_device_info(
            ucr_name,
            unique_id,
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

        ucr_name, unique_id, sensor_id = _get_unique_id(
            entry,
            "alarmtext_",
        )

        self._attr_name = (
            f"DIVERA Alarmtext {ucr_name}"
        )

        self._attr_unique_id = sensor_id

        self._attr_device_info = _get_device_info(
            ucr_name,
            unique_id,
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


class DiveraAddressSensor(
    CoordinatorEntity[DiveraCoordinator],
    SensorEntity,
):
    """Sensor für die Einsatzadresse."""

    def __init__(
        self,
        coordinator: DiveraCoordinator,
        entry: ConfigEntry,
    ) -> None:
        super().__init__(coordinator)

        ucr_name, unique_id, sensor_id = _get_unique_id(
            entry,
            "adresse_",
        )

        self._attr_name = (
            f"DIVERA Einsatzadresse {ucr_name}"
        )

        self._attr_unique_id = sensor_id

        self._attr_device_info = _get_device_info(
            ucr_name,
            unique_id,
        )

    @property
    def native_value(self) -> str:
        """Einsatzadresse zurückgeben."""
        alarm = self.coordinator.data

        if alarm is None:
            return ""

        return str(
            alarm.get("address") or ""
        )


class DiveraAlarmIdSensor(
    CoordinatorEntity[DiveraCoordinator],
    SensorEntity,
):
    """Sensor für die Einsatz-ID."""

    def __init__(
        self,
        coordinator: DiveraCoordinator,
        entry: ConfigEntry,
    ) -> None:
        super().__init__(coordinator)

        ucr_name, unique_id, sensor_id = _get_unique_id(
            entry,
            "einsatz_id_",
        )

        self._attr_name = (
            f"DIVERA Einsatz ID {ucr_name}"
        )

        self._attr_unique_id = sensor_id

        self._attr_device_info = _get_device_info(
            ucr_name,
            unique_id,
        )

    @property
    def native_value(self) -> str:
        """Einsatz-ID zurückgeben."""
        alarm = self.coordinator.data

        if alarm is None:
            return ""

        value = alarm.get("id")

        return str(value) if value is not None else ""


class DiveraAlarmTimeSensor(
    CoordinatorEntity[DiveraCoordinator],
    SensorEntity,
):
    """Sensor für die Alarmzeit."""

    def __init__(
        self,
        coordinator: DiveraCoordinator,
        entry: ConfigEntry,
    ) -> None:
        super().__init__(coordinator)

        ucr_name, unique_id, sensor_id = _get_unique_id(
            entry,
            "alarmzeit_",
        )

        self._attr_name = (
            f"DIVERA Alarmzeit {ucr_name}"
        )

        self._attr_unique_id = sensor_id

        self._attr_device_info = _get_device_info(
            ucr_name,
            unique_id,
        )

    @property
    def native_value(self) -> str:
        """Alarmzeit zurückgeben."""
        alarm = self.coordinator.data

        if alarm is None:
            return ""

        timestamp = alarm.get("date")

        return _fmt_ts(timestamp) or ""


class DiveraDurationSensor(
    CoordinatorEntity[DiveraCoordinator],
    SensorEntity,
):
    """Sensor für die Einsatzdauer."""

    def __init__(
        self,
        coordinator: DiveraCoordinator,
        entry: ConfigEntry,
    ) -> None:
        super().__init__(coordinator)

        ucr_name, unique_id, sensor_id = _get_unique_id(
            entry,
            "einsatzdauer_",
        )

        self._attr_name = (
            f"DIVERA Einsatzdauer {ucr_name}"
        )

        self._attr_unique_id = sensor_id

        self._attr_device_info = _get_device_info(
            ucr_name,
            unique_id,
        )

    @property
    def native_value(self) -> str:
        """Einsatzdauer zurückgeben."""
        alarm = self.coordinator.data

        if alarm is None:
            return ""

        return str(
            alarm.get("duration") or ""
        )


class DiveraRecipientsSensor(
    CoordinatorEntity[DiveraCoordinator],
    SensorEntity,
):
    """Sensor für die Anzahl der alarmierten Empfänger."""

    def __init__(
        self,
        coordinator: DiveraCoordinator,
        entry: ConfigEntry,
    ) -> None:
        super().__init__(coordinator)

        ucr_name, unique_id, sensor_id = _get_unique_id(
            entry,
            "alarmierte_",
        )

        self._attr_name = (
            f"DIVERA Alarmierte {ucr_name}"
        )

        self._attr_unique_id = sensor_id
        self._attr_native_unit_of_measurement = "Personen"

        self._attr_device_info = _get_device_info(
            ucr_name,
            unique_id,
        )

    @property
    def native_value(self) -> int:
        """Anzahl der alarmierten Empfänger."""
        alarm = self.coordinator.data

        if alarm is None:
            return 0

        return int(
            alarm.get("count_recipients") or 0
        )


class DiveraReadSensor(
    CoordinatorEntity[DiveraCoordinator],
    SensorEntity,
):
    """Sensor für die Anzahl der gelesenen Alarmierungen."""

    def __init__(
        self,
        coordinator: DiveraCoordinator,
        entry: ConfigEntry,
    ) -> None:
        super().__init__(coordinator)

        ucr_name, unique_id, sensor_id = _get_unique_id(
            entry,
            "gelesen_",
        )

        self._attr_name = (
            f"DIVERA Gelesen {ucr_name}"
        )

        self._attr_unique_id = sensor_id
        self._attr_native_unit_of_measurement = "Personen"

        self._attr_device_info = _get_device_info(
            ucr_name,
            unique_id,
        )

    @property
    def native_value(self) -> int:
        """Anzahl der gelesenen Alarmierungen."""
        alarm = self.coordinator.data

        if alarm is None:
            return 0

        return int(
            alarm.get("count_read") or 0
        )


class DiveraReportSensor(
    CoordinatorEntity[DiveraCoordinator],
    SensorEntity,
):
    """Sensor für den Einsatzbericht."""

    def __init__(
        self,
        coordinator: DiveraCoordinator,
        entry: ConfigEntry,
    ) -> None:
        super().__init__(coordinator)

        ucr_name, unique_id, sensor_id = _get_unique_id(
            entry,
            "bericht_",
        )

        self._attr_name = (
            f"DIVERA Einsatzbericht {ucr_name}"
        )

        self._attr_unique_id = sensor_id

        self._attr_device_info = _get_device_info(
            ucr_name,
            unique_id,
        )

    @property
    def native_value(self) -> str:
        """Einsatzbericht zurückgeben."""
        alarm = self.coordinator.data

        if alarm is None:
            return ""

        return str(
            alarm.get("report") or ""
        )


class DiveraLatitudeSensor(
    CoordinatorEntity[DiveraCoordinator],
    SensorEntity,
):
    """Sensor für den Breitengrad."""

    def __init__(
        self,
        coordinator: DiveraCoordinator,
        entry: ConfigEntry,
    ) -> None:
        super().__init__(coordinator)

        ucr_name, unique_id, sensor_id = _get_unique_id(
            entry,
            "latitude_",
        )

        self._attr_name = (
            f"DIVERA Latitude {ucr_name}"
        )

        self._attr_unique_id = sensor_id
        self._attr_native_unit_of_measurement = "°"

        self._attr_device_info = _get_device_info(
            ucr_name,
            unique_id,
        )

    @property
    def native_value(self) -> float | None:
        """Breitengrad zurückgeben."""
        alarm = self.coordinator.data

        if alarm is None:
            return None

        value = alarm.get("lat")

        try:
            return float(value) if value is not None else None
        except (TypeError, ValueError):
            return None


class DiveraLongitudeSensor(
    CoordinatorEntity[DiveraCoordinator],
    SensorEntity,
):
    """Sensor für den Längengrad."""

    def __init__(
        self,
        coordinator: DiveraCoordinator,
        entry: ConfigEntry,
    ) -> None:
        super().__init__(coordinator)

        ucr_name, unique_id, sensor_id = _get_unique_id(
            entry,
            "longitude_",
        )

        self._attr_name = (
            f"DIVERA Longitude {ucr_name}"
        )

        self._attr_unique_id = sensor_id
        self._attr_native_unit_of_measurement = "°"

        self._attr_device_info = _get_device_info(
            ucr_name,
            unique_id,
        )

    @property
    def native_value(self) -> float | None:
        """Längengrad zurückgeben."""
        alarm = self.coordinator.data

        if alarm is None:
            return None

        value = alarm.get("lng")

        try:
            return float(value) if value is not None else None
        except (TypeError, ValueError):
            return None
