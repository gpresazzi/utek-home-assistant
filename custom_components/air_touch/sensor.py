"""Raw registers and interpreted measurements."""

from homeassistant.components.sensor import (
    SensorEntity, SensorDeviceClass, SensorStateClass,
)
from homeassistant.const import EntityCategory, UnitOfTemperature, UnitOfTime

from .entity import AirTouchEntity
from .state import ventilation_mode

RAW_REGISTERS = {
    20: "Parameter flags", 51: "Speed setpoint raw", 52: "Temperature setpoint raw",
    53: "Timer", 54: "Remote fan control raw", 55: "Humidity setpoint",
    56: "Free temperature setpoint raw", 81: "Temperature E raw",
    82: "Temperature R raw", 83: "Temperature X raw", 84: "Temperature I raw",
    85: "Temperature W raw", 86: "Status flags", 87: "Supply fan speed raw",
    88: "Exhaust fan speed raw", 89: "Auto input", 90: "Alarms 1 raw",
    91: "Supply pressure", 92: "Exhaust pressure", 93: "Supply flow",
    94: "Exhaust flow", 95: "Fan hours high", 96: "Fan hours low",
    97: "Alarms 2 raw", 98: "Preheat output", 99: "Postheat output",
    100: "Temperature D raw",
}
TEMPERATURES = {81: "E", 82: "R", 83: "X", 84: "I", 85: "W", 100: "D"}


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = entry.runtime_data
    entities = [AirTouchRegisterSensor(coordinator, entry, r, n)
                for r, n in RAW_REGISTERS.items()]
    entities.extend(AirTouchTemperatureSensor(coordinator, entry, r, n)
                    for r, n in TEMPERATURES.items())
    entities.append(AirTouchHoursSensor(coordinator, entry))
    entities.append(AirTouchModeSensor(coordinator, entry))
    async_add_entities(entities)


class AirTouchRegisterSensor(AirTouchEntity, SensorEntity):
    """Expose lossless raw values, retaining ambiguous speed encoding."""

    def __init__(self, coordinator, entry, register, name):
        super().__init__(coordinator, entry, f"register_{register}")
        self.register = register
        self._attr_name = name
        self._attr_entity_category = EntityCategory.DIAGNOSTIC
        self._attr_entity_registry_enabled_default = register in (87, 88, 90, 97)
        self._attr_extra_state_attributes = {
            "app_register": register, "modbus_address": register - 1,
        }
        if register in (91, 92):
            self._attr_native_unit_of_measurement = "Pa"
            self._attr_state_class = SensorStateClass.MEASUREMENT
        elif register in (93, 94):
            self._attr_native_unit_of_measurement = "m³/h"
            self._attr_state_class = SensorStateClass.MEASUREMENT
        elif register in (55, 89, 98, 99):
            self._attr_native_unit_of_measurement = "%"
        elif register == 53:
            self._attr_native_unit_of_measurement = UnitOfTime.SECONDS

    @property
    def native_value(self):
        return self.coordinator.data.get(self.register)


class AirTouchTemperatureSensor(AirTouchEntity, SensorEntity):
    """Signed int16 / 10 decoding; physical probe positions remain unconfirmed."""

    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_entity_registry_enabled_default = True

    def __init__(self, coordinator, entry, register, label):
        super().__init__(coordinator, entry, f"temperature_{register}")
        self.register = register
        self._attr_name = f"Temperatura {label}"

    @property
    def native_value(self):
        raw = self.coordinator.data.get(self.register)
        if raw is None or raw in (0x7FFF, 0x8000):
            return None
        return (raw - 65536 if raw & 0x8000 else raw) / 10


class AirTouchHoursSensor(AirTouchEntity, SensorEntity):
    """32-bit fan runtime, confirmed by the app UI."""

    _attr_name = "Fan runtime"
    _attr_device_class = SensorDeviceClass.DURATION
    _attr_native_unit_of_measurement = UnitOfTime.HOURS
    _attr_state_class = SensorStateClass.TOTAL_INCREASING

    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry, "fan_hours")

    @property
    def native_value(self):
        data = self.coordinator.data
        if 95 not in data or 96 not in data:
            return None
        return data[95] * 65536 + data[96]


class AirTouchModeSensor(AirTouchEntity, SensorEntity):
    """Show operating selection without confusing presets with fixed mode IDs."""

    _attr_name = "Modalità ventilazione"
    _attr_icon = "mdi:fan"

    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry, "ventilation_mode")

    @property
    def native_value(self):
        return ventilation_mode(self.coordinator.data)

    @property
    def extra_state_attributes(self):
        data = self.coordinator.data
        speed = data.get(51)
        flags = data.get(20)
        supply, exhaust = data.get(87), data.get(88)
        return {
            "setpoint_raw": speed,
            "speed_switch_off": bool(flags & 32) if flags is not None else None,
            "supply_speed_raw": supply,
            "exhaust_speed_raw": exhaust,
            "fans_running": bool(supply or exhaust)
                if supply is not None and exhaust is not None else None,
            "observed_profile": {30: "Sole", 65: "Aperitivo"}.get(speed),
        }
