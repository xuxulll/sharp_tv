"""The Sharp TV component."""
from __future__ import annotations

import asyncio
from collections.abc import Iterable
from datetime import timedelta
import logging
from typing import Final
import paramiko
import threading
from requests import RequestException
import voluptuous as vol

from homeassistant import util
from homeassistant.components.media_player import MediaPlayerEntity, PLATFORM_SCHEMA
from homeassistant.components.media_player.const import (
    SUPPORT_NEXT_TRACK,
    SUPPORT_PAUSE,
    SUPPORT_PLAY,
    SUPPORT_PREVIOUS_TRACK,
    SUPPORT_SELECT_SOURCE,
    SUPPORT_TURN_OFF,
    SUPPORT_TURN_ON,
    SUPPORT_VOLUME_MUTE,
    SUPPORT_VOLUME_STEP,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_HOST,
    CONF_NAME,
    CONF_PORT,
    STATE_ON,
    STATE_OFF,
    STATE_PAUSED,
    STATE_PLAYING,
    Platform,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.debounce import Debouncer
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

import homeassistant.helpers.config_validation as cv

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

PLATFORMS: Final[list[Platform]] = [Platform.MEDIA_PLAYER, Platform.REMOTE]
SCAN_INTERVAL: Final = timedelta(seconds=10)

DEFAULT_NAME = "Sharp TV"
DEFAULT_PORT = 9688

SUPPORT_SHARPTV = (
    SUPPORT_PAUSE
    | SUPPORT_VOLUME_STEP
    | SUPPORT_VOLUME_MUTE
    | SUPPORT_PREVIOUS_TRACK
    | SUPPORT_NEXT_TRACK
    | SUPPORT_TURN_OFF
    | SUPPORT_TURN_ON
    | SUPPORT_PLAY
)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_HOST): cv.string,
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
        vol.Optional(CONF_PORT, default=DEFAULT_PORT): cv.port,
    }
)

async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Set up a config entry."""
    host = config_entry.data[CONF_HOST]
    name = config_entry.data[CONF_NAME]
    port = config_entry.data[CONF_PORT]

    coordinator = SharpTVCoordinator(hass, host, name, port)
    config_entry.async_on_unload(config_entry.add_update_listener(update_listener))

    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][config_entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(config_entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(
        config_entry, PLATFORMS
    )

    if unload_ok:
        hass.data[DOMAIN].pop(config_entry.entry_id)

    return unload_ok


async def update_listener(hass: HomeAssistant, config_entry: ConfigEntry) -> None:
    """Handle options update."""
    await hass.config_entries.async_reload(config_entry.entry_id)


class SharpTVCoordinator(DataUpdateCoordinator[None]):
    """Representation of a Sharp TV Coordinator.
    An instance is used per device to share the same power state between
    several platforms.
    """

    def __init__(
        self,
        hass: HomeAssistant,
        host: str,
        name: str,
        port: str,
    ) -> None:
        """Initialize Bravia TV Client."""
        self._host = host
        self._port = port
        self._name = name
        self._muted = False
        # Assume that the TV is in Play mode
        self._playing = True
        self._volume = 0
        self._state = None

        self.state_lock = asyncio.Lock()

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=SCAN_INTERVAL,
            request_refresh_debouncer=Debouncer(
                hass, _LOGGER, cooldown=1.0, immediate=False
            ),
        )

    def _send_command(self, command: str) -> None:
        """Send remote control commands to the TV."""
        import socket
        import time
        s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        s.settimeout(5)
        try:
            s.connect((self.host,self.port))
            s.send(command.encode('utf-8'))
            s.close()
            self._state = STATE_ON
        except socket.error as err:
            self._state = STATE_OFF

    def turn_on(self):
        """Wake the TV back up from sleep."""
        if self._state is not STATE_ON:
            #if self.hass.services.has_service('hdmi_cec','power_on'):
            #    self.hass.services.call('hdmi_cec','power_on')
            #else:
            #    _LOGGER.warning("hdmi_cec.power_on not exist!")
            cmd = ['echo "on 0" | cec-client -s']
            a=threading.Thread(target=self.ssh2,args=('192.168.31.58',22,'pi','yuan.1995.',cmd))
            a.start()

    def turn_off(self):
        """Turn off media player."""
        if self._state is not STATE_OFF:
            self.send_command('SPRC#DIRK#19#1#2#1|22#')

    def volume_up(self):
        """Volume up the media player."""
        self.send_command('SPRC#DIRK#19#1#2#1|20#')

    def volume_down(self):
        """Volume down media player."""
        self.send_command('SPRC#DIRK#19#1#2#1|21#')

    def mute_volume(self, mute):
        """Send mute command."""
        self.send_command('SPRC#DIRK#19#1#2#1|23#')

    def media_play_pause(self):
        """Simulate play pause media player."""
        if self._playing:
            self.media_pause()
        else:
            self.media_play()

    def media_play(self):
        """Send play command."""
        self._playing = True
        self._state = STATE_PLAYING
        self.send_command('SPRC#DIRK#19#1#2#1|36#')

    def media_pause(self):
        """Send media pause command to media player."""
        self._playing = False
        self._state = STATE_PAUSED
        self.send_command('SPRC#DIRK#19#1#2#1|36#')

    def media_next_track(self):
        """Send next track command."""
        self.send_command('SPRC#DIRK#19#1#2#1|246#')

    def media_previous_track(self):
        """Send the previous track command."""
        self.send_command('SPRC#DIRK#19#1#2#1|245#')

    async def async_turn_on(self) -> None:
        """Turn the device on."""
        async with self.state_lock:
            await self.hass.async_add_executor_job(self.turn_on)
            await self.async_request_refresh()

    async def async_turn_off(self) -> None:
        """Turn off device."""
        async with self.state_lock:
            await self.hass.async_add_executor_job(self.turn_off)
            await self.async_request_refresh()

    async def async_volume_up(self) -> None:
        """Send volume up command to device."""
        async with self.state_lock:
            await self.hass.async_add_executor_job(self.volume_up)
            await self.async_request_refresh()

    async def async_volume_down(self) -> None:
        """Send volume down command to device."""
        async with self.state_lock:
            await self.hass.async_add_executor_job(self.volume_down)
            await self.async_request_refresh()

    async def async_mute_volume(self, mute: bool) -> None:
        """Send mute command to device."""
        async with self.state_lock:
            await self.hass.async_add_executor_job(self.mute_volume, mute)
            await self.async_request_refresh()

    async def async_media_play(self) -> None:
        """Send play command to device."""
        async with self.state_lock:
            await self.hass.async_add_executor_job(self.media_play)
            await self.async_request_refresh()

    async def async_media_pause(self) -> None:
        """Send pause command to device."""
        async with self.state_lock:
            await self.hass.async_add_executor_job(self.media_pause)
            await self.async_request_refresh()

    async def async_media_stop(self) -> None:
        """Send stop command to device."""
        async with self.state_lock:
            await self.hass.async_add_executor_job(self.media_stop)
            await self.async_request_refresh()

    async def async_media_next_track(self) -> None:
        """Send next track command."""
        async with self.state_lock:
            await self.hass.async_add_executor_job(self.media_next_track)
            await self.async_request_refresh()

    async def async_media_previous_track(self) -> None:
        """Send previous track command."""
        async with self.state_lock:
            await self.hass.async_add_executor_job(self.media_previous_track)
            await self.async_request_refresh()

    async def async_send_command(self, command: str) -> None:
        """Send command to device."""
        async with self.state_lock:
            await self.hass.async_add_executor_job(self._send_command, command)
            await self.async_request_refresh()