"""Constants for DIVERA 24/7."""
from __future__ import annotations

DOMAIN = "divera"

CONF_BASE_URL = "base_url"
CONF_ACCESS_KEY = "access_key"
CONF_UCR_ID = "ucr_id"
CONF_UCR_NAME = "ucr_name"

CONF_STATION_ADDRESS = "station_address"
CONF_STATION_LATITUDE = "station_latitude"
CONF_STATION_LONGITUDE = "station_longitude"

DEFAULT_BASE_URL = "https://app.divera247.com"

# Fallback-Polling
FALLBACK_POLL_INTERVAL = 60

# WebSocket
WS_RECONNECT_DELAY = 10
WS_MAX_RECONNECT_DELAY = 300

# Geocoding
GEOCODING_URL = "https://nominatim.openstreetmap.org/search"

# Routing
ROUTING_URL = "https://router.project-osrm.org"
ROUTING_PROFILE = "driving"
ROUTE_TIMEOUT = 15
