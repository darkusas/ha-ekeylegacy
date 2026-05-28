"""Event entity for Ekey (legacy) integration."""

import asyncio
import logging

from homeassistant.components.event import EventDeviceClass, EventEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PORT, CONF_TYPE
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import CONF_DELIMITER, CONF_RARE_AUTH_CMD, CONF_RARE_FAIL_CMD, DEFAULT_RARE_AUTH_CMD, DEFAULT_RARE_FAIL_CMD, DOMAIN, EVENT_TYPE_NAME, TYPE_HOME, TYPE_MULTI, TYPE_RARE

_LOGGER = logging.getLogger(__name__)

RARE_PACKET_LENGTH = 72


class EkeyLegacyAuthEvent(EventEntity):
    """Representation of a Ekey (legacy) event entity."""

    _attr_device_class = EventDeviceClass.BUTTON
    _attr_event_types = ["authenticated", "failed"]
    _attr_has_entity_name = True

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize the Ekey (legacy) event entity."""
        port: int = config_entry.data[CONF_PORT]
        device_type: str = config_entry.data[CONF_TYPE]

        self._attr_name = None
        self._attr_suggested_object_id = f"ekey_{device_type}"
        self._attr_unique_id = f"{device_type}-{port}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{device_type}-{port}")},
            manufacturer="ekey",
            name=f"ekey {device_type}",
        )

        self._conf_port = port
        self._conf_type = device_type
        self._conf_delimiter = config_entry.data[CONF_DELIMITER]
        self._conf_rare_auth_cmd = config_entry.data.get(CONF_RARE_AUTH_CMD, DEFAULT_RARE_AUTH_CMD)
        self._conf_rare_fail_cmd = config_entry.data.get(CONF_RARE_FAIL_CMD, DEFAULT_RARE_FAIL_CMD)
        self._transport = None

    async def async_added_to_hass(self) -> None:
        """Register callbacks."""
        loop = asyncio.get_running_loop()
        self._transport, _ = await loop.create_datagram_endpoint(
            lambda: _EkeyUDPProtocol(self.hass, self),
            local_addr=("0.0.0.0", self._conf_port),
        )

    @callback
    def async_handle_event(self, message: bytes) -> None:
        """Handle the Ekey (legacy) event."""
        parsed_event = self._parse_event(message)
        if parsed_event is None:
            return

        event_type, event_data = parsed_event
        self._trigger_event(event_type, event_data)
        self.hass.bus.async_fire(
            EVENT_TYPE_NAME,
            {
                "event_type": event_type,
                **event_data,
            },
        )

        self.async_write_ha_state()

    def _parse_event(self, message: bytes) -> tuple[str, dict[str, str]] | None:
        """Parse an incoming event payload."""
        if self._conf_type == TYPE_RARE:
            return _parse_rare_message(message, self._conf_rare_auth_cmd, self._conf_rare_fail_cmd)

        text_message = message.decode("ascii", errors="ignore").strip()
        parts = text_message.split(self._conf_delimiter)

        _LOGGER.info("Received event '%s'", text_message)

        if self._conf_type == TYPE_HOME and len(parts) == 6:
            event_data = {
                "type": parts[0],
                "user": parts[1].lstrip("0"),
                "finger": parts[2],
                "scanner": parts[3],
                "action": parts[4],
                "relay": parts[5],
            }
            return ("authenticated", event_data) if event_data["action"] == "1" else ("failed", event_data)

        if self._conf_type == TYPE_MULTI and len(parts) == 10:
            event_data = {
                "type": parts[0],
                "user": parts[1].lstrip("0"),
                "user_name": parts[2].lstrip("-"),
                "user_status": parts[3],
                "finger": parts[4],
                "relay": parts[5],
                "scanner": parts[6],
                "scanner_name": parts[7].lstrip("-"),
                "action": parts[8],
                "digital_input": parts[9],
            }
            return ("authenticated", event_data) if event_data["action"] == "1" else ("failed", event_data)

        _LOGGER.warning(
            "Ignored invalid %s payload on port %s: %s",
            self._conf_type,
            self._conf_port,
            text_message,
        )
        return None

    async def async_will_remove_from_hass(self) -> None:
        """Unregister the Ekey (legacy) event."""
        if self._transport is not None:
            self._transport.close()
            self._transport = None


class _EkeyUDPProtocol(asyncio.DatagramProtocol):
    """UDP protocol handler for incoming Ekey packets."""

    def __init__(self, hass: HomeAssistant, entity: EkeyLegacyAuthEvent) -> None:
        self.hass = hass
        self.entity = entity

    def datagram_received(self, data: bytes, addr) -> None:
        self.entity.async_handle_event(data)


def _parse_rare_message(
    message: bytes,
    auth_command: int = DEFAULT_RARE_AUTH_CMD,
    fail_command: int = DEFAULT_RARE_FAIL_CMD,
) -> tuple[str, dict[str, str]] | None:
    """Parse a binary ekey RARE protocol packet."""
    if len(message) < RARE_PACKET_LENGTH:
        _LOGGER.warning("Ignored short rare packet with %s bytes", len(message))
        return None

    byteorder: str | None = None
    for order in ("big", "little"):
        if int.from_bytes(message[0:4], byteorder=order, signed=False) == 3:
            byteorder = order
            break

    if byteorder is None:
        version_be = int.from_bytes(message[0:4], byteorder="big", signed=False)
        version_le = int.from_bytes(message[0:4], byteorder="little", signed=False)
        _LOGGER.warning(
            "Ignored rare packet with unsupported version %s (big-endian) / %s (little-endian)",
            version_be,
            version_le,
        )
        return None

    def _u32(buf: bytes) -> int:
        return int.from_bytes(buf, byteorder=byteorder, signed=False)

    def _u16(buf: bytes) -> int:
        return int.from_bytes(buf, byteorder=byteorder, signed=False)

    version = _u32(message[0:4])
    command = _u32(message[4:8])

    if command == auth_command:
        event_type = "authenticated"
    elif command == fail_command:
        event_type = "failed"
    else:
        _LOGGER.warning(
            "Received rare packet with unknown command %s – treating as failed",
            f"{command:#x}",
        )
        event_type = "failed"

    event_data = {
        "version": str(version),
        "command": str(command),
        "action": "open" if event_type == "authenticated" else "reject",
        "terminal_id": str(_u32(message[8:12])),
        "terminal_serial": _decode_rare_text_field(message[12:26]),
        "relay": str(message[26]),
        "user": str(_u32(message[28:32])),
        "finger": str(_u32(message[32:36])),
        "event": _decode_rare_text_field(message[36:52]),
        "timestamp": _decode_rare_text_field(message[52:68]),
        "name": str(_u16(message[68:70])),
        "personal_id": str(_u16(message[70:72])),
    }

    _LOGGER.info(
        "Received rare event '%s' for terminal '%s'",
        event_data["action"],
        event_data["terminal_serial"],
    )
    _LOGGER.debug("Parsed rare event data: %s", event_data)
    return event_type, event_data


def _decode_rare_text_field(value: bytes) -> str:
    """Decode a fixed-length ASCII field from a rare packet."""
    return value.decode("ascii", errors="ignore").rstrip("\x00 ").strip()


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the Ekey (legacy) event platform."""
    _migrate_entity_id(
        hass,
        f"{config_entry.data[CONF_TYPE]}-{config_entry.data[CONF_PORT]}",
        f"event.ekey_{config_entry.data[CONF_TYPE]}",
    )
    async_add_entities(
        [
            EkeyLegacyAuthEvent(config_entry)
        ]
    )


@callback
def _migrate_entity_id(
    hass: HomeAssistant, unique_id: str, expected_entity_id: str
) -> None:
    """Rename legacy event entity IDs to the new `event.ekey_<type>` format."""
    entity_registry = er.async_get(hass)
    current_entity_id = entity_registry.async_get_entity_id("event", DOMAIN, unique_id)
    if current_entity_id is None or current_entity_id == expected_entity_id:
        return

    try:
        entity_registry.async_update_entity(
            current_entity_id,
            new_entity_id=expected_entity_id,
        )
    except ValueError:
        _LOGGER.warning(
            "Cannot migrate entity ID for %s from %s to %s because the target is already in use",
            unique_id,
            current_entity_id,
            expected_entity_id,
        )
