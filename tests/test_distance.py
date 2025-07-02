"""
Unit tests for the distance calculator module.
"""

import unittest
import math
import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.distance_calculator import DistanceCalculator


class TestDistanceCalculator(unittest.TestCase):
    """Test cases for DistanceCalculator class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.calculator = DistanceCalculator()
    
    def test_haversine_distance_same_point(self):
        """Test haversine distance for same point."""
        coord = (40.7128, -74.0060)  # New York
        distance = self.calculator.haversine_distance(coord, coord)
        
        self.assertAlmostEqual(distance, 0.0, places=6)
    
    def test_haversine_distance_known_cities(self):
        """Test haversine distance between known cities."""
        # New York to Los Angeles (approximately 3944 km)
        nyc = (40.7128, -74.0060)
        la = (34.0522, -118.2437)
        
        distance = self.calculator.haversine_distance(nyc, la)
        
        # Should be approximately 3944 km (within 100 km tolerance)
        self.assertGreater(distance, 3800)
        self.assertLess(distance, 4100)
    
    def test_haversine_distance_symmetric(self):
        """Test that haversine distance is symmetric."""
        coord1 = (40.7128, -74.0060)  # New York
        coord2 = (34.0522, -118.2437)  # Los Angeles
        
        distance1 = self.calculator.haversine_distance(coord1, coord2)
        distance2 = self.calculator.haversine_distance(coord2, coord1)
        
        self.assertAlmostEqual(distance1, distance2, places=6)
    
    def test_calculate_distance_matrix(self):
        """Test distance matrix calculation."""
        coordinates = [
            (40.7128, -74.0060),  # New York
            (34.0522, -118.2437), # Los Angeles  
            (41.8781, -87.6298),  # Chicago
        ]
        
        matrix = self.calculator.calculate_distance_matrix(coordinates)
        
        # Check matrix dimensions
        self.assertEqual(len(matrix), 3)
        self.assertEqual(len(matrix[0]), 3)
        
        # Check diagonal is zero
        for i in range(3):
            self.assertAlmostEqual(matrix[i][i], 0.0, places=6)
        
        # Check symmetry
        for i in range(3):
            for j in range(3):
                self.assertAlmostEqual(matrix[i][j], matrix[j][i], places=6)
        
        # Check positive distances
        for i in range(3):
            for j in range(3):
                if i != j:
                    self.assertGreater(matrix[i][j], 0)
    
    def test_estimate_travel_time(self):
        """Test travel time estimation."""
        distance_km = 100.0
        speed_kmh = 50.0
        
        time_hours = self.calculator.estimate_travel_time(distance_km, speed_kmh)
        
        expected_time = 2.0  # 100 km / 50 km/h = 2 hours
        self.assertEqual(time_hours, expected_time)
    
    def test_estimate_travel_time_default_speed(self):
        """Test travel time estimation with default speed."""
        distance_km = 50.0
        
        time_hours = self.calculator.estimate_travel_time(distance_km)
        
        expected_time = 1.0  # 50 km / 50 km/h (default) = 1 hour
        self.assertEqual(time_hours, expected_time)
    
    def test_calculate_total_route_distance(self):
        """Test total route distance calculation."""
        coordinates = [
            (0.0, 0.0),
            (0.0, 1.0),
            (1.0, 1.0),
            (1.0, 0.0)
        ]
        
        route_order = [0, 1, 2, 3]  # Square route
        
        total_distance = self.calculator.calculate_total_route_distance(coordinates, route_order)
        
        # Should be greater than 0
        self.assertGreater(total_distance, 0)
    
    def test_single_location_route(self):
        """Test route distance with single location."""
        coordinates = [(40.7128, -74.0060)]
        route_order = [0]
        
        total_distance = self.calculator.calculate_total_route_distance(coordinates, route_order)
        
        # Single location should have zero distance
        self.assertEqual(total_distance, 0.0)
    
    def test_two_location_route(self):
        """Test route distance with two locations."""
        coordinates = [
            (40.7128, -74.0060),  # New York
            (34.0522, -118.2437)  # Los Angeles
        ]
        route_order = [0, 1]
        
        total_distance = self.calculator.calculate_total_route_distance(coordinates, route_order)
        
        # Should be twice the distance between the cities (round trip)
        one_way = self.calculator.haversine_distance(coordinates[0], coordinates[1])
        expected_total = 2 * one_way
        
        self.assertAlmostEqual(total_distance, expected_total, places=6)


if __name__ == '__main__':
    unittest.main()
