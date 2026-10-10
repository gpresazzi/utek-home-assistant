"""Operating state checks using hardware observations."""
import importlib.util
from pathlib import Path
import unittest

path = Path(__file__).parents[1] / "custom_components/air_touch/state.py"
spec = importlib.util.spec_from_file_location("air_touch_state", path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class StateTests(unittest.TestCase):
    def test_hardware_samples(self):
        for data, expected in (
            ({20: 70, 51: 101}, "Programmazione oraria"),
            ({20: 70, 51: 65}, "Manuale"),
            ({20: 70, 51: 30}, "Manuale"),
            ({20: 102, 51: 0}, "Spenta"),
        ):
            with self.subTest(data=data):
                self.assertEqual(module.ventilation_mode(data), expected)

    def test_off_flag_has_priority(self):
        self.assertEqual(module.ventilation_mode({20: 102, 51: 65}), "Spenta")

    def test_unknown_code_not_guessed(self):
        self.assertEqual(module.ventilation_mode({20: 70, 51: 102}), "Non riconosciuta")

    def test_missing_data(self):
        self.assertIsNone(module.ventilation_mode({20: 70}))
