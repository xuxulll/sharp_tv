"""Adds config flow for Bravia TV integration."""
from __future__ import annotations

import logging
import fcntl
import socket
import struct

from typing import Any

_LOGGER = logging.getLogger(__name__)

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError

import voluptuous as vol

from contextlib import suppress
import ipaddress
import re

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PORT

from .const import DOMAIN

import homeassistant.helpers.config_validation as cv

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Required(CONF_PORT, default=9688): cv.port,
    }
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

    def getMac(self, ipaddr: str) -> str:
        from subprocess import Popen, PIPE
        import re

        pid = Popen(["arp", "-a", ipaddr], stdout=PIPE)
        s = pid.communicate()[0]
        mac = re.search(r"(([a-f\d]{1,2}\:){5}[a-f\d]{1,2})", s).groups()[0]
        return mac

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Show the setup form to the user."""
        if user_input is None:
            return self.async_show_form(
                step_id="user", data_schema=STEP_USER_DATA_SCHEMA
            )

        errors = {}

        # Validate user input
        host = user_input[CONF_HOST]

        valid = host_valid(host)
        if valid:
            unique_id = self.getMac(host)
            if unique_id is not None:
                await self.async_set_unique_id(unique_id)
                self._abort_if_unique_id_configured()
                # See next section on create entry usage
                return self.async_create_entry(
                    title=host,
                    data=user_input,
                )
            else:
                errors["base"] = "unique_id"
                return self.async_show_form(
                    step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
                )
        else:
            errors["base"] = "host_invalid"
            return self.async_show_form(
                step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
            )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""
