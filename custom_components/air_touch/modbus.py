"""Small asynchronous Modbus TCP client for FC03 and FC06 only.

No retry of writes: a timeout may occur after the device accepted the command.
All operations, including read/modify/write, are serialized per client.
"""

import asyncio
from contextlib import asynccontextmanager
import struct


class ModbusError(Exception):
    """A communication, protocol or readback error."""


class AirTouchClient:
    """Use a short TCP session per poll or command with validated responses."""

    def __init__(self, host: str, port: int = 502, unit_id: int = 1, timeout: float = 5):
        self.host = host
        self.port = port
        self.unit_id = unit_id
        self.timeout = timeout
        self._transaction = 0
        self._reader = None
        self._writer = None
        self._lock = asyncio.Lock()

    async def _close(self):
        writer, self._writer = self._writer, None
        self._reader = None
        if writer is not None:
            writer.close()
            try:
                async with asyncio.timeout(1):
                    await writer.wait_closed()
            except (OSError, TimeoutError):
                pass

    async def close(self):
        """Close under the same lock as requests."""
        async with self._lock:
            await self._close()

    @asynccontextmanager
    async def _session(self):
        """Release the device connection before another operation starts."""
        async with self._lock:
            try:
                yield
            finally:
                await self._close()

    async def _request(self, function: int, register: int, value: int) -> bytes:
        if not 1 <= register <= 65536 or not 0 <= value <= 65535:
            raise ValueError("Register or value outside Modbus bounds")
        try:
            async with asyncio.timeout(self.timeout):
                if self._writer is None or self._writer.is_closing():
                    self._reader, self._writer = await asyncio.open_connection(
                        self.host, self.port
                    )
                self._transaction = self._transaction % 65535 + 1
                transaction = self._transaction
                pdu = struct.pack(">BHH", function, register - 1, value)
                self._writer.write(
                    struct.pack(">HHHB", transaction, 0, len(pdu) + 1, self.unit_id)
                    + pdu
                )
                await self._writer.drain()
                header = await self._reader.readexactly(7)
                response_id, protocol, length, unit = struct.unpack(">HHHB", header)
                if (response_id, protocol, unit) != (transaction, 0, self.unit_id):
                    raise ModbusError("Unexpected MBAP header")
                if not 2 <= length <= 254:
                    raise ModbusError("Invalid MBAP length")
                response = await self._reader.readexactly(length - 1)
                if response[0] == function | 0x80:
                    if len(response) != 2:
                        raise ModbusError("Malformed Modbus exception")
                    raise ModbusError(f"Modbus exception {response[1]}")
                if response[0] != function:
                    raise ModbusError("Unexpected function code")
                if function == 6 and response != pdu:
                    raise ModbusError("Write echo differs from request")
                return response
        except asyncio.CancelledError:
            await self._close()
            raise
        except (OSError, TimeoutError, asyncio.IncompleteReadError, ModbusError) as err:
            await self._close()
            raise ModbusError(str(err) or type(err).__name__) from err

    async def _read(self, register: int, count: int) -> list[int]:
        if not 1 <= count <= 125 or register + count - 1 > 65536:
            raise ValueError("Invalid read range")
        response = await self._request(3, register, count)
        if len(response) != 2 + count * 2 or response[1] != count * 2:
            await self._close()
            raise ModbusError("Unexpected register count")
        return list(struct.unpack(f">{count}H", response[2:]))

    async def read_blocks(self, blocks) -> dict[int, int]:
        """Return a complete snapshot; never publish a partial poll."""
        async with self._session():
            result = {}
            for start, count in blocks:
                values = await self._read(start, count)
                result.update({start + index: raw for index, raw in enumerate(values)})
            return result

    async def update_bits(self, register: int, shift: int, width: int, value: int):
        """Preserve unrelated bits and verify the selected field after FC06."""
        if width < 1 or shift < 0 or shift + width > 16 or not 0 <= value < 1 << width:
            raise ValueError("Invalid bit field")
        async with self._session():
            current = (await self._read(register, 1))[0]
            mask = ((1 << width) - 1) << shift
            updated = (current & ~mask) | (value << shift)
            if updated != current:
                await self._request(6, register, updated)
            actual = (await self._read(register, 1))[0]
            if actual & mask != updated & mask:
                raise ModbusError("Command not confirmed by readback")
            return actual


    async def set_ventilation(self, value: int):
        """Replicate the app: register 51, then WR_APP_CONF and WR_SP in 5.

        Values 30/65 are observed device presets, not universal profile IDs.
        Do not write read-only derived flags in register 20.
        """
        if value not in (0, 30, 65, 101):
            raise ValueError("Unsupported ventilation selection")
        async with self._session():
            await self._request(6, 51, value)
            control = (await self._read(5, 1))[0]
            await self._request(6, 5, control | 0xC000)
            actual = (await self._read(51, 1))[0]
            if actual != value:
                raise ModbusError("Ventilation selection not confirmed by readback")
            return actual
