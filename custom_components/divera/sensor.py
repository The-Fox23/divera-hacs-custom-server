"""DIVERA 24/7 sensor entity."""
from __future__ import annotations

from datetime import datetime, timezone

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_UCR_ID, CONF_UCR_NAME, DOMAIN
from .coordinator import DiveraCoordinator

NO_ALARM_STATE = "Kein aktiver Einsatz"


def _fmt_ts(unix: int | None) -> str | None:
    if unix is None:
        return None
    try:
        return datetime.fromtimestamp(unix, tz=timezone.utc).isoformat()
    except (TypeError, ValueError, OSError):
        return str(unix)


def _resolve_groups(group_ids: list | None, group_map: dict) -> str | None:
    """Gruppen-IDs anhand der Cluster-Gruppen-Zuordnung in Namen auflösen."""
    if not group_ids:
        return None
    names = [group_map.get(str(gid), {}).get("name", str(gid)) for gid in group_ids]
    return ", ".join(names)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: DiveraCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([DiveraSensor(coordinator, entry)])


class DiveraSensor(CoordinatorEntity[DiveraCoordinator], SensorEntity):

    def __init__(self, coordinator: DiveraCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        ucr_name: str = entry.data.get(CONF_UCR_NAME, "DIVERA")
        ucr_id: str = entry.data.get(CONF_UCR_ID, entry.entry_id)

        self._attr_name = f"DIVERA {ucr_name}"
        self._attr_unique_id = f"divera_{ucr_id}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, ucr_id)},
            name=f"DIVERA 24/7 – {ucr_name}",
            manufacturer="DIVERA GmbH",
            model="DIVERA 24/7",
        )

    @property
    def native_value(self) -> str:
        alarm = (self.coordinator.data or {}).get("alarm")
        if alarm is None:
            return NO_ALARM_STATE
        return alarm.get("title") or NO_ALARM_STATE

    @property
    def extra_state_attributes(self) -> dict:
        data = self.coordinator.data or {}
        alarm = data.get("alarm")
        if alarm is None:
            return {}
        groups = data.get("groups", {})

        # Gesamten API-Response als Attribute, bekannte Felder mit deutschen Namen
        attrs: dict = {}

        # Bekannte Felder → deutsche Namen
        attrs["stichwort"]    = alarm.get("title")
        attrs["beschreibung"] = alarm.get("text")
        attrs["adresse"]      = alarm.get("address")
        attrs["einsatz_id"]   = alarm.get("id")
        attrs["prioritaet"]   = alarm.get("priority")
        attrs["geschlossen"]  = alarm.get("closed")
        attrs["alarmiert_am"] = _fmt_ts(alarm.get("date"))
        attrs["latitude"]     = alarm.get("lat")
        attrs["longitude"]    = alarm.get("lng")
        attrs["fahrzeuge"]    = alarm.get("vehicles")
        attrs["group"]        = _resolve_groups(alarm.get("group"), groups)

        # Alle restlichen API-Felder direkt übernehmen
        bekannte = {"title", "text", "address", "id", "priority", "closed", "date", "lat", "lng", "vehicles", "group"}
        for key, value in alarm.items():
            if key not in bekannte:
                attrs[key] = value

        # None entfernen
        return {k: v for k, v in attrs.items() if v is not None}
