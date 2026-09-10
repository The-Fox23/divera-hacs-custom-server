"""DIVERA 24/7 route sensors."""
from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    CONF_BASE_URL,
    CONF_UCR_ID,
    CONF_UCR_NAME,
    DOMAIN,
)
from .route import DiveraRouteCoordinator


def _get_server_hash(base_url: str) -> str:
    """Server-Hash erzeugen."""
    import hashlib

    return hashlib.sha1(
        base_url.encode("utf-8")
    ).hexdigest()[:8]


def _device_info(
    entry: ConfigEntry,
) -> DeviceInfo:
    """Geräteinformationen erzeugen."""
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

    server_hash = _get_server_hash(base_url)

    return DeviceInfo(
        identifiers={
            (
                DOMAIN,
                f"{server_hash}_{ucr_id}",
            )
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
    """Routing-Sensoren einrichten."""
    coordinator: DiveraRouteCoordinator = (
        hass.data[f"{DOMAIN}_route"][
            entry.entry_id
        ]
    )

    async_add_entities(
        [
            DiveraRouteDistanceSensor(
                coordinator,
                entry,
            ),
            DiveraRouteDurationSensor(
                coordinator,
                entry,
            ),
            DiveraRouteStatusSensor(
                coordinator,
                entry,
            ),
        ]
    )


class DiveraRouteDistanceSensor(
    CoordinatorEntity[DiveraRouteCoordinator],
    SensorEntity,
):
    """Entfernung Feuerwache zum Einsatzort."""

    _attr_native_unit_of_measurement = "km"
    _attr_icon = "mdi:map-marker-distance"

    def __init__(
        self,
        coordinator: DiveraRouteCoordinator,
        entry: ConfigEntry,
    ) -> None:
        super().__init__(coordinator)

        ucr_name = entry.data.get(
            CONF_UCR_NAME,
            "DIVERA",
        )

        base_url = entry.data.get(
            CONF_BASE_URL,
            "",
        )

        ucr_id = entry.data.get(
            CONF_UCR_ID,
            entry.entry_id,
        )

        server_hash = _get_server_hash(base_url)

        self._attr_name = (
            f"DIVERA Routendistanz {ucr_name}"
        )

        self._attr_unique_id = (
            f"divera_route_distance_"
            f"{server_hash}_{ucr_id}"
        )

        self._attr_device_info = _device_info(
            entry
        )

    @property
    def native_value(self) -> float | None:
        """Entfernung in km."""
        data = self.coordinator.data

        if not data:
            return None

        distance_m = data.get("distance_m")

        if distance_m is None:
            return None

        return round(
            float(distance_m) / 1000,
            1,
        )


class DiveraRouteDurationSensor(
    CoordinatorEntity[DiveraRouteCoordinator],
    SensorEntity,
):
    """Fahrzeit Feuerwache zum Einsatzort."""

    _attr_native_unit_of_measurement = "min"
    _attr_icon = "mdi:clock-outline"

    def __init__(
        self,
        coordinator: DiveraRouteCoordinator,
        entry: ConfigEntry,
    ) -> None:
        super().__init__(coordinator)

        ucr_name = entry.data.get(
            CONF_UCR_NAME,
            "DIVERA",
        )

        base_url = entry.data.get(
            CONF_BASE_URL,
            "",
        )

        ucr_id = entry.data.get(
            CONF_UCR_ID,
            entry.entry_id,
        )

        server_hash = _get_server_hash(base_url)

        self._attr_name = (
            f"DIVERA Fahrzeit {ucr_name}"
        )

        self._attr_unique_id = (
            f"divera_route_duration_"
            f"{server_hash}_{ucr_id}"
        )

        self._attr_device_info = _device_info(
            entry
        )

    @property
    def native_value(self) -> float | None:
        """Fahrzeit in Minuten."""
        data = self.coordinator.data

        if not data:
            return None

        duration_s = data.get("duration_s")

        if duration_s is None:
            return None

        return round(
            float(duration_s) / 60,
            1,
        )


class DiveraRouteStatusSensor(
    CoordinatorEntity[DiveraRouteCoordinator],
    SensorEntity,
):
    """Status der DIVERA Route."""

    _attr_icon = "mdi:map-marker-path"

    def __init__(
        self,
        coordinator: DiveraRouteCoordinator,
        entry: ConfigEntry,
    ) -> None:
        super().__init__(coordinator)

        ucr_name = entry.data.get(
            CONF_UCR_NAME,
            "DIVERA",
        )

        base_url = entry.data.get(
            CONF_BASE_URL,
            "",
        )

        ucr_id = entry.data.get(
            CONF_UCR_ID,
            entry.entry_id,
        )

        server_hash = _get_server_hash(base_url)

        self._attr_name = (
            f"DIVERA Routenstatus {ucr_name}"
        )

        self._attr_unique_id = (
            f"divera_route_status_"
            f"{server_hash}_{ucr_id}"
        )

        self._attr_device_info = _device_info(
            entry
        )

    @property
    def native_value(self) -> str:
        """Routenstatus."""
        data = self.coordinator.data

        if not data:
            return "Kein aktiver Einsatz"

        return "Route verfügbar"

    @property
    def extra_state_attributes(self) -> dict:
        """Routeninformationen."""
        data = self.coordinator.data

        if not data:
            return {}

        return {
            "einsatz_id": data.get(
                "incident_id"
            ),
            "einsatz_latitude": data.get(
                "incident_latitude"
            ),
            "einsatz_longitude": data.get(
                "incident_longitude"
            ),
            "distance_m": data.get(
                "distance_m"
            ),
            "duration_s": data.get(
                "duration_s"
            ),
            "geometry": data.get(
                "geometry"
            ),
        }
