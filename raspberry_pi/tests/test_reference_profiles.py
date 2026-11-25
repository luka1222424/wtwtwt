"""Regression checks for the six-day reference configuration."""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[2]

class ReferenceProfileTests(unittest.TestCase):
    def test_baseline_profile(self):
        profile = (ROOT / "esp32/sdkconfig.baseline.defaults").read_text()
        header = (ROOT / "esp32/main/measurement_output.h").read_text()
        self.assertIn("CONFIG_SMART_PLANT_MODE_BASELINE=y", profile)
        self.assertRegex(header, r"SMART_PLANT_BASELINE_INTERVAL_MS\s+20000U")
        runner = (ROOT / "raspberry_pi/run_test.sh").read_text()
        self.assertIn("CAMERA_INTERVAL_SECONDS:-1800", runner)

    def test_optimized_profile_and_kconfig(self):
        profile = (ROOT / "esp32/sdkconfig.optimized.defaults").read_text()
        kconfig = (ROOT / "esp32/main/Kconfig.projbuild").read_text()
        self.assertIn("CONFIG_SMART_PLANT_MODE_OPTIMIZED=y", profile)
        for key, value in (("MIN_INTERVAL_S", 20), ("PI_NORMAL_CYCLES", 90), ("PI_WAKE_CYCLES", 360)):
            self.assertRegex(profile, rf"(?m)^CONFIG_SMART_PLANT_OPTIMIZED_{key}={value}$")
            section = re.search(rf"(?ms)^config SMART_PLANT_OPTIMIZED_{key}\n(.*?)(?=^config |\Z)", kconfig)
            self.assertIsNotNone(section)
            self.assertRegex(section.group(1), rf"(?m)^\s+default {value}$")

    def test_optimized_halt_entrypoints(self):
        launcher = (ROOT / "raspberry_pi/run_optimized.sh").read_text()
        service = (ROOT / "raspberry_pi/systemd/smartplant-optimized.service").read_text()
        self.assertNotIn("PI_SHUTDOWN_AFTER_INITIAL_CYCLE", launcher)
        direct = (ROOT / "raspberry_pi/run_test.sh").read_text()
        self.assertIn('set -- --shutdown-after-initial-cycle "$@"', direct)
        runner = (ROOT / "raspberry_pi/smartplant_pi/experiment_runner.py").read_text()
        self.assertIn('if args.mode == "optimized":\n        args.shutdown_after_initial_cycle = True', runner)
        self.assertIn("--shutdown-after-initial-cycle", launcher)
        self.assertIn("--shutdown-after-initial-cycle", service)
        self.assertIn("ConditionPathExists=!/boot/firmware/smartplant-maintenance", service)

if __name__ == "__main__":
    unittest.main()
