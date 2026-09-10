"""Config flow for DIVERA 24/7."""
from __future__ import annotations

from urllib.parse import urlparse

import aiohttp
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.selector import (
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)

from .const import (
    CONF_ACCESS_KEY,
    CONF_BASE_URL,
    CONF_STATION_ADDRESS,
    CONF_STATION_LATITUDE,
    CONF_STATION_LONGITUDE,
    CONF_UCR_ID,
    CONF_UCR_NAME,
    DEFAULT_BASE_URL,
    DOMAIN,
    GEOCODING_URL,
)


class DiveraConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for DIVERA 24/7."""

    VERSION = 2

    def __init__(self) -> None:
        self._base_url = DEFAULT_BASE_URL
        self._access_key = ""
        self._ucr_options: dict[str, str] = {}
        self._ucr_id = ""
        self._ucr_name = ""
        self._reconfigure_entry: config_entries.ConfigEntry | None = None

    async def async_step_user(self, user_input=None) -> FlowResult:
        """Step 1: collect server URL and access key."""
        errors: dict[str, str] = {}
        if user_input is not None:
            base_url = user_input[CONF_BASE_URL].strip().rstrip("/")
            access_key = user_input[CONF_ACCESS_KEY].strip()
            if not self._valid_base_url(base_url):
                errors[CONF_BASE_URL] = "invalid_url"
            elif not access_key:
                errors[CONF_ACCESS_KEY] = "invalid_auth"
            else:
                options, error = await self._fetch_ucr(base_url, access_key)
                if error:
                    errors["base"] = error
                else:
                    self._base_url = base_url
                    self._access_key = access_key
                    self._ucr_options = options
                    return await self.async_step_select_ucr()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_BASE_URL, default=self._base_url): str,
                    vol.Required(CONF_ACCESS_KEY): str,
                }
            ),
            errors=errors,
        )

    async def async_step_select_ucr(self, user_input=None) -> FlowResult:
        """Step 2: select the DIVERA unit."""
        if user_input is not None:
            self._ucr_id = str(user_input[CONF_UCR_ID])
            self._ucr_name = self._ucr_options.get(self._ucr_id, self._ucr_id)
            return await self.async_step_station()

        if not self._ucr_options:
            return self.async_abort(reason="no_units")

        selector = SelectSelector(
            SelectSelectorConfig(
                options=[
                    {"value": uid, "label": name}
                    for uid, name in self._ucr_options.items()
                ],
                mode=SelectSelectorMode.LIST,
            )
        )
        return self.async_show_form(
            step_id="select_ucr",
            data_schema=vol.Schema({vol.Required(CONF_UCR_ID): selector}),
        )

    async def async_step_station(self, user_input=None) -> FlowResult:
        """Step 3: configure and geocode the station address."""
        errors: dict[str, str] = {}
        if user_input is not None:
            address = user_input[CONF_STATION_ADDRESS].strip()
            if not address:
                errors[CONF_STATION_ADDRESS] = "invalid_station"
            else:
                coords = await self._geocode(address)
                if coords is None:
                    errors[CONF_STATION_ADDRESS] = "station_not_found"
                else:
                    data = {
                        CONF_BASE_URL: self._base_url,
                        CONF_ACCESS_KEY: self._access_key,
                        CONF_UCR_ID: self._ucr_id,
                        CONF_UCR_NAME: self._ucr_name,
                        CONF_STATION_ADDRESS: address,
                        CONF_STATION_LATITUDE: coords[0],
                        CONF_STATION_LONGITUDE: coords[1],
                    }
                    unique_id = f"{self._base_url}|{self._ucr_id}"
                    await self.async_set_unique_id(unique_id)
                    self._abort_if_unique_id_configured()
                    return self.async_create_entry(
                        title=f"DIVERA – {self._ucr_name}", data=data
                    )

        return self.async_show_form(
            step_id="station",
            data_schema=vol.Schema({vol.Required(CONF_STATION_ADDRESS): str}),
            errors=errors,
        )

    async def async_step_reconfigure(self, user_input=None) -> FlowResult:
        """Allow existing installations to add/change the station."""
        entry_id = self.context.get("entry_id")
        if entry_id:
            self._reconfigure_entry = self.hass.config_entries.async_get_entry(entry_id)
        entry = self._reconfigure_entry
        if entry is None:
            return self.async_abort(reason="cannot_connect")

        errors: dict[str, str] = {}
        if user_input is not None:
            address = user_input[CONF_STATION_ADDRESS].strip()
            old_address = entry.data.get(CONF_STATION_ADDRESS, "")
            if address == old_address and entry.data.get(CONF_STATION_LATITUDE) is not None:
                lat = entry.data[CONF_STATION_LATITUDE]
                lng = entry.data[CONF_STATION_LONGITUDE]
            else:
                coords = await self._geocode(address)
                if coords is None:
                    errors[CONF_STATION_ADDRESS] = "station_not_found"
                    coords = None
                if coords is None:
                    return self.async_show_form(
                        step_id="reconfigure",
                        data_schema=vol.Schema(
                            {vol.Required(CONF_STATION_ADDRESS, default=address): str}
                        ),
                        errors=errors,
                    )
                lat, lng = coords

            self.hass.config_entries.async_update_entry(
                entry,
                data={
                    **entry.data,
                    CONF_STATION_ADDRESS: address,
                    CONF_STATION_LATITUDE: lat,
                    CONF_STATION_LONGITUDE: lng,
                },
            )
            return self.async_abort(reason="reconfigure_successful")

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_STATION_ADDRESS,
                        default=entry.data.get(CONF_STATION_ADDRESS, ""),
                    ): str
                }
            ),
            errors=errors,
        )

    async def _fetch_ucr(self, base_url: str, access_key: str):
        """Validate the access key and load units."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{base_url}/api/v2/auth/jwt",
                    params={"accesskey": access_key},
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as resp:
                    if resp.status == 401:
                        return {}, "invalid_auth"
                    if resp.status != 200:
                        return {}, "cannot_connect"

                async with session.get(
                    f"{base_url}/api/v2/pull/all",
                    params={"accesskey": access_key},
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as resp:
                    if resp.status == 401:
                        return {}, "invalid_auth"
                    if resp.status != 200:
                        return {}, "cannot_connect"
                    payload = await resp.json()
        except (aiohttp.ClientError, TimeoutError):
            return {}, "cannot_connect"

        raw = payload.get("data", {}).get("ucr", {})
        if not isinstance(raw, dict) or not raw:
            return {"0": "Standard"}, None

        options = {}
        for uid, data in raw.items():
            if isinstance(data, dict):
                name = data.get("name") or data.get("shortname") or str(uid)
            else:
                name = str(uid)
            options[str(uid)] = str(name)
        return options, None

    async def _geocode(self, address: str) -> tuple[float, float] | None:
        """Resolve the station address once during configuration."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    GEOCODING_URL,
                    params={"q": address, "format": "jsonv2", "limit": 1},
                    headers={
                        "User-Agent": "DIVERA-Home-Assistant-Integration/1.1"
                    },
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as resp:
                    if resp.status != 200:
                        return None
                    result = await resp.json()
        except (aiohttp.ClientError, TimeoutError, ValueError):
            return None

        if not result:
            return None
        try:
            return float(result[0]["lat"]), float(result[0]["lon"])
        except (KeyError, TypeError, ValueError):
            return None

    @staticmethod
    def _valid_base_url(base_url: str) -> bool:
        try:
            parsed = urlparse(base_url)
        except ValueError:
            return False
        return parsed.scheme in ("http", "https") and bool(parsed.netloc)
