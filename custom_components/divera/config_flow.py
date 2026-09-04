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
    CONF_UCR_ID,
    CONF_UCR_NAME,
    DEFAULT_BASE_URL,
    DOMAIN,
)


class DiveraConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for DIVERA 24/7."""

    VERSION = 3

    def __init__(self) -> None:
        self._base_url: str = DEFAULT_BASE_URL
        self._access_key: str = ""
        self._ucr_options: dict[str, str] = {}

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
                ucr_options, error = await self._fetch_ucr(
                    base_url,
                    access_key,
                )

                if error:
                    errors["base"] = error
                else:
                    self._base_url = base_url
                    self._access_key = access_key
                    self._ucr_options = ucr_options
                    return await self.async_step_select_ucr()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_BASE_URL,
                        default=self._base_url,
                    ): str,
                    vol.Required(CONF_ACCESS_KEY): str,
                }
            ),
            errors=errors,
        )

    async def async_step_select_ucr(self, user_input=None) -> FlowResult:
        """Step 2: let the user pick a unit (UCR)."""
        errors: dict[str, str] = {}

        if user_input is not None:
            ucr_id = user_input[CONF_UCR_ID]
            ucr_name = self._ucr_options.get(ucr_id, ucr_id)

            unique_id = f"{self._base_url}|{ucr_id}"
            await self.async_set_unique_id(unique_id)
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title=f"DIVERA – {ucr_name}",
                data={
                    CONF_BASE_URL: self._base_url,
                    CONF_ACCESS_KEY: self._access_key,
                    CONF_UCR_ID: ucr_id,
                    CONF_UCR_NAME: ucr_name,
                },
            )

        if not self._ucr_options:
            return self.async_abort(reason="no_units")

        ucr_selector = SelectSelector(
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
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_UCR_ID): ucr_selector,
                }
            ),
            errors=errors,
        )

    async def _fetch_ucr(
        self,
        base_url: str,
        access_key: str,
    ) -> tuple[dict[str, str], str | None]:
        """Validate Access Key and return available UCR units."""

        jwt_url = f"{base_url}/api/v2/auth/jwt"
        pull_url = f"{base_url}/api/v2/pull/all"

        # Step 1: Get JWT – this also validates the Access Key.
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    jwt_url,
                    params={"accesskey": access_key},
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as resp:
                    if resp.status == 401:
                        return {}, "invalid_auth"

                    if resp.status != 200:
                        return {}, "cannot_connect"

        except (aiohttp.ClientError, TimeoutError):
            return {}, "cannot_connect"

        # Step 2: Get available units using pull/all.
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    pull_url,
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

        ucr_raw = payload.get("data", {}).get("ucr", {})

        if not isinstance(ucr_raw, dict) or not ucr_raw:
            return {"0": "Standard"}, None

        options: dict[str, str] = {}

        for ucr_id, ucr_data in ucr_raw.items():
            if isinstance(ucr_data, dict):
                name = (
                    ucr_data.get("name")
                    or ucr_data.get("shortname")
                    or str(ucr_id)
                )
            else:
                name = str(ucr_id)

            options[str(ucr_id)] = name

        return options, None

    @staticmethod
    def _valid_base_url(base_url: str) -> bool:
        """Check whether the configured server URL is valid."""
        try:
            parsed = urlparse(base_url)
        except ValueError:
            return False

        return parsed.scheme in ("http", "https") and bool(parsed.netloc)
