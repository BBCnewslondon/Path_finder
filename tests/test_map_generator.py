"""
Unit tests for the map generator module.
"""

import unittest
from unittest.mock import patch, MagicMock
import os
import sys

from src.map_generator import MapGenerator


class TestMapGenerator(unittest.TestCase):
    """Test cases for MapGenerator class."""

    def setUp(self):
        """Set up test fixtures."""
        self.map_generator = MapGenerator(use_real_roads=False)
        self.addresses = ["Address 1", "Address 2", "Address 3"]
        self.coordinates = [(40.7128, -74.0060), (34.0522, -118.2437), (41.8781, -87.6298)]
        self.route_order = [0, 2, 1]
        self.output_file = "test_map.html"

    def tearDown(self):
        """Clean up after tests."""
        if os.path.exists(self.output_file):
            os.remove(self.output_file)

    def test_create_route_map_creates_file(self):
        """Test that a map file is created."""
        self.map_generator.create_route_map(self.addresses, self.coordinates, self.route_order, self.output_file)
        self.assertTrue(os.path.exists(self.output_file))
        # Check that file is not empty
        self.assertGreater(os.path.getsize(self.output_file), 0)

    @patch('src.map_generator.folium')
    def test_create_route_map_folium_calls(self, mock_folium):
        """Test that folium is called with correct parameters."""
        # Mock the folium objects
        mock_map_instance = MagicMock()
        mock_folium.Map.return_value = mock_map_instance

        self.map_generator.create_route_map(self.addresses, self.coordinates, self.route_order, self.output_file, use_real_roads=False)

        # Check that Map is created once
        mock_folium.Map.assert_called_once()

        # Check that CircleMarker is now used instead of Marker
        self.assertEqual(mock_folium.CircleMarker.call_count, len(self.coordinates))

        # Check that a PolyLine is added for the route
        mock_folium.PolyLine.assert_called_once()

        # Check that the map is saved
        mock_map_instance.save.assert_called_once_with(self.output_file)

    @patch('src.map_generator.OSRMRouteService.get_route_geometry')
    def test_real_road_routing_calls(self, mock_get_geometry):
        """Test that the route geometry service is called for real road maps."""
        # Mock the geometry service to return a simple path
        mock_get_geometry.return_value = [ (40.7, -74.0), (40.8, -74.1) ]

        map_gen_real = MapGenerator(use_real_roads=True)
        map_gen_real.create_route_map(self.addresses, self.coordinates, self.route_order, self.output_file)

        # The number of calls should be equal to the number of legs in the route (stops - 1)
        self.assertEqual(mock_get_geometry.call_count, len(self.route_order) - 1)


if __name__ == '__main__':
    unittest.main()
