"""
Caching mechanisms for geocoding and routing data.
"""

import json
import os
import hashlib
from typing import Dict, Optional, List, Tuple


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


class RouteCache:
    """File-based cache for distance and duration matrices."""

    def __init__(self, cache_file: str = "route_cache.json"):
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

    def _generate_key(self, coordinates: List[Tuple[float, float]]) -> str:
        """Generate a stable hash key from a list of coordinates."""
        # Sort coordinates to ensure order doesn't matter
        sorted_coords = sorted(coordinates)
        # Create a canonical string representation
        coords_str = json.dumps(sorted_coords)
        # Hash the string to create a key
        return hashlib.sha256(coords_str.encode('utf-8')).hexdigest()

    def get(self, coordinates: List[Tuple[float, float]]) -> Optional[Dict[str, List[List[float]]]]:
        """Get cached matrices for a set of coordinates."""
        key = self._generate_key(coordinates)
        return self.cache.get(key)

    def set(self, coordinates: List[Tuple[float, float]],
            distance_matrix: List[List[float]],
            duration_matrix: List[List[float]]) -> None:
        """Cache distance and duration matrices."""
        key = self._generate_key(coordinates)
        self.cache[key] = {
            'distances': distance_matrix,
            'durations': duration_matrix
        }
        self._save_cache()
