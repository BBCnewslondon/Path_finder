"""
Unit tests for the geocoder module.
"""

import unittest
from unittest.mock import Mock, patch
import sys
import os

from src.geocoder import AddressGeocoder
from src.cache import GeocodeCache


class TestGeocodeCache(unittest.TestCase):
    """Test cases for GeocodeCache class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.cache = GeocodeCache("test_cache.json")
    
    def tearDown(self):
        """Clean up test fixtures."""
        if os.path.exists("test_cache.json"):
            os.remove("test_cache.json")
    
    def test_cache_set_and_get(self):
        """Test setting and getting cache values."""
        address = "123 Test St"
        result = {'success': True, 'lat': 40.0, 'lon': -88.0}
        
        self.cache.set(address, result)
        cached_result = self.cache.get(address)
        
        self.assertEqual(cached_result, result)
    
    def test_cache_case_insensitive(self):
        """Test that cache is case insensitive."""
        result = {'success': True, 'lat': 40.0, 'lon': -88.0}
        
        self.cache.set("Test Address", result)
        cached_result = self.cache.get("test address")
        
        self.assertEqual(cached_result, result)


class TestAddressGeocoder(unittest.TestCase):
    """Test cases for AddressGeocoder class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.geocoder = AddressGeocoder(use_cache=False)
    
    def test_geocode_empty_address(self):
        """Test geocoding empty address."""
        result = self.geocoder.geocode_address("")
        self.assertIsNone(result)
        
        result = self.geocoder.geocode_address(None)
        self.assertIsNone(result)
    
    def test_geocode_whitespace_address(self):
        """Test geocoding address with only whitespace."""
        result = self.geocoder.geocode_address("   ")
        self.assertIsNone(result)
    
    def test_geocode_successful(self):
        """Test successful geocoding with a mock."""
        geocoder = AddressGeocoder(use_cache=False)

        mock_location = Mock()
        mock_location.latitude, mock_location.longitude = 40.7128, -74.0060
        
        mock_service = Mock()
        mock_service.geocode.return_value = mock_location
        
        geocoder.geocoders = [('MockService', mock_service)]
        
        result = geocoder.geocode_address("Any Address")
        self.assertEqual(result, (40.7128, -74.0060))

    def test_geocode_failure(self):
        """Test geocoding failure with a mock."""
        geocoder = AddressGeocoder(use_cache=False)
        
        mock_service = Mock()
        mock_service.geocode.return_value = None

        geocoder.geocoders = [('MockService', mock_service)]

        result = geocoder.geocode_address("Invalid Address")
        self.assertIsNone(result)

    def test_validate_addresses(self):
        """Test address validation with a mock."""
        geocoder = AddressGeocoder(use_cache=False)

        # Create a dummy location object to be returned on success
        valid_location = Mock()
        valid_location.latitude, valid_location.longitude = 40.0, -88.0

        # Mock the geocoding service
        mock_service = Mock()
        # Set the side effect to return a location, then None, then a location
        mock_service.geocode.side_effect = [valid_location, None, valid_location]

        # Replace the real geocoders with our mock
        geocoder.geocoders = [('MockService', mock_service)]

        addresses = ["Valid Address 1", "Invalid Address", "Valid Address 2"]
        valid_addresses = geocoder.validate_addresses(addresses)

        # Check that geocode was called for all three addresses
        self.assertEqual(mock_service.geocode.call_count, 3)

        # Check that the final list is correct
        self.assertEqual(len(valid_addresses), 2)
        self.assertIn("Valid Address 1", valid_addresses)
        self.assertIn("Valid Address 2", valid_addresses)
        self.assertNotIn("Invalid Address", valid_addresses)


if __name__ == '__main__':
    unittest.main()
