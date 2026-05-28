"""Constants for the Ekey (legacy) integration."""

DOMAIN = "ekeylegacy"
EVENT_TYPE_NAME = f"{DOMAIN}_event"

CONF_DELIMITER = "delimiter"
CONF_DURATION = "duration"

DEFAULT_PORT = 56000
DEFAULT_DELIMITER = "_"
DEFAULT_DURATION = 2.0

TYPE_HOME = "home"
TYPE_MULTI = "multi"
TYPE_RARE = "rare"

CONF_RARE_AUTH_CMD = "rare_auth_cmd"
CONF_RARE_FAIL_CMD = "rare_fail_cmd"
DEFAULT_RARE_AUTH_CMD = 0x88  # 136 – open door with finger
DEFAULT_RARE_FAIL_CMD = 0x89  # 137 – wrong / unrecognised finger
