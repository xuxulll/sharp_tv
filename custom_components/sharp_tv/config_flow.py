"""Adds config flow for Bravia TV integration."""
from __future__ import annotations

from contextlib import suppress
import ipaddress
import re
from typing import Any

import voluptuous as vol

from homeassistant import config_entries, exceptions
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_PORT
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
import homeassistant.helpers.config_validation as cv

from . import _send_command

from .const import (
    ATTR_CID,
    ATTR_MAC,
    ATTR_MODEL,
    DOMAIN,
)


def host_valid(host: str) -> bool:
    """Return True if hostname or IP address is valid."""
    with suppress(ValueError):
        if ipaddress.ip_address(host).version in [4, 6]:
            return True
    disallowed = re.compile(r"[^a-zA-Z\d\-]")
    return all(x and not disallowed.search(x) for x in host.split("."))


class SharpTVConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for SharpTV integration."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize."""
        self.host: str | None = None
        self.title = ""
        self.port: int | None = None

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> SharpTVOptionsFlowHandler:
        """Bravia TV options callback."""
        return SharpTVOptionsFlowHandler(config_entry)

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Show the setup form to the user."""
        host = user_input.get(CONF_HOST, "") if user_input else ""
        data_schema = vol.Schema(
            {
                vol.Required(CONF_HOST, default=host): str,
                vol.Required(CONF_PORT, default=9688): cv.port,
            },
        )

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors={"base": error} if error else None,
        )


class SharpTVOptionsFlowHandler(config_entries.OptionsFlow):
    """Config flow options for Sharp TV."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize Sharp TV options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        coordinator = self.hass.data[DOMAIN][self.config_entry.entry_id]
        return await self.async_step_user()

    def getMac(
        self, ipaddr: str
    ) -> str:
        from subprocess import Popen, PIPE
        import re
        pid = Popen(["arp", "-n", ipaddr], stdout=PIPE)
        s = pid.communicate()[0]
        mac = re.search(r"(([a-f\d]{1,2}\:){5}[a-f\d]{1,2})", s).groups()[0]
        return mac

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle a flow initiated by the user."""
        error = None

        if user_input is not None:
            host = user_input[CONF_HOST]
            
            unique_id = self.getMac(host)
            if unique_id is not None:
                await self.async_set_unique_id(unique_id)
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=host,
                    data=user_input,
                )
                
        host = user_input.get(CONF_HOST, "") if user_input else ""
        data_schema = vol.Schema(
            {
                vol.Required(CONF_HOST, default=host): str,
                vol.Required(CONF_PORT, default=9688): cv.port,
            },
        )

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors={"base": error} if error else None,
        )

