"""UI configuration and options."""

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import callback

from .const import (
    DOMAIN, CONF_UNIT_ID, CONF_ENABLE_WRITES, CONF_POLL_INTERVAL,
    DEFAULT_PORT, DEFAULT_UNIT_ID, DEFAULT_POLL_INTERVAL, READ_BLOCKS,
)
from .modbus import AirTouchClient, ModbusError


class AirTouchConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Configure a local VMC endpoint."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            user_input[CONF_HOST] = user_input[CONF_HOST].strip().lower()
            await self.async_set_unique_id(
                f"{user_input[CONF_HOST]}:{user_input[CONF_PORT]}:{user_input[CONF_UNIT_ID]}"
            )
            self._abort_if_unique_id_configured()
            client = AirTouchClient(
                user_input[CONF_HOST], user_input[CONF_PORT], user_input[CONF_UNIT_ID]
            )
            try:
                await client.read_blocks(READ_BLOCKS)
            except ModbusError:
                errors["base"] = "cannot_connect"
            else:
                return self.async_create_entry(title="Air Touch VMC", data=user_input)
            finally:
                await client.close()
        return self.async_show_form(
            step_id="user", errors=errors,
            data_schema=vol.Schema({
                vol.Required(CONF_HOST): vol.All(str, vol.Length(min=1)),
                vol.Required(CONF_PORT, default=DEFAULT_PORT): vol.All(
                    vol.Coerce(int), vol.Range(min=1, max=65535)
                ),
                vol.Required(CONF_UNIT_ID, default=DEFAULT_UNIT_ID): vol.All(
                    vol.Coerce(int), vol.Range(min=1, max=247)
                ),
            }),
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return AirTouchOptionsFlow()


class AirTouchOptionsFlow(config_entries.OptionsFlow):
    """Configure polling and opt-in command entities."""

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)
        return self.async_show_form(
            step_id="init", data_schema=vol.Schema({
                vol.Required(CONF_POLL_INTERVAL, default=self.config_entry.options.get(
                    CONF_POLL_INTERVAL, DEFAULT_POLL_INTERVAL
                )): vol.All(vol.Coerce(int), vol.Range(min=10, max=3600)),
                vol.Required(CONF_ENABLE_WRITES, default=self.config_entry.options.get(
                    CONF_ENABLE_WRITES, False
                )): bool,
            }),
        )
