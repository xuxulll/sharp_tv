"""Remote control support for Sharp TV."""
from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from homeassistant.components.remote import ATTR_NUM_REPEATS, RemoteEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.const import STATE_OFF

from .const import DOMAIN
from .entity import SharpTVEntity


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Sharp TV Remote from a config entry."""

    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    unique_id = config_entry.unique_id
    assert unique_id is not None

    async_add_entities([SharpTVRemote(coordinator, unique_id, config_entry.title)])


class SharpTVRemote(SharpTVEntity, RemoteEntity):
    """Representation of a Sharp TV Remote."""

    @property
    def is_on(self) -> bool:
        """Return true if device is on."""
        return self.coordinator._state is not STATE_OFF

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the device on."""
        await self.coordinator.async_turn_on()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the device off."""
        await self.coordinator.async_turn_off()

    async def async_send_command(self, command: str, **kwargs: Any) -> None:
        """Send a command to device."""
        await self.coordinator.async_send_command(command)