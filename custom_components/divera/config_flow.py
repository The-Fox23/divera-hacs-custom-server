"""Config flow for DIVERA 24/7."""
from __future__ import annotations

from urllib.parse import quote, urlparse

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


class DiveraConfigFlow(
    config_entries.ConfigFlow,
    domain=DOMAIN,
):
    """Handle a config flow for DIVERA 24/7."""

    VERSION = 2

    def __init__(self) -> None:
        self._base_url = DEFAULT_BASE_URL
        self._access_key = ""
        self._ucr_options: dict[str, str] = {}
        self._ucr_id = ""
        self._ucr_name = ""

    async def async_step_user(
        self,
        user_input=None,
    ) -> FlowResult:
        """Server URL und API-Schlüssel abfragen."""
        errors: dict[str, str] = {}

        if user_input is not None:
            base_url = (
                user_input[CONF_BASE_URL]
                .strip()
                .rstrip("/")
            )

            access_key = (
                user_input[CONF_ACCESS_KEY]
                .strip()
            )

            if not self._valid_base_url(
                base_url
            ):
                errors[CONF_BASE_URL] = (
                    "invalid_url"
                )

            elif not access_key:
                errors[CONF_ACCESS_KEY] = (
                    "invalid_auth"
                )

            else:
                (
                    ucr_options,
                    error,
                ) = await self._fetch_ucr(
                    base_url,
                    access_key,
                )

                if error:
                    errors["base"] = error

                else:
                    self._base_url = base_url
                    self._access_key = access_key
                    self._ucr_options = (
                        ucr_options
                    )

                    return await (
                        self.async_step_select_ucr()
                    )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_BASE_URL,
                        default=self._base_url,
                    ): str,
                    vol.Required(
                        CONF_ACCESS_KEY
                    ): str,
                }
            ),
            errors=errors,
        )

    async def async_step_select_ucr(
        self,
        user_input=None,
    ) -> FlowResult:
        """Einheit auswählen."""
        if user_input is not None:
            self._ucr_id = user_input[
                CONF_UCR_ID
            ]

            self._ucr_name = (
                self._ucr_options.get(
                    self._ucr_id,
                    self._ucr_id,
                )
            )

            unique_id = (
                f"{self._base_url}|"
                f"{self._ucr_id}"
            )

            await self.async_set_unique_id(
                unique_id
            )

            self._abort_if_unique_id_configured()

            return await self.async_step_station()

        if not self._ucr_options:
            return self.async_abort(
                reason="no_units"
            )

        ucr_selector = SelectSelector(
            SelectSelectorConfig(
                options=[
                    {
                        "value": uid,
                        "label": name,
                    }
                    for uid, name
                    in self._ucr_options.items()
                ],
                mode=SelectSelectorMode.LIST,
            )
        )

        return self.async_show_form(
            step_id="select_ucr",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_UCR_ID
                    ): ucr_selector,
                }
            ),
        )

    async def async_step_station(
        self,
        user_input=None,
    ) -> FlowResult:
        """Feuerwache konfigurieren."""
        errors: dict[str, str] = {}

        if user_input is not None:
            address = (
                user_input[
                    CONF_STATION_ADDRESS
                ]
                .strip()
            )

            if not address:
                errors[
                    CONF_STATION_ADDRESS
                ] = "invalid_station"

            else:
                coordinates = (
                    await self._geocode_address(
                        address
                    )
                )

                if coordinates is None:
                    errors[
                        CONF_STATION_ADDRESS
                    ] = "station_not_found"

                else:
                    latitude, longitude = (
                        coordinates
                    )

                    return self.async_create_entry(
                        title=(
                            f"DIVERA – "
                            f"{self._ucr_name}"
                        ),
                        data={
                            CONF_BASE_URL:
                                self._base_url,
                            CONF_ACCESS_KEY:
                                self._access_key,
                            CONF_UCR_ID:
                                self._ucr_id,
                            CONF_UCR_NAME:
                                self._ucr_name,
                            CONF_STATION_ADDRESS:
                                address,
                            CONF_STATION_LATITUDE:
                                latitude,
                            CONF_STATION_LONGITUDE:
                                longitude,
                        },
                    )

        return self.async_show_form(
            step_id="station",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_STATION_ADDRESS
                    ): str,
                }
            ),
            errors=errors,
        )

    async def async_step_reconfigure(
        self,
        user_input=None,
    ) -> FlowResult:
        """Feuerwache einer bestehenden Installation ändern."""
        entry = self._get_reconfigure_entry()

        if user_input is not None:
            address = (
                user_input[
                    CONF_STATION_ADDRESS
                ]
                .strip()
            )

            coordinates = (
                await self._geocode_address(
                    address
                )
            )

            if coordinates is None:
                return self.async_show_form(
                    step_id="reconfigure",
                    data_schema=vol.Schema(
                        {
                            vol.Required(
                                CONF_STATION_ADDRESS,
                                default=address,
                            ): str,
                        }
                    ),
                    errors={
                        CONF_STATION_ADDRESS:
                            "station_not_found"
                    },
                )

            latitude, longitude = coordinates

            return self.async_update_reload_and_abort(
                entry,
                data_updates={
                    CONF_STATION_ADDRESS:
                        address,
                    CONF_STATION_LATITUDE:
                        latitude,
                    CONF_STATION_LONGITUDE:
                        longitude,
                },
            )

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_STATION_ADDRESS,
                        default=entry.data.get(
                            CONF_STATION_ADDRESS,
                            "",
                        ),
                    ): str,
                }
            ),
        )

    async def _fetch_ucr(
        self,
        base_url: str,
        access_key: str,
    ) -> tuple[dict[str, str], str | None]:
        """Access Key prüfen und UCR-Einheiten laden."""
        jwt_url = (
            f"{base_url}/api/v2/auth/jwt"
        )

        pull_url = (
            f"{base_url}/api/v2/pull/all"
        )

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    jwt_url,
                    params={
                        "accesskey": access_key
                    },
                    timeout=aiohttp.ClientTimeout(
                        total=10
                    ),
                ) as resp:

                    if resp.status == 401:
                        return {}, "invalid_auth"

                    if resp.status != 200:
                        return {}, "cannot_connect"

        except (
            aiohttp.ClientError,
            TimeoutError,
        ):
            return {}, "cannot_connect"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    pull_url,
                    params={
                        "accesskey": access_key
                    },
                    timeout=aiohttp.ClientTimeout(
                        total=10
                    ),
                ) as resp:

                    if resp.status == 401:
                        return {}, "invalid_auth"

                    if resp.status != 200:
                        return {}, "cannot_connect"

                    payload = await resp.json()

        except (
            aiohttp.ClientError,
            TimeoutError,
        ):
            return {}, "cannot_connect"

        ucr_raw = (
            payload
            .get("data", {})
            .get("ucr", {})
        )

        if (
            not isinstance(
                ucr_raw,
                dict,
            )
            or not ucr_raw
        ):
            return {
                "0": "Standard"
            }, None

        options: dict[str, str] = {}

        for ucr_id, ucr_data in (
            ucr_raw.items()
        ):
            if isinstance(
                ucr_data,
                dict,
            ):
                name = (
                    ucr_data.get("name")
                    or ucr_data.get("shortname")
                    or str(ucr_id)
                )
            else:
                name = str(ucr_id)

            options[
                str(ucr_id)
            ] = name

        return options, None

    async def _geocode_address(
        self,
        address: str,
    ) -> tuple[float, float] | None:
        """Feuerwachen-Adresse einmalig geocodieren."""
        params = {
            "q": address,
            "format": "jsonv2",
            "limit": 1,
        }

        headers = {
            "User-Agent": (
                "DIVERA-Home-Assistant-Integration"
            )
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    GEOCODING_URL,
                    params=params,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(
                        total=15
                    ),
                ) as response:

                    if response.status != 200:
                        return None

                    results = await response.json()

        except (
            aiohttp.ClientError,
            TimeoutError,
        ):
            return None

        if not results:
            return None

        try:
            latitude = float(
                results[0]["lat"]
            )
            longitude = float(
                results[0]["lon"]
            )
        except (
            KeyError,
            TypeError,
            ValueError,
        ):
            return None

        return latitude, longitude

    @staticmethod
    def _valid_base_url(
        base_url: str,
    ) -> bool:
        """Server URL prüfen."""
        try:
            parsed = urlparse(
                base_url
            )
        except ValueError:
            return False

        return (
            parsed.scheme in (
                "http",
                "https",
            )
            and bool(parsed.netloc)
        )
