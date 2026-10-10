"""Operating status and aggregate alarms."""

from homeassistant.components.binary_sensor import BinarySensorEntity, BinarySensorDeviceClass

from .entity import AirTouchEntity

FLAGS = (
    ("bypass", "Bypass active", 86, 0),
    ("supply_remote", "Supply remote control active", 86, 1),
    ("exhaust_remote", "Exhaust remote control active", 86, 2),
    ("dehumidifier", "Dehumidifier active", 86, 3),
    ("nofrost", "Antifrost active", 86, 4),
    ("remote_off", "Remote off input", 86, 7),
    ("fire", "Fire input", 86, 12),
    ("water_low", "Water temperature low", 86, 10),
    ("alarms_1", "Alarms 1", 90, None),
    ("alarms_2", "Alarms 2", 97, None),
    ("filter_alarm", "Filter alarm", 90, 4),
    ("fan_alarm", "Fan alarm", 90, 5),
)


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities(AirTouchBinarySensor(entry.runtime_data, entry, *flag)
                       for flag in FLAGS)
    async_add_entities([AirTouchFansRunningSensor(entry.runtime_data, entry)])


class AirTouchBinarySensor(AirTouchEntity, BinarySensorEntity):
    def __init__(self, coordinator, entry, key, name, register, bit):
        super().__init__(coordinator, entry, key)
        self._attr_name = name
        self.register = register
        self.bit = bit
        if register in (90, 97):
            self._attr_device_class = BinarySensorDeviceClass.PROBLEM

    @property
    def is_on(self):
        raw = self.coordinator.data.get(self.register)
        if raw is None:
            return None
        return bool(raw if self.bit is None else raw & (1 << self.bit))


class AirTouchFansRunningSensor(AirTouchEntity, BinarySensorEntity):
    """Measured fan movement, separate from the requested operating mode."""

    _attr_name = "Ventilatori in funzione"
    _attr_icon = "mdi:fan"

    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry, "fans_running")

    @property
    def is_on(self):
        data = self.coordinator.data
        if 87 not in data or 88 not in data:
            return None
        return bool(data[87] or data[88])
