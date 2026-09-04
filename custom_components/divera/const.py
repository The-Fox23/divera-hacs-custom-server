DOMAIN = "divera"

CONF_BASE_URL = "base_url"
CONF_ACCESS_KEY = "access_key"
CONF_UCR_ID = "ucr_id"
CONF_UCR_NAME = "ucr_name"

# Standard-URL für den offiziellen DIVERA-Server.
# Bei einem eigenen DIVERA Server kann diese URL bei der Einrichtung geändert werden.
DEFAULT_BASE_URL = "https://app.divera247.com"

# Fallback-Polling-Intervall (Sekunden) falls WS-Verbindung unterbrochen ist
FALLBACK_POLL_INTERVAL = 60

# Wartezeit (Sekunden) vor erstem Verbindungsversuch nach Fehler
WS_RECONNECT_DELAY = 10

# Maximale Wartezeit (Sekunden) beim exponentiellen Backoff
WS_MAX_RECONNECT_DELAY = 300
