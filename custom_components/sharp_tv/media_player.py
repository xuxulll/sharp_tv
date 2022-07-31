"""Support for SHARP TV running """
from __future__ import annotations

from homeassistant.components.media_player import (
    MediaPlayerDeviceClass,
    MediaPlayerEntity,
    MediaPlayerEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import STATE_OFF, STATE_PAUSED, STATE_PLAYING
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Sharp TV Media Player from a config_entry."""

    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    unique_id = config_entry.unique_id
    assert unique_id is not None

    async_add_entities(
        [SharpTVMediaPlayer(coordinator, unique_id, config_entry.title)]
    )


class SharpTVMediaPlayer(SharpTVEntity, MediaPlayerEntity):
    """Representation of a Sharp TV."""

    _attr_device_class = MediaPlayerDeviceClass.TV
    _attr_supported_features = (
        MediaPlayerEntityFeature.PAUSE
        | MediaPlayerEntityFeature.VOLUME_STEP
        | MediaPlayerEntityFeature.VOLUME_MUTE
        | MediaPlayerEntityFeature.PREVIOUS_TRACK
        | MediaPlayerEntityFeature.NEXT_TRACK
        | MediaPlayerEntityFeature.TURN_ON
        | MediaPlayerEntityFeature.TURN_OFF
        | MediaPlayerEntityFeature.SELECT_SOURCE
        | MediaPlayerEntityFeature.PLAY
        | MediaPlayerEntityFeature.STOP
    )

    @property
    def name(self):
        """Return the name of the device."""
        return self.coordinator._name

    @property
    def state(self):
        """Return the state of the device."""
        return self.coordinator._state

    @property
    def is_volume_muted(self):
        """Boolean if volume is currently muted."""
        return self.coordinator._muted

    @property
    def volume_level(self):
        """Volume level of the media player (0..1)."""
        return self.coordinator._volume / 100.0

    async def async_turn_on(self) -> None:
        """Turn the device on."""
        await self.coordinator.async_turn_on()

    async def async_turn_off(self) -> None:
        """Turn off device."""
        await self.coordinator.async_turn_off()

    async def async_volume_up(self) -> None:
        """Send volume up command to device."""
        await self.coordinator.async_volume_up()

    async def async_volume_down(self) -> None:
        """Send volume down command to device."""
        await self.coordinator.async_volume_down()

    async def async_mute_volume(self, mute: bool) -> None:
        """Send mute command to device."""
        await self.coordinator.async_mute_volume(mute)

    async def async_media_play(self) -> None:
        """Send play command to device."""
        await self.coordinator.async_media_play()

    async def async_media_pause(self) -> None:
        """Send pause command to device."""
        await self.coordinator.async_media_pause()

    async def async_media_stop(self) -> None:
        """Send stop command to device."""
        await self.coordinator.async_volume_down()

    async def async_media_next_track(self) -> None:
        """Send next track command."""
        await self.coordinator.async_media_next_track()

    async def async_media_previous_track(self) -> None:
        """Send previous track command."""
        await self.coordinator.async_media_previous_track()
