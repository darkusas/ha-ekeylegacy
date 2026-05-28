"""Binary sensor platform for Ekey (legacy) events."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.components.binary_sensor import BinarySensorEntity, PLATFORM_SCHEMA
from homeassistant.const import CONF_NAME
from homeassistant.core import CALLBACK_TYPE, Event, HomeAssistant, callback
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_call_later

from .const import CONF_DURATION, DEFAULT_DURATION, EVENT_TYPE_NAME

_DEFAULT_NAME = "ekey trigger"
_RESERVED_CONFIG_KEYS = {CONF_NAME, CONF_DURATION}

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Optional(CONF_NAME, default=_DEFAULT_NAME): cv.string,
        vol.Optional(CONF_DURATION, default=DEFAULT_DURATION): vol.All(
            vol.Coerce(float), vol.Range(min=0.1)
        ),
    },
    extra=vol.ALLOW_EXTRA,
)


async def async_setup_platform(
    hass: HomeAssistant,
    config: dict[str, Any],
    async_add_entities: AddEntitiesCallback,
    _discovery_info: dict[str, Any] | None = None,
) -> None:
    """Set up ekey legacy binary sensor from YAML."""
    matchers = {
        key: str(value)
        for key, value in config.items()
        if key not in _RESERVED_CONFIG_KEYS
    }

    async_add_entities(
        [
            EkeyLegacyTriggerBinarySensor(
                name=config[CONF_NAME],
                pulse_seconds=config[CONF_DURATION],
                matchers=matchers,
            )
        ]
    )


class EkeyLegacyTriggerBinarySensor(BinarySensorEntity):
    """Pulse-based binary sensor activated by matching ekey events."""

    _attr_should_poll = False
    _attr_has_entity_name = False

    def __init__(
        self,
        name: str,
        pulse_seconds: float,
        matchers: dict[str, str],
    ) -> None:
        """Initialize the trigger binary sensor."""
        self._attr_name = name
        self._pulse_seconds = pulse_seconds
        self._matchers = matchers
        self._is_on = False
        self._cancel_turn_off: CALLBACK_TYPE | None = None

    @property
    def is_on(self) -> bool:
        """Return true if sensor is on."""
        return self._is_on

    async def async_added_to_hass(self) -> None:
        """Register listeners."""
        self.async_on_remove(
            self.hass.bus.async_listen(EVENT_TYPE_NAME, self._handle_ekey_event)
        )

    async def async_will_remove_from_hass(self) -> None:
        """Cancel pending off timer on remove."""
        if self._cancel_turn_off is not None:
            self._cancel_turn_off()
            self._cancel_turn_off = None

    @callback
    def _handle_ekey_event(self, event: Event) -> None:
        """Handle incoming ekey event bus message."""
        data = event.data

        if not self._matches(data):
            return

        self._is_on = True
        self.async_write_ha_state()
        self._schedule_turn_off()

    def _matches(self, event_data: dict[str, Any]) -> bool:
        """Return whether event data matches configured filters."""
        for key, expected_value in self._matchers.items():
            if str(event_data.get(key, "")) != expected_value:
                return False

        return True

    @callback
    def _schedule_turn_off(self) -> None:
        """Schedule automatic sensor reset."""
        if self._cancel_turn_off is not None:
            self._cancel_turn_off()

        self._cancel_turn_off = async_call_later(
            self.hass, self._pulse_seconds, self._async_turn_off
        )

    @callback
    def _async_turn_off(self, _now: Any) -> None:
        """Reset sensor back to off state."""
        self._cancel_turn_off = None
        if not self._is_on:
            return

        self._is_on = False
        self.async_write_ha_state()
