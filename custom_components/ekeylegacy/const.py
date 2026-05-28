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
DEFAULT_RARE_AUTH_CMD = 1  # successful authentication
DEFAULT_RARE_FAIL_CMD = 19  # failed / unrecognised authentication
