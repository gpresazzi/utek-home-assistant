"""Experimental mode commands with field readback."""

from homeassistant.components.select import SelectEntity

from .entity import AirTouchEntity


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = entry.runtime_data
    if coordinator.writes_enabled:
        async_add_entities([
            AirTouchVentilationSelect(coordinator, entry),
            AirTouchModeSelect(coordinator, entry, "season", "Season", 0,
                               ["auto", "winter", "summer"]),
            AirTouchModeSelect(coordinator, entry, "bypass_mode", "Bypass mode", 2,
                               ["auto", "off", "on"]),
        ])


class AirTouchModeSelect(AirTouchEntity, SelectEntity):
    def __init__(self, coordinator, entry, key, name, shift, options):
        super().__init__(coordinator, entry, key)
        self._attr_name = name
        self.shift = shift
        self._attr_options = options

    @property
    def current_option(self):
        raw = self.coordinator.data.get(20)
        if raw is None:
            return None
        value = (raw >> self.shift) & 3
        return self.options[value] if value < len(self.options) else None

    async def async_select_option(self, option):
        await self.coordinator.async_set_mode(self.shift, self.options.index(option))


VENTILATION_OPTIONS = {
    "Spenta": 0,
    "Programmazione oraria": 101,
    "Sole (30)": 30,
    "Aperitivo (65)": 65,
}


class AirTouchVentilationSelect(AirTouchEntity, SelectEntity):
    """Selectable commands separate from the measured operating state."""

    _attr_name = "Controllo ventilazione"
    _attr_icon = "mdi:fan"
    _attr_options = list(VENTILATION_OPTIONS)

    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry, "ventilation_control")

    @property
    def current_option(self):
        data = self.coordinator.data
        flags, value = data.get(20), data.get(51)
        if flags is None or value is None:
            return None
        if flags & 32:
            return "Spenta"
        return next((name for name, raw in VENTILATION_OPTIONS.items()
                     if raw == value), None)

    async def async_select_option(self, option):
        await self.coordinator.async_set_ventilation(VENTILATION_OPTIONS[option])
