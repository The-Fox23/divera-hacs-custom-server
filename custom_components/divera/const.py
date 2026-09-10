DOMAIN = "divera"

CONF_BASE_URL = "base_url"
CONF_ACCESS_KEY = "access_key"
CONF_UCR_ID = "ucr_id"
CONF_UCR_NAME = "ucr_name"
CONF_STATION_ADDRESS = "station_address"
CONF_STATION_LATITUDE = "station_latitude"
CONF_STATION_LONGITUDE = "station_longitude"

DEFAULT_BASE_URL = "https://app.divera247.com"

# DIVERA-Fallback, falls die WebSocket-Verbindung ausfällt.
FALLBACK_POLL_INTERVAL = 60
WS_RECONNECT_DELAY = 10
WS_MAX_RECONNECT_DELAY = 300

# Routing / Geocoding
GEOCODING_URL = "https://nominatim.openstreetmap.org/search"
ROUTING_URL = "https://router.project-osrm.org"
ROUTING_PROFILE = "driving"
ROUTE_TIMEOUT = 15
