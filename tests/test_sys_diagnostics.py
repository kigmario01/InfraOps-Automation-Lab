"""
Unit tests for System Diagnostics module.
"""

import unittest
from python.diagnostics.sys_diagnostics import (
    get_cpu_info,
    get_memory_info,
    get_disk_info,
    get_uptime_seconds,
    format_duration,
    run_diagnostics,
)


class TestSysDiagnostics(unittest.TestCase):

    def test_format_duration(self):
        self.assertEqual(format_duration(0), "0m")
        self.assertEqual(format_duration(60), "1m")
        self.assertEqual(format_duration(3600), "1h 0m")
        self.assertEqual(format_duration(86400), "1d 0h 0m")
        self.assertEqual(format_duration(90061), "1d 1h 1m")

    def test_cpu_info_structure(self):
        cpu = get_cpu_info()
        self.assertIn("cores", cpu)
        self.assertIn("usage_pct", cpu)
        self.assertIsInstance(cpu["cores"], int)
        self.assertGreaterEqual(cpu["cores"], 1)
        self.assertGreaterEqual(cpu["usage_pct"], 0.0)

    def test_memory_info_structure(self):
        mem = get_memory_info()
        self.assertIn("total_mb", mem)
        self.assertIn("used_mb", mem)
        self.assertIn("free_mb", mem)
        self.assertIn("used_pct", mem)

    def test_disk_info_structure(self):
        disks = get_disk_info()
        self.assertIsInstance(disks, list)
        if disks:
            d = disks[0]
            self.assertIn("mount", d)
            self.assertIn("total_gb", d)
            self.assertIn("used_pct", d)

    def test_run_diagnostics_overall(self):
        data = run_diagnostics()
        self.assertIn("timestamp", data)
        self.assertIn("host", data)
        self.assertIn("health_status", data)
        self.assertIn(data["health_status"], ["HEALTHY", "WARNING", "CRITICAL"])


if __name__ == "__main__":
    unittest.main()
