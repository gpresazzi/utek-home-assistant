#!/usr/bin/env python3
"""Read a VMC using the integration's Python client, without Home Assistant."""

import argparse
import asyncio
import importlib.util
import json
from pathlib import Path
import sys


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def bounded_int(minimum, maximum):
    def parse(text):
        value = int(text)
        if not minimum <= value <= maximum:
            raise argparse.ArgumentTypeError(f"Valore ammesso: {minimum}–{maximum}")
        return value
    return parse


async def read(args, root):
    component = root / "custom_components" / "air_touch"
    protocol = load_module(component / "modbus.py", "air_touch_standalone_modbus")
    constants = load_module(component / "const.py", "air_touch_standalone_const")
    client = protocol.AirTouchClient(args.host, args.port, args.unit_id, args.timeout)
    blocks = ((args.register, args.count),) if args.register else constants.READ_BLOCKS
    try:
        data = await client.read_blocks(blocks)
    finally:
        await client.close()
    mapping_path = root / "analysis" / "registers.json"
    descriptors = {}
    if mapping_path.exists():
        mapping = json.loads(mapping_path.read_text())
        descriptors = {r["id"]: r for r in mapping["registers"]}
    result = {}
    for register, raw in data.items():
        descriptor = descriptors.get(register, {})
        item = {"address": register - 1, "name": descriptor.get("name"), "raw": raw,
                "hex": f"0x{raw:04X}"}
        if descriptor.get("isMultiple"):
            item["fields"] = {
                field["name"]: (raw >> field["startingBit"]) & ((1 << field["length"]) - 1)
                for field in descriptor["dataFormat"].values()
            }
        result[str(register)] = item
    print(json.dumps(result, ensure_ascii=False, indent=2))


def main():
    if sys.version_info < (3, 11):
        print("Serve Python 3.11 o successivo.", file=sys.stderr)
        return 1
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("host", help="IP o hostname della VMC")
    parser.add_argument("--port", type=bounded_int(1, 65535), default=502)
    parser.add_argument("--unit-id", type=bounded_int(1, 247), default=1)
    parser.add_argument("--timeout", type=bounded_int(1, 60), default=5)
    parser.add_argument("--register", type=bounded_int(1, 65536),
                        help="ID registro nell'app (base 1); default: blocchi dell'integrazione")
    parser.add_argument("--count", type=bounded_int(1, 125), default=1)
    args = parser.parse_args()
    if args.count != 1 and args.register is None:
        parser.error("--count richiede --register")
    if args.register and args.register + args.count - 1 > 65536:
        parser.error("Il blocco supera l'indirizzo Modbus massimo")
    try:
        asyncio.run(read(args, Path(__file__).resolve().parents[1]))
    except (OSError, ValueError, Exception) as err:
        print(f"Lettura fallita: {err}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        return 130
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
