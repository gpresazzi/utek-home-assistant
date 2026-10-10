"""Download protocol diagnostics without the network address."""

from homeassistant.const import CONF_HOST
from homeassistant.components.diagnostics import async_redact_data


async def async_get_config_entry_diagnostics(hass, entry):
    coordinator = entry.runtime_data
    return {
        "connection": async_redact_data(dict(entry.data), {CONF_HOST}),
        "options": dict(entry.options),
        "last_update_success": coordinator.last_update_success,
        "registers": {str(k): v for k, v in (coordinator.data or {}).items()},
        "address_convention": "app register ID minus 1",
    }
