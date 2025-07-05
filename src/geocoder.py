"""
Geocoding module for converting addresses to coordinates.
Handles address validation and coordinate lookup using multiple services.
"""

from typing import Dict, List, Optional, Tuple
import time
import json
import os
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderUnavailable
import requests
from dotenv import load_dotenv

load_dotenv()


class GeocodeCache:
    """Simple file-based cache for geocoding results."""
    
    def __init__(self, cache_file: str = "geocode_cache.json"):
        self.cache_file = cache_file
        self.cache = self._load_cache()
    
    def _load_cache(self) -> Dict[str, Dict]:
        """Load cache from file."""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        return {}
    
    def _save_cache(self) -> None:
        """Save cache to file."""
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f, indent=2)
        except IOError:
            pass
    
    def get(self, address: str) -> Optional[Dict]:
        """Get cached result for address."""
        return self.cache.get(address.lower())
    
    def set(self, address: str, result: Dict) -> None:
        """Cache result for address."""
        self.cache[address.lower()] = result
        self._save_cache()


class AddressGeocoder:
    """
    Geocodes addresses to coordinates using multiple services.
    Implements fallback geocoding services and caching for robust operation.
    """
    
    def __init__(self, user_agent: str = "DeliveryRouteOptimizer", 
                 timeout: int = 10, use_cache: bool = True):
        """
        Initialize geocoder with multiple services.
        
        Args:
            user_agent: User agent string for API requests
            timeout: Request timeout in seconds
            use_cache: Whether to use geocoding cache
        """
        self.timeout = timeout
        self.cache = GeocodeCache() if use_cache else None
        
        # Initialize multiple geocoding services
        self.geocoders = []
        
        # Primary: Nominatim (OpenStreetMap) - Free and reliable
        self.geocoders.append(('Nominatim', Nominatim(user_agent=user_agent)))
        
        # Secondary: Google (if API key available)
        google_api_key = os.getenv('GOOGLE_MAPS_API_KEY')
        if google_api_key:
            try:
                from geopy.geocoders import GoogleV3
                self.geocoders.append(('Google', GoogleV3(api_key=google_api_key)))
            except ImportError:
                pass
        
        # Tertiary: ArcGIS (free, no API key needed)
        try:
            from geopy.geocoders import ArcGIS
            self.geocoders.append(('ArcGIS', ArcGIS()))
        except ImportError:
            pass
    
    def geocode_address(self, address: str) -> Optional[Tuple[float, float]]:
        """
        Convert an address to latitude, longitude coordinates using multiple services.
        
        Args:
            address: Street address string
            
        Returns:
            Tuple of (latitude, longitude) or None if geocoding fails
        """
        if not address or not address.strip():
            return None
        
        address = address.strip()
        
        # Check cache first
        if self.cache:
            cached_result = self.cache.get(address)
            if cached_result:
                if cached_result.get('success'):
                    return (cached_result['lat'], cached_result['lon'])
                else:
                    return None
        
        # Try each geocoding service
        for service_name, geocoder in self.geocoders:
            try:
                # Add small delay to respect rate limits
                time.sleep(0.1)
                
                location = geocoder.geocode(address)
                
                if location:
                    result = {
                        'success': True,
                        'lat': location.latitude,
                        'lon': location.longitude,
                        'full_address': location.address,
                        'service_used': service_name
                    }
                    
                    if self.cache:
                        self.cache.set(address, result)
                    
                    return (location.latitude, location.longitude)
                    
            except (GeocoderTimedOut, GeocoderUnavailable) as e:
                print(f"  {service_name} geocoding timeout/unavailable for '{address}': {e}")
                continue
            except Exception as e:
                print(f"  {service_name} geocoding error for '{address}': {e}")
                continue
        
        # Cache negative results to avoid repeated failures
        if self.cache:
            self.cache.set(address, {'success': False})
        
        return None
    
    def geocode_addresses(self, addresses: List[str]) -> Dict[str, Optional[Tuple[float, float]]]:
        """
        Geocode multiple addresses.
        
        Args:
            addresses: List of address strings
            
        Returns:
            Dictionary mapping addresses to coordinates (or None if failed)
        """
        results = {}
        
        for i, address in enumerate(addresses):
            print(f"Geocoding address {i+1}/{len(addresses)}: {address}")
            coords = self.geocode_address(address)
            results[address] = coords
            
            if coords is None:
                print(f"  Warning: Could not geocode '{address}'")
            else:
                print(f"  Success: {coords[0]:.6f}, {coords[1]:.6f}")
        
        return results
    
    def validate_addresses(self, addresses: List[str]) -> List[str]:
        """
        Validate a list of addresses, returning only those that can be geocoded.
        
        Args:
            addresses: List of address strings
            
        Returns:
            List of valid addresses
        """
        valid_addresses = []
        
        for address in addresses:
            if self.geocode_address(address) is not None:
                valid_addresses.append(address)
            else:
                print(f"Skipping invalid address: {address}")
        
        return valid_addresses
