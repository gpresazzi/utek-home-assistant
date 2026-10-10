"""Constants for Air Touch VMC."""

DOMAIN = "air_touch"
CONF_UNIT_ID = "unit_id"
CONF_ENABLE_WRITES = "enable_writes"
CONF_POLL_INTERVAL = "poll_interval"
DEFAULT_PORT = 502
DEFAULT_UNIT_ID = 1
DEFAULT_POLL_INTERVAL = 30
# App register IDs are ONE based; the transport subtracts one.
READ_BLOCKS = ((20, 1), (51, 6), (81, 20))
