"""DIVERA 24/7 Home Assistant integration."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .coordinator import DiveraCoordinator
from .route import DiveraRouteCoordinator

PLATFORMS = ["sensor", "device_tracker"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up DIVERA and the independent routing coordinator."""
    coordinator = DiveraCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    route_coordinator = DiveraRouteCoordinator(hass, entry, coordinator)
    await route_coordinator.async_config_entry_first_refresh()
    hass.data.setdefault(f"{DOMAIN}_route", {})[entry.entry_id] = route_coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    await coordinator.async_start_websocket()
    return True


async def async_migrate_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Migrate older entries without station data to version 2."""
    if config_entry.version < 2:
        hass.config_entries.async_update_entry(
            config_entry,
            version=2,
        )
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload DIVERA and routing."""
    coordinator: DiveraCoordinator | None = hass.data.get(DOMAIN, {}).get(entry.entry_id)
    route_coordinator: DiveraRouteCoordinator | None = hass.data.get(
        f"{DOMAIN}_route", {}
    ).get(entry.entry_id)

    if coordinator:
        coordinator.async_stop_websocket()
    if route_coordinator:
        await route_coordinator.async_close()

    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
        hass.data.get(f"{DOMAIN}_route", {}).pop(entry.entry_id, None)
    return unload_ok
