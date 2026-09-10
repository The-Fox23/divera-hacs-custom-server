"""Routing support for DIVERA 24/7."""
from __future__ import annotations

import logging
from typing import Any

import aiohttp
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    CONF_STATION_LATITUDE,
    CONF_STATION_LONGITUDE,
    ROUTE_TIMEOUT,
    ROUTING_PROFILE,
    ROUTING_URL,
)
from .coordinator import DiveraCoordinator

_LOGGER = logging.getLogger(__name__)


def _number(value: Any) -> float | None:
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _active_alarm(data: dict | None) -> dict | None:
    if not isinstance(data, dict):
        return None
    if data.get("closed") is True:
        return None
    lat = _number(data.get("lat"))
    lng = _number(data.get("lng"))
    if lat is None or lng is None:
        return None
    if not (-90 <= lat <= 90 and -180 <= lng <= 180):
        return None
    return data


class DiveraRouteCoordinator(DataUpdateCoordinator[dict | None]):
    """Calculates and caches the route from the station to the incident."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        coordinator: DiveraCoordinator,
    ) -> None:
        self.station_lat = _number(entry.data.get(CONF_STATION_LATITUDE))
        self.station_lng = _number(entry.data.get(CONF_STATION_LONGITUDE))
        self._divera_coordinator = coordinator
        self._last_key: tuple[float, float] | None = None
        self._cached_route: dict | None = None
        super().__init__(
            hass,
            _LOGGER,
            name="divera_route",
            update_interval=None,
        )
        coordinator.async_add_listener(self._alarm_changed)

    async def async_close(self) -> None:
        self._divera_coordinator.async_remove_listener(self._alarm_changed)

    def _alarm_changed(self) -> None:
        self.hass.async_create_task(self.async_request_refresh())

    async def _async_update_data(self) -> dict | None:
        alarm = _active_alarm(self._divera_coordinator.data)
        if alarm is None or self.station_lat is None or self.station_lng is None:
            self._last_key = None
            self._cached_route = None
            return None

        dest_lat = _number(alarm.get("lat"))
        dest_lng = _number(alarm.get("lng"))
        if dest_lat is None or dest_lng is None:
            return None

        key = (round(dest_lat, 5), round(dest_lng, 5))
        if key == self._last_key and self._cached_route is not None:
            return self._cached_route

        url = (
            f"{ROUTING_URL}/route/v1/{ROUTING_PROFILE}/"
            f"{self.station_lng},{self.station_lat};{dest_lng},{dest_lat}"
        )
        params = {
            "overview": "full",
            "geometries": "geojson",
            "steps": "false",
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url,
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=ROUTE_TIMEOUT),
                    headers={"User-Agent": "DIVERA-Home-Assistant-Integration"},
                ) as response:
                    if response.status != 200:
                        raise UpdateFailed(
                            f"Routing-Server HTTP {response.status}"
                        )
                    payload = await response.json()
        except (aiohttp.ClientError, TimeoutError) as err:
            raise UpdateFailed(f"Routing-Anfrage fehlgeschlagen: {err}") from err

        routes = payload.get("routes") or []
        if not routes:
            raise UpdateFailed("Routing-Server hat keine Route geliefert")

        route = routes[0]
        geometry = route.get("geometry", {}).get("coordinates", [])
        result = {
            "distance_m": float(route.get("distance", 0)),
            "duration_s": float(route.get("duration", 0)),
            "geometry": geometry,
            "incident_id": alarm.get("id"),
            "incident_latitude": dest_lat,
            "incident_longitude": dest_lng,
        }
        self._last_key = key
        self._cached_route = result
        _LOGGER.debug(
            "DIVERA Route berechnet: %.0f m / %.0f s",
            result["distance_m"],
            result["duration_s"],
        )
        return result
