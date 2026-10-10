"""Coordinate polls and commands."""

from datetime import timedelta
import logging

from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    CONF_ENABLE_WRITES, CONF_POLL_INTERVAL, DEFAULT_POLL_INTERVAL, READ_BLOCKS,
)
from .modbus import ModbusError

_LOGGER = logging.getLogger(__name__)


class AirTouchCoordinator(DataUpdateCoordinator[dict[int, int]]):
    """One poll for all entities of a device."""

    def __init__(self, hass, entry, client):
        super().__init__(
            hass, _LOGGER, name="Air Touch VMC", config_entry=entry,
            update_interval=timedelta(seconds=entry.options.get(
                CONF_POLL_INTERVAL, DEFAULT_POLL_INTERVAL
            )), always_update=False,
        )
        self.client = client
        self.writes_enabled = entry.options.get(CONF_ENABLE_WRITES, False)

    async def _async_update_data(self):
        try:
            return await self.client.read_blocks(READ_BLOCKS)
        except ModbusError as err:
            raise UpdateFailed(f"Modbus communication failed: {err}") from err

    async def async_set_mode(self, shift: int, value: int):
        if not self.writes_enabled:
            raise HomeAssistantError("Enable experimental writes in integration options")
        if shift not in (0, 2) or value not in (0, 1, 2):
            raise HomeAssistantError("Unsupported mode")
        try:
            await self.client.update_bits(20, shift, 2, value)
        except ModbusError as err:
            # Do not retry a possibly accepted write, or change state optimistically.
            await self.async_request_refresh()
            raise HomeAssistantError(f"Command could not be confirmed: {err}") from err
        await self.async_request_refresh()


    async def async_set_ventilation(self, value: int):
        """Send a device selection, then refresh measured states."""
        if not self.writes_enabled:
            raise HomeAssistantError("Enable writes in integration options")
        if value not in (0, 30, 65, 101):
            raise HomeAssistantError("Unsupported ventilation selection")
        try:
            await self.client.set_ventilation(value)
        except ModbusError as err:
            await self.async_request_refresh()
            raise HomeAssistantError(
                f"Ventilation command could not be confirmed: {err}"
            ) from err
        await self.async_request_refresh()
