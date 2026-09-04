"""DIVERA 24/7 – WebSocket-getriebener DataUpdateCoordinator."""
from __future__ import annotations

import asyncio
import logging
from datetime import timedelta
from urllib.parse import urlparse

import aiohttp
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    CONF_ACCESS_KEY,
    CONF_BASE_URL,
    CONF_UCR_ID,
    DOMAIN,
    FALLBACK_POLL_INTERVAL,
    WS_MAX_RECONNECT_DELAY,
    WS_RECONNECT_DELAY,
)

_LOGGER = logging.getLogger(__name__)


class DiveraCoordinator(DataUpdateCoordinator):
    """Koordiniert DIVERA-Daten per WebSocket (Push-to-Pull).

    Ablauf:
      1. Beim Setup: JWT holen, initiale Daten per REST laden.
      2. WebSocket-Schleife starten.
      3. Bei 'cluster-pull': REST-Daten neu laden.
      4. Bei 'jwtExpired': neuen JWT holen und neu authentifizieren.
      5. Fallback: Falls WS-Verbindung weg ist, wird per REST gepollt.
    """

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.base_url: str = entry.data[CONF_BASE_URL].rstrip("/")
        self.access_key: str = entry.data[CONF_ACCESS_KEY]
        self.ucr_id: str | None = entry.data.get(CONF_UCR_ID)

        self._jwt: str | None = None
        self._ws_task: asyncio.Task | None = None
        self._ws_connected: bool = False

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=FALLBACK_POLL_INTERVAL),
        )

    # ------------------------------------------------------------------
    # URLs
    # ------------------------------------------------------------------

    @property
    def jwt_url(self) -> str:
        """URL für den JWT-Endpunkt."""
        return f"{self.base_url}/api/v2/auth/jwt"

    @property
    def pull_url(self) -> str:
        """URL für den Pull-Endpunkt."""
        return f"{self.base_url}/api/v2/pull/all"

    @property
    def ws_url(self) -> str:
        """WebSocket-URL aus der konfigurierten Server-URL erzeugen."""
        parsed = urlparse(self.base_url)

        if parsed.scheme == "https":
            ws_scheme = "wss"
        elif parsed.scheme == "http":
            ws_scheme = "ws"
        else:
            raise UpdateFailed(
                f"Ungültiges URL-Schema für DIVERA Server: {parsed.scheme}"
            )

        path = parsed.path.rstrip("/")

        return f"{ws_scheme}://{parsed.netloc}{path}/ws"

    # ------------------------------------------------------------------
    # Fallback-Polling Steuerung
    # ------------------------------------------------------------------

    def _set_ws_connected(self, connected: bool) -> None:
        """WebSocket-Status setzen und Fallback-Polling steuern."""
        if connected == self._ws_connected:
            return

        self._ws_connected = connected

        if connected:
            _LOGGER.info(
                "DIVERA: WebSocket aktiv – Fallback-Polling deaktiviert"
            )
            self.update_interval = None

            if self._unsub_refresh:
                self._unsub_refresh()
                self._unsub_refresh = None

        else:
            _LOGGER.warning(
                "DIVERA: WebSocket nicht verfügbar – "
                "Fallback-Polling (%ds)",
                FALLBACK_POLL_INTERVAL,
            )

            self.update_interval = timedelta(
                seconds=FALLBACK_POLL_INTERVAL
            )

            self._schedule_refresh()

    # ------------------------------------------------------------------
    # JWT
    # ------------------------------------------------------------------

    async def async_fetch_jwt(self) -> str:
        """JWT vom konfigurierten DIVERA-Server holen."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    self.jwt_url,
                    params={"accesskey": self.access_key},
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as resp:
                    if resp.status == 401:
                        raise ConfigEntryAuthFailed(
                            "Ungültiger Access Key"
                        )

                    if resp.status != 200:
                        raise UpdateFailed(
                            f"JWT-Abruf fehlgeschlagen: HTTP {resp.status}"
                        )

                    payload = await resp.json()

        except ConfigEntryAuthFailed:
            raise

        except (aiohttp.ClientError, TimeoutError) as err:
            raise UpdateFailed(
                f"Verbindungsfehler beim JWT-Abruf: {err}"
            ) from err

        data = payload.get("data", {})

        # Je nach DIVERA-Version kann das Feld jwt oder jwt_ws heißen.
        jwt = data.get("jwt_ws") or data.get("jwt")

        if not jwt:
            raise UpdateFailed(
                "Kein JWT in der Server-Antwort gefunden"
            )

        self._jwt = jwt

        return jwt

    # ------------------------------------------------------------------
    # REST-Datenabruf
    # ------------------------------------------------------------------

    async def _async_update_data(self):
        """Aktuelle Alarmdaten per REST laden."""
        params = {"accesskey": self.access_key}

        if self.ucr_id:
            params["ucr"] = self.ucr_id

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    self.pull_url,
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as resp:
                    if resp.status == 401:
                        raise ConfigEntryAuthFailed(
                            "Ungültiger Access Key"
                        )

                    if resp.status != 200:
                        raise UpdateFailed(
                            f"API-Fehler: HTTP {resp.status}"
                        )

                    payload = await resp.json()

        except ConfigEntryAuthFailed:
            raise

        except (aiohttp.ClientError, TimeoutError) as err:
            raise UpdateFailed(
                f"Verbindungsfehler: {err}"
            ) from err

        return self._extract_alarm(payload)

    def _extract_alarm(self, payload: dict):
        """Neuesten aktiven Alarm aus der API-Antwort extrahieren."""
        items = payload.get(
            "data", {}
        ).get(
            "alarm", {}
        ).get(
            "items", []
        )

        # items kann [] oder ein Dictionary sein.
        if not items or not isinstance(items, dict):
            return None

        alarms = list(items.values())

        _LOGGER.debug(
            "DIVERA: %d Alarm(e) gefunden",
            len(alarms),
        )

        return max(
            alarms,
            key=lambda alarm: alarm.get("id", 0),
        )

    # ------------------------------------------------------------------
    # WebSocket
    # ------------------------------------------------------------------

    async def async_start_websocket(self) -> None:
        """WebSocket-Schleife als Background-Task starten."""
        self._ws_task = self.hass.async_create_background_task(
            self._ws_loop(),
            name="divera_websocket",
        )

    def async_stop_websocket(self) -> None:
        """WebSocket-Task beim Entladen der Integration beenden."""
        if self._ws_task and not self._ws_task.done():
            self._ws_task.cancel()
            self._ws_task = None

    async def _ws_loop(self) -> None:
        """WebSocket verbinden und bei Fehler automatisch neu verbinden."""
        delay = WS_RECONNECT_DELAY

        while True:
            try:
                await self._ws_run_once()

                self._set_ws_connected(False)
                delay = WS_RECONNECT_DELAY

            except asyncio.CancelledError:
                _LOGGER.debug(
                    "DIVERA WebSocket-Task wurde beendet"
                )

                self._set_ws_connected(False)
                return

            except ConfigEntryAuthFailed:
                _LOGGER.error(
                    "DIVERA: Ungültiger Access Key – "
                    "WebSocket wird nicht neu verbunden"
                )

                self._set_ws_connected(False)
                return

            except Exception as err:  # noqa: BLE001
                self._set_ws_connected(False)

                _LOGGER.warning(
                    "DIVERA: WebSocket-Verbindung unterbrochen – "
                    "Grund: %s (%s). Neuer Versuch in %s Sekunden.",
                    err,
                    type(err).__name__,
                    delay,
                )

                await asyncio.sleep(delay)

                delay = min(
                    delay * 2,
                    WS_MAX_RECONNECT_DELAY,
                )

                continue

            await asyncio.sleep(WS_RECONNECT_DELAY)

    async def _ws_run_once(self) -> None:
        """Eine WebSocket-Sitzung aufbauen und Events verarbeiten."""
        jwt = await self.async_fetch_jwt()

        _LOGGER.debug(
            "DIVERA: JWT erfolgreich geholt, "
            "verbinde WebSocket: %s",
            self.ws_url,
        )

        async with aiohttp.ClientSession() as session:
            async with session.ws_connect(
                self.ws_url,
                heartbeat=25,
                timeout=aiohttp.ClientTimeout(
                    total=None,
                    connect=15,
                ),
            ) as ws:

                auth_payload: dict = {
                    "jwt": jwt,
                }

                if self.ucr_id:
                    auth_payload["ucr"] = int(self.ucr_id)

                await ws.send_json(
                    {
                        "type": "authenticate",
                        "payload": auth_payload,
                    }
                )

                _LOGGER.debug(
                    "DIVERA: authenticate gesendet"
                )

                async for msg in ws:
                    if msg.type == aiohttp.WSMsgType.TEXT:
                        await self._handle_ws_message(
                            msg.data,
                            ws,
                        )

                    elif msg.type == aiohttp.WSMsgType.ERROR:
                        raise UpdateFailed(
                            f"WebSocket-Fehler: {ws.exception()}"
                        )

                    elif msg.type in (
                        aiohttp.WSMsgType.CLOSE,
                        aiohttp.WSMsgType.CLOSING,
                        aiohttp.WSMsgType.CLOSED,
                    ):
                        close_code = msg.data
                        close_reason = (
                            msg.extra
                            or "kein Grund angegeben"
                        )

                        _LOGGER.warning(
                            "DIVERA: WebSocket-Verbindung getrennt – "
                            "Code: %s, Grund: %s",
                            close_code,
                            close_reason,
                        )

                        return

    async def _handle_ws_message(
        self,
        raw: str,
        ws: aiohttp.ClientWebSocketResponse,
    ) -> None:
        """Eingehende WebSocket-Nachricht verarbeiten."""
        try:
            import json

            data = json.loads(raw)

        except ValueError:
            _LOGGER.debug(
                "DIVERA: Nicht-JSON-Nachricht empfangen: %s",
                raw,
            )
            return

        msg_type = data.get("type", "")

        if msg_type == "init":
            _LOGGER.info(
                "DIVERA: WebSocket erfolgreich authentifiziert"
            )

            self._set_ws_connected(True)

        elif msg_type == "jwtExpired":
            _LOGGER.info(
                "DIVERA: JWT abgelaufen – "
                "hole neuen JWT und authentifiziere neu"
            )

            try:
                new_jwt = await self.async_fetch_jwt()

                auth_payload: dict = {
                    "jwt": new_jwt,
                }

                if self.ucr_id:
                    auth_payload["ucr"] = int(self.ucr_id)

                await ws.send_json(
                    {
                        "type": "authenticate",
                        "payload": auth_payload,
                    }
                )

            except Exception as err:  # noqa: BLE001
                _LOGGER.error(
                    "DIVERA: JWT-Erneuerung fehlgeschlagen: %s",
                    err,
                )

                raise

        elif msg_type == "cluster-pull":
            _LOGGER.debug(
                "DIVERA: cluster-pull empfangen – "
                "lade neue Alarmdaten"
            )

            await self.async_refresh()

        elif msg_type == "cluster-vehicle":
            _LOGGER.debug(
                "DIVERA: Fahrzeugstatus-Update: %s",
                data.get("payload"),
            )

        elif msg_type == "user-status":
            _LOGGER.debug(
                "DIVERA: Nutzerstatus-Update: %s",
                data.get("payload"),
            )

        else:
            _LOGGER.debug(
                "DIVERA: Unbekanntes WS-Event '%s': %s",
                msg_type,
                data,
            )
