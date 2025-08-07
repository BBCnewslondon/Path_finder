"""
Integration tests for the main CLI application.
"""

import unittest
import subprocess
import os
import sys

class TestMainApp(unittest.TestCase):
    """Test cases for the main command-line application."""

    def setUp(self):
        """Set up test fixtures."""
        self.main_script = os.path.join(os.path.dirname(__file__), '..', 'main.py')
        self.sample_addresses = os.path.join(os.path.dirname(__file__), '..', 'examples', 'sample_addresses.txt')

    def test_main_help_message(self):
        """Test that running with --help exits cleanly and shows usage."""
        result = subprocess.run(
            [sys.executable, self.main_script, '--help'],
            capture_output=True, text=True, check=False
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("usage: main.py", result.stdout)
        self.assertIn("--optimize-by", result.stdout)

    def test_main_basic_run_straight_line(self):
        """Test a basic run with sample addresses and straight-line distance."""
        result = subprocess.run(
            [sys.executable, self.main_script, '--file', self.sample_addresses, '--straight-line'],
            capture_output=True, text=True, check=False
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("DELIVERY ROUTE OPTIMIZATION RESULTS", result.stdout)
        self.assertIn("Total Distance:", result.stdout)

    @unittest.skipIf("CI" in os.environ, "Skipping real API call test in CI environment.")
    def test_main_basic_run_real_roads(self):
        """Test a basic run with sample addresses and real roads. This test makes a live API call."""
        result = subprocess.run(
            [sys.executable, self.main_script, '--file', self.sample_addresses, '--roads'],
            capture_output=True, text=True, check=False
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("DELIVERY ROUTE OPTIMIZATION RESULTS", result.stdout)
        self.assertIn("Attempting to use OSRM matrix service", result.stdout)

    def test_main_invalid_argument(self):
        """Test that an invalid argument causes a non-zero exit code."""
        result = subprocess.run(
            [sys.executable, self.main_script, '--file', self.sample_addresses, '--invalid-argument'],
            capture_output=True, text=True, check=False
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unrecognized arguments", result.stderr)

    def tearDown(self):
        """Clean up after tests."""
        if os.path.exists("route_cache.json"):
            os.remove("route_cache.json")
        if os.path.exists("geocode_cache.json"):
            os.remove("geocode_cache.json")


if __name__ == '__main__':
    unittest.main()
