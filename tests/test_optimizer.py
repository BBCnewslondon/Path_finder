"""
Unit tests for the route optimizer module.
"""

import unittest
import sys
import os

from src.route_optimizer import RouteOptimizer


class TestRouteOptimizer(unittest.TestCase):
    """Test cases for RouteOptimizer class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.optimizer = RouteOptimizer()
        
        # Sample distance matrix for 4 locations
        self.distance_matrix = [
            [0.0, 10.0, 15.0, 20.0],
            [10.0, 0.0, 35.0, 25.0],
            [15.0, 35.0, 0.0, 30.0],
            [20.0, 25.0, 30.0, 0.0]
        ]
    
    def test_single_location(self):
        """Test optimization with single location."""
        single_matrix = [[0.0]]
        route, distance = self.optimizer.optimize_route(single_matrix)
        
        self.assertEqual(route, [0])
        self.assertEqual(distance, 0.0)
    
    def test_empty_matrix(self):
        """Test optimization with empty matrix."""
        empty_matrix = []
        route, distance = self.optimizer.optimize_route(empty_matrix)
        
        self.assertEqual(route, [0])
        self.assertEqual(distance, 0.0)
    
    def test_nearest_neighbor_algorithm(self):
        """Test nearest neighbor algorithm."""
        self.optimizer.algorithm = "nearest_neighbor"
        route, distance = self.optimizer.optimize_route(self.distance_matrix)
        
        # Should return a valid route
        self.assertEqual(len(route), 4)
        self.assertEqual(route[0], 0)  # Should start at index 0
        self.assertGreater(distance, 0)
        
        # All indices should be present
        self.assertEqual(set(route), {0, 1, 2, 3})
    
    def test_two_opt_algorithm(self):
        """Test 2-opt algorithm."""
        self.optimizer.algorithm = "2opt"
        route, distance = self.optimizer.optimize_route(self.distance_matrix)
        
        self.assertEqual(len(route), 4)
        self.assertEqual(route[0], 0)
        self.assertGreater(distance, 0)
        self.assertEqual(set(route), {0, 1, 2, 3})
    
    def test_genetic_algorithm(self):
        """Test genetic algorithm."""
        self.optimizer.algorithm = "genetic"
        route, distance = self.optimizer.optimize_route(self.distance_matrix)
        
        self.assertEqual(len(route), 4)
        self.assertEqual(route[0], 0)
        self.assertGreater(distance, 0)
        self.assertEqual(set(route), {0, 1, 2, 3})
    
    def test_invalid_algorithm(self):
        """Test invalid algorithm raises error."""
        self.optimizer.algorithm = "invalid_algorithm"
        
        with self.assertRaises(ValueError):
            self.optimizer.optimize_route(self.distance_matrix)
    
    def test_calculate_route_distance_round_trip(self):
        """Test round trip route distance calculation."""
        route = [0, 1, 2, 3]
        distance = self.optimizer._calculate_route_distance(route, self.distance_matrix, is_round_trip=True)
        
        # Distance should be: 0->1 (10) + 1->2 (35) + 2->3 (30) + 3->0 (20) = 95
        expected_distance = 10.0 + 35.0 + 30.0 + 20.0
        self.assertEqual(distance, expected_distance)

    def test_calculate_route_distance_open_tour(self):
        """Test open tour route distance calculation."""
        route = [0, 1, 3, 2] # A possible open route from 0 to 2
        distance = self.optimizer._calculate_route_distance(route, self.distance_matrix, is_round_trip=False)

        # Distance should be: 0->1 (10) + 1->3 (25) + 3->2 (30) = 65
        expected_distance = 10.0 + 25.0 + 30.0
        self.assertEqual(distance, expected_distance)
    
    def test_different_start_index(self):
        """Test optimization with different start index."""
        route, distance = self.optimizer.optimize_route(self.distance_matrix, start_index=2)
        
        self.assertEqual(route[0], 2)  # Should start at index 2
        self.assertEqual(len(route), 4)
        self.assertEqual(set(route), {0, 1, 2, 3})
    
    def test_two_location_optimization(self):
        """Test optimization with only two locations."""
        two_location_matrix = [
            [0.0, 10.0],
            [10.0, 0.0]
        ]
        
        route, distance = self.optimizer.optimize_route(two_location_matrix)
        
        self.assertEqual(len(route), 2)
        self.assertEqual(route[0], 0)
        self.assertEqual(distance, 20.0)  # 0->1 (10) + 1->0 (10) = 20


if __name__ == '__main__':
    unittest.main()
