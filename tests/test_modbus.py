"""Protocol checks independent from a Home Assistant installation."""

import asyncio
import importlib.util
from pathlib import Path
import struct
import unittest
from unittest.mock import AsyncMock, patch

SOURCE = Path(__file__).parents[1] / "custom_components/air_touch/modbus.py"
spec = importlib.util.spec_from_file_location("air_touch_modbus", SOURCE)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class FakeWriter:
    def __init__(self):
        self.messages = []
        self.closed = False

    def write(self, data):
        self.messages.append(data)

    async def drain(self):
        pass

    def is_closing(self):
        return self.closed

    def close(self):
        self.closed = True

    async def wait_closed(self):
        pass


def frame(transaction, pdu, unit=1, protocol=0):
    return struct.pack(">HHHB", transaction, protocol, len(pdu) + 1, unit) + pdu


class ProtocolTests(unittest.IsolatedAsyncioTestCase):
    def setup_client(self, data):
        reader = asyncio.StreamReader()
        reader.feed_data(data)
        reader.feed_eof()
        writer = FakeWriter()
        client = module.AirTouchClient("test.invalid")
        client._reader, client._writer = reader, writer
        return client, writer

    async def test_read_address_and_unsigned_values(self):
        client, writer = self.setup_client(frame(1, bytes.fromhex("0304000affff")))
        values = await client.read_blocks(((81, 2),))
        self.assertEqual(values, {81: 10, 82: 65535})
        self.assertEqual(writer.messages, [bytes.fromhex("000100000006010300500002")])

    async def test_read_modify_write_preserves_other_bits(self):
        initial = 0xA5F1
        expected = (initial & ~0xC) | 8
        wire = frame(1, struct.pack(">BBH", 3, 2, initial))
        wire += frame(2, struct.pack(">BHH", 6, 19, expected))
        wire += frame(3, struct.pack(">BBH", 3, 2, expected))
        client, writer = self.setup_client(wire)
        self.assertEqual(await client.update_bits(20, 2, 2, 2), expected)
        self.assertEqual(writer.messages[1][7:], struct.pack(">BHH", 6, 19, expected))
        self.assertEqual(len(writer.messages), 3)

    async def test_no_write_for_unchanged_mode(self):
        wire = frame(1, bytes.fromhex("03020008")) + frame(2, bytes.fromhex("03020008"))
        client, writer = self.setup_client(wire)
        await client.update_bits(20, 2, 2, 2)
        self.assertTrue(all(packet[7] == 3 for packet in writer.messages))

    async def test_wrong_header_closes_connection(self):
        for wire in (frame(2, b"\x03\x02\x00\x00"),
                     frame(1, b"\x03\x02\x00\x00", unit=2),
                     frame(1, b"\x03\x02\x00\x00", protocol=1)):
            client, writer = self.setup_client(wire)
            with self.assertRaises(module.ModbusError):
                await client.read_blocks(((20, 1),))
            self.assertTrue(writer.closed)

    async def test_modbus_exception(self):
        client, writer = self.setup_client(frame(1, b"\x83\x02"))
        with self.assertRaisesRegex(module.ModbusError, "exception 2"):
            await client.read_blocks(((20, 1),))
        self.assertTrue(writer.closed)

    async def test_wrong_byte_count_and_truncated_response(self):
        for wire in (frame(1, b"\x03\x01\x00"), frame(1, b"\x03\x02\x00\x00")[:-1]):
            client, writer = self.setup_client(wire)
            with self.assertRaises(module.ModbusError):
                await client.read_blocks(((20, 1),))
            self.assertTrue(writer.closed)

    async def test_write_echo_and_readback_mismatch(self):
        initial = frame(1, b"\x03\x02\x00\x00")
        for tail in (frame(2, struct.pack(">BHH", 6, 19, 9)),
                     frame(2, struct.pack(">BHH", 6, 19, 8)) +
                     frame(3, b"\x03\x02\x00\x00")):
            client, writer = self.setup_client(initial + tail)
            with self.assertRaises(module.ModbusError):
                await client.update_bits(20, 2, 2, 2)
            self.assertEqual(sum(packet[7] == 6 for packet in writer.messages), 1)

    async def test_concurrent_fields_are_serialized(self):
        wire = frame(1, b"\x03\x02\x00\x00")
        wire += frame(2, struct.pack(">BHH", 6, 19, 1))
        wire += frame(3, b"\x03\x02\x00\x01")
        wire += frame(4, b"\x03\x02\x00\x01")
        wire += frame(5, struct.pack(">BHH", 6, 19, 9))
        wire += frame(6, b"\x03\x02\x00\x09")
        client, writer = self.setup_client(wire[:34])
        second_reader = asyncio.StreamReader()
        second_reader.feed_data(wire[34:])
        second_reader.feed_eof()
        second_writer = FakeWriter()
        with patch.object(module.asyncio, "open_connection", AsyncMock(
            return_value=(second_reader, second_writer)
        )):
            await asyncio.gather(client.update_bits(20, 0, 2, 1), client.update_bits(20, 2, 2, 2))
        self.assertEqual([packet[7] for packet in writer.messages + second_writer.messages],
                         [3, 6, 3, 3, 6, 3])
        self.assertTrue(writer.closed)
        self.assertTrue(second_writer.closed)

    async def test_reconnect_after_failure(self):
        client, writer = self.setup_client(frame(1, b"\x83\x02"))
        with self.assertRaises(module.ModbusError):
            await client.read_blocks(((20, 1),))
        reader = asyncio.StreamReader()
        reader.feed_data(frame(2, b"\x03\x02\x00\x05"))
        with patch.object(module.asyncio, "open_connection", AsyncMock(return_value=(reader, FakeWriter()))):
            self.assertEqual(await client.read_blocks(((20, 1),)), {20: 5})

    async def test_timeout_closes_and_does_not_retry(self):
        client, writer = self.setup_client(b"")
        client._reader = asyncio.StreamReader()
        client.timeout = 0.01
        with self.assertRaises(module.ModbusError):
            await client.read_blocks(((20, 1),))
        self.assertTrue(writer.closed)
        self.assertEqual(len(writer.messages), 1)

    async def test_invalid_input_never_sends(self):
        client, writer = self.setup_client(b"")
        with self.assertRaises(ValueError):
            await client.update_bits(20, 15, 2, 1)
        with self.assertRaises(ValueError):
            await client.read_blocks(((81, 126),))
        self.assertEqual(writer.messages, [])


    async def test_ventilation_sequence_and_preserved_control_bits(self):
        for selection in (0, 30, 65, 101):
            initial = 0x0006
            saved = initial | 0xC000
            wire = frame(1, struct.pack(">BHH", 6, 50, selection))
            wire += frame(2, struct.pack(">BBH", 3, 2, initial))
            wire += frame(3, struct.pack(">BHH", 6, 4, saved))
            wire += frame(4, struct.pack(">BBH", 3, 2, selection))
            client, writer = self.setup_client(wire)
            self.assertEqual(await client.set_ventilation(selection), selection)
            self.assertEqual([p[7] for p in writer.messages], [6, 3, 6, 3])
            self.assertEqual(writer.messages[2][7:], struct.pack(">BHH", 6, 4, saved))

    async def test_ventilation_commit_failure_does_not_retry(self):
        wire = frame(1, struct.pack(">BHH", 6, 50, 101))
        wire += frame(2, bytes.fromhex("03020006"))
        wire += frame(3, bytes.fromhex("8602"))
        client, writer = self.setup_client(wire)
        with self.assertRaises(module.ModbusError):
            await client.set_ventilation(101)
        self.assertEqual(len(writer.messages), 3)
        self.assertTrue(writer.closed)

    async def test_ventilation_readback_mismatch(self):
        wire = frame(1, struct.pack(">BHH", 6, 50, 30))
        wire += frame(2, bytes.fromhex("03020006"))
        wire += frame(3, struct.pack(">BHH", 6, 4, 0xC006))
        wire += frame(4, bytes.fromhex("03020000"))
        client, writer = self.setup_client(wire)
        with self.assertRaisesRegex(module.ModbusError, "not confirmed"):
            await client.set_ventilation(30)
        self.assertEqual(len(writer.messages), 4)

    async def test_ventilation_rejects_other_values(self):
        client, writer = self.setup_client(b"")
        with self.assertRaises(ValueError):
            await client.set_ventilation(102)
        self.assertEqual(writer.messages, [])


    async def test_successful_poll_closes_one_session_after_all_blocks(self):
        wire = frame(1, bytes.fromhex("03020046"))
        wire += frame(2, bytes.fromhex("03020065"))
        client, writer = self.setup_client(wire)
        self.assertEqual(await client.read_blocks(((20, 1), (51, 1))), {20: 70, 51: 101})
        self.assertEqual(len(writer.messages), 2)
        self.assertTrue(writer.closed)
        self.assertIsNone(client._writer)
        self.assertIsNone(client._reader)

    async def test_successful_command_closes_session(self):
        wire = frame(1, struct.pack(">BHH", 6, 50, 101))
        wire += frame(2, bytes.fromhex("03020006"))
        wire += frame(3, struct.pack(">BHH", 6, 4, 0xC006))
        wire += frame(4, bytes.fromhex("03020065"))
        client, writer = self.setup_client(wire)
        await client.set_ventilation(101)
        self.assertTrue(writer.closed)
        self.assertIsNone(client._writer)

    async def test_readback_failure_closes_session(self):
        wire = frame(1, bytes.fromhex("03020000"))
        wire += frame(2, struct.pack(">BHH", 6, 19, 8))
        wire += frame(3, bytes.fromhex("03020000"))
        client, writer = self.setup_client(wire)
        with self.assertRaises(module.ModbusError):
            await client.update_bits(20, 2, 2, 2)
        self.assertTrue(writer.closed)

    async def test_next_poll_opens_new_connection(self):
        client, first_writer = self.setup_client(frame(1, bytes.fromhex("03020046")))
        await client.read_blocks(((20, 1),))
        second_reader = asyncio.StreamReader()
        second_reader.feed_data(frame(2, bytes.fromhex("03020066")))
        second_writer = FakeWriter()
        with patch.object(module.asyncio, "open_connection", AsyncMock(
            return_value=(second_reader, second_writer)
        )) as connect:
            self.assertEqual(await client.read_blocks(((20, 1),)), {20: 102})
            connect.assert_awaited_once()
        self.assertTrue(first_writer.closed and second_writer.closed)

    async def test_cancelled_poll_releases_connection_and_lock(self):
        client, writer = self.setup_client(b"")
        client._reader = asyncio.StreamReader()
        task = asyncio.create_task(client.read_blocks(((20, 1),)))
        await asyncio.sleep(0)
        task.cancel()
        with self.assertRaises(asyncio.CancelledError):
            await task
        self.assertTrue(writer.closed)
        self.assertFalse(client._lock.locked())


if __name__ == "__main__":
    unittest.main()
