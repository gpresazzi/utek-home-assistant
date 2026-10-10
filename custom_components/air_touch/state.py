"""Interpret operating selections from the observed register map."""


def ventilation_mode(data: dict[int, int]) -> str | None:
    """Describe selection, not measured airflow or the physical fan state."""
    flags, setpoint = data.get(20), data.get(51)
    if flags is None or setpoint is None:
        return None
    if flags & 32 or setpoint == 0:
        return "Spenta"
    if setpoint == 101:
        return "Programmazione oraria"
    if 1 <= setpoint <= 100:
        return "Manuale"
    return "Non riconosciuta"
