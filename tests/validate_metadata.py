"""Basic package metadata and translation consistency."""

import json
from pathlib import Path

root = Path(__file__).parents[1]
component = root / "custom_components/air_touch"
manifest = json.loads((component / "manifest.json").read_text())
assert manifest["domain"] == component.name
assert manifest["config_flow"] is True
assert manifest["iot_class"] == "local_polling"
strings = json.loads((component / "strings.json").read_text())


def keys(value, prefix=""):
    result = set()
    for key, child in value.items():
        path = f"{prefix}.{key}"
        result.add(path)
        if isinstance(child, dict):
            result.update(keys(child, path))
    return result


for translation in (component / "translations").glob("*.json"):
    assert keys(json.loads(translation.read_text())) == keys(strings), translation
json.loads((root / "hacs.json").read_text())
print("Metadata and translation keys valid")
