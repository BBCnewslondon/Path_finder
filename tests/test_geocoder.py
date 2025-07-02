"""
Unit tests for the geocoder module.
"""

import unittest
from unittest.mock import Mock, patch
import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.geocoder import AddressGeocoder, GeocodeCache


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
    
    @patch('src.geocoder.Nominatim')
    def test_geocode_successful(self, mock_nominatim):
        """Test successful geocoding."""
        # Mock the geocoder response
        mock_location = Mock()
        mock_location.latitude = 40.7128
        mock_location.longitude = -74.0060
        mock_location.address = "New York, NY"
        
        mock_geocoder_instance = Mock()
        mock_geocoder_instance.geocode.return_value = mock_location
        mock_nominatim.return_value = mock_geocoder_instance
        
        geocoder = AddressGeocoder(use_cache=False)
        result = geocoder.geocode_address("New York, NY")
        
        self.assertIsNotNone(result)
        self.assertEqual(result, (40.7128, -74.0060))
    
    @patch('src.geocoder.Nominatim')
    def test_geocode_failure(self, mock_nominatim):
        """Test geocoding failure."""
        mock_geocoder_instance = Mock()
        mock_geocoder_instance.geocode.return_value = None
        mock_nominatim.return_value = mock_geocoder_instance
        
        geocoder = AddressGeocoder(use_cache=False)
        result = geocoder.geocode_address("Invalid Address")
        
        self.assertIsNone(result)
    
    def test_validate_addresses(self):
        """Test address validation."""
        # Mock the geocode_address method
        with patch.object(self.geocoder, 'geocode_address') as mock_geocode:
            mock_geocode.side_effect = lambda addr: (40.0, -88.0) if "valid" in addr.lower() else None
            
            addresses = ["Valid Address 1", "Invalid Address", "Valid Address 2"]
            valid_addresses = self.geocoder.validate_addresses(addresses)
            
            self.assertEqual(len(valid_addresses), 2)
            self.assertIn("Valid Address 1", valid_addresses)
            self.assertIn("Valid Address 2", valid_addresses)
            self.assertNotIn("Invalid Address", valid_addresses)


if __name__ == '__main__':
    unittest.main()
