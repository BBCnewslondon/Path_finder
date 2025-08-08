"""
Distance and time calculation module.
Calculates distances and travel times between coordinates using real road networks.
"""

from typing import List, Tuple, Optional, Dict, Any
import math
import requests
import os
import time

from src.cache import RouteCache
from src.config import ORS_API_KEY, GOOGLE_API_KEY


class RoadRoutingService:
    """Base class for road routing services."""

    def get_route_info(self, origin: Tuple[float, float],
                      destination: Tuple[float, float]) -> Optional[Dict[str, Any]]:
        """Get route information between two points."""
        raise NotImplementedError


class OpenRouteService(RoadRoutingService):
    """OpenRouteService routing (free with API key)."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or ORS_API_KEY
        self.base_url = "https://api.openrouteservice.org/v2/directions/driving-car"

    def get_route_info(self, origin: Tuple[float, float],
                      destination: Tuple[float, float]) -> Optional[Dict[str, Any]]:
        """Get route info from OpenRouteService."""
        if not self.api_key:
            return None

        try:
            headers = {
                'Authorization': self.api_key,
                'Content-Type': 'application/json'
            }

            params = {
                'start': f"{origin[1]},{origin[0]}",  # lon,lat format
                'end': f"{destination[1]},{destination[0]}"
            }

            response = requests.get(self.base_url, headers=headers, params=params, timeout=10)

            if response.status_code == 200:
                data = response.json()
                if data.get('features'):
                    route = data['features'][0]
                    properties = route['properties']
                    summary = properties['summary']

                    return {
                        'distance_km': summary['distance'] / 1000.0,
                        'duration_hours': summary['duration'] / 3600.0,
                        'service': 'OpenRouteService'
                    }

            return None

        except Exception as e:
            print(f"OpenRouteService error: {e}")
            return None


class GoogleMapsRouting(RoadRoutingService):
    """Google Maps routing service."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or GOOGLE_API_KEY
        self.base_url = "https://maps.googleapis.com/maps/api/directions/json"

    def get_route_info(self, origin: Tuple[float, float],
                      destination: Tuple[float, float]) -> Optional[Dict[str, Any]]:
        """Get route info from Google Maps."""
        if not self.api_key:
            return None

        try:
            params = {
                'origin': f"{origin[0]},{origin[1]}",
                'destination': f"{destination[0]},{destination[1]}",
                'mode': 'driving',
                'key': self.api_key
            }

            response = requests.get(self.base_url, params=params, timeout=10)

            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'OK' and data.get('routes'):
                    route = data['routes'][0]
                    leg = route['legs'][0]

                    return {
                        'distance_km': leg['distance']['value'] / 1000.0,
                        'duration_hours': leg['duration']['value'] / 3600.0,
                        'service': 'Google Maps'
                    }

            return None

        except Exception as e:
            print(f"Google Maps routing error: {e}")
            return None


class OSRMRouting(RoadRoutingService):
    """OSRM (Open Source Routing Machine) - Free, no API key needed."""

    def __init__(self, server_url: str = "http://router.project-osrm.org"):
        self.server_url = server_url

    def get_route_info(self, origin: Tuple[float, float],
                      destination: Tuple[float, float]) -> Optional[Dict[str, Any]]:
        """Get route info from OSRM."""
        try:
            # OSRM uses lon,lat format
            url = f"{self.server_url}/route/v1/driving/{origin[1]},{origin[0]};{destination[1]},{destination[0]}"
            params = {
                'overview': 'false',
                'alternatives': 'false',
                'steps': 'false'
            }

            response = requests.get(url, params=params, timeout=10)

            if response.status_code == 200:
                data = response.json()
                if data.get('code') == 'Ok' and data.get('routes'):
                    route = data['routes'][0]

                    return {
                        'distance_km': route['distance'] / 1000.0,
                        'duration_hours': route['duration'] / 3600.0,
                        'service': 'OSRM'
                    }

            return None

        except Exception as e:
            print(f"OSRM routing error: {e}")
            return None

    def get_distance_duration_matrix(self, coordinates: List[Tuple[float, float]]) -> Optional[Tuple[List[List[float]], List[List[float]]]]:
        """Get distance and duration matrices from OSRM Table service."""
        if not coordinates or len(coordinates) < 2:
            return None

        try:
            # Format coordinates for OSRM URL: lon,lat;lon,lat;...
            coords_str = ";".join([f"{lon},{lat}" for lat, lon in coordinates])
            url = f"{self.server_url}/table/v1/driving/{coords_str}"
            params = {
                'annotations': 'distance,duration'
            }

            response = requests.get(url, params=params, timeout=30)

            if response.status_code == 200:
                data = response.json()
                if data.get('code') == 'Ok':
                    distances_m = data.get('distances')
                    durations_s = data.get('durations')

                    if not distances_m or not durations_s:
                        return None

                    # Convert units: meters to km, seconds to hours
                    distances_km = [[d / 1000.0 if d is not None else float('inf') for d in row] for row in distances_m]
                    durations_h = [[t / 3600.0 if t is not None else float('inf') for t in row] for row in durations_s]

                    return distances_km, durations_h

            return None

        except Exception as e:
            print(f"OSRM matrix error: {e}")
            return None


class DistanceCalculator:
    """
    Calculates distances and travel times between coordinates.
    Supports both straight-line distances and real road-based routing.
    """

    def __init__(self, use_real_roads: bool = True, preferred_service: str = 'auto'):
        """
        Initialize distance calculator.

        Args:
            use_real_roads: Whether to use real road distances (True) or straight-line (False)
            preferred_service: Preferred routing service ('auto', 'osrm', 'google', 'openroute')
        """
        self.use_real_roads = use_real_roads
        self.preferred_service = preferred_service

        # Initialize routing services
        self.routing_services = {
            'osrm': OSRMRouting(),
            'openroute': OpenRouteService(),
            'google': GoogleMapsRouting()
        }

        # Cache for route calculations
        self.route_cache = RouteCache()
        self._in_memory_route_cache = {} # For individual route segments
        self.distance_matrix_cache = None
        self.duration_matrix_cache = None

        print(f"DistanceCalculator initialized with {len(self.routing_services)} routing services")
        if self.use_real_roads:
            print("  Using real road distances")
        else:
            print("  Using straight-line distances")

    def haversine_distance(self, coord1: Tuple[float, float],
                          coord2: Tuple[float, float]) -> float:
        """
        Calculate the great circle distance between two points on Earth.

        Args:
            coord1: (latitude, longitude) of first point
            coord2: (latitude, longitude) of second point

        Returns:
            Distance in kilometers
        """
        lat1, lon1 = coord1
        lat2, lon2 = coord2

        # Convert latitude and longitude from degrees to radians
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])

        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))

        # Radius of Earth in kilometers
        r = 6371

        return c * r

    def get_road_route_info(self, origin: Tuple[float, float],
                           destination: Tuple[float, float]) -> Optional[Dict[str, Any]]:
        """
        Get real road route information between two points.

        Args:
            origin: (latitude, longitude) of starting point
            destination: (latitude, longitude) of ending point

        Returns:
            Dictionary with distance_km, duration_hours, and service info or None
        """
        # Create cache key
        cache_key = f"{origin[0]:.6f},{origin[1]:.6f}-{destination[0]:.6f},{destination[1]:.6f}"

        if cache_key in self._in_memory_route_cache:
            return self._in_memory_route_cache[cache_key]

        # Try each routing service in a defined order
        service_order = ['osrm', 'openroute', 'google']
        active_services = [self.routing_services[s_name] for s_name in service_order if s_name in self.routing_services]

        for service in active_services:
            route_info = service.get_route_info(origin, destination)
            if route_info:
                self._in_memory_route_cache[cache_key] = route_info
                return route_info

            # Small delay between service attempts
            time.sleep(0.1)

        return None

    def calculate_distance_matrix(self, coordinates: List[Tuple[float, float]],
                                 show_progress: bool = True) -> List[List[float]]:
        """
        Calculate distance matrix between all pairs of coordinates.
        Uses OSRM table service for efficiency if available.
        """
        if self.distance_matrix_cache:
            return self.distance_matrix_cache

        n = len(coordinates)
        if n == 0:
            return []

        # Check persistent cache first
        cached_matrices = self.route_cache.get(coordinates)
        if cached_matrices:
            print("  Found route matrix in persistent cache.")
            self.distance_matrix_cache = cached_matrices['distances']
            self.duration_matrix_cache = cached_matrices['durations']
            return self.distance_matrix_cache

        # Efficient matrix calculation using OSRM
        if self.use_real_roads and 'osrm' in self.routing_services:
            print("  Attempting to use OSRM matrix service for efficiency...")
            osrm_service = self.routing_services['osrm']
            matrix_data = osrm_service.get_distance_duration_matrix(coordinates)

            if matrix_data:
                print("  Successfully calculated matrix using OSRM.")
                self.distance_matrix_cache, self.duration_matrix_cache = matrix_data
                # Save to persistent cache
                self.route_cache.set(coordinates, self.distance_matrix_cache, self.duration_matrix_cache)
                return self.distance_matrix_cache

            print("  OSRM matrix service failed, falling back to individual calculations.")

        # Fallback to calculating pair by pair
        matrix = [[0.0 for _ in range(n)] for _ in range(n)]
        total_calculations = n * (n - 1)
        current_calculation = 0

        for i in range(n):
            for j in range(n):
                if i == j:
                    continue

                current_calculation += 1
                if show_progress and total_calculations > 10:
                    print(f"  Calculating distances (fallback): {current_calculation}/{total_calculations}")

                distance = self._calculate_single_distance(coordinates[i], coordinates[j])
                matrix[i][j] = distance

        self.distance_matrix_cache = matrix
        return matrix

    def _calculate_single_distance(self, coord1: Tuple[float, float],
                                  coord2: Tuple[float, float]) -> float:
        """Calculate distance between two coordinates."""
        if self.use_real_roads:
            # Try to get real road distance
            route_info = self.get_road_route_info(coord1, coord2)
            if route_info:
                return route_info['distance_km']

            # Fallback to straight-line distance
            print(f"    Fallback to straight-line distance for {coord1} -> {coord2}")

        return self.haversine_distance(coord1, coord2)

    def get_duration_matrix(self, coordinates: List[Tuple[float, float]],
                             show_progress: bool = True) -> List[List[float]]:
        """
        Calculate or retrieve the cached duration matrix.
        """
        # If cache is available, return it
        if self.duration_matrix_cache:
            return self.duration_matrix_cache

        # If not cached, the distance matrix calculation will populate it
        print("  Duration matrix not found, calculating new matrices...")
        self.calculate_distance_matrix(coordinates, show_progress)

        # If the cache is still empty (e.g., fallback didn't run), calculate manually
        if not self.duration_matrix_cache:
             print("  Calculating duration matrix manually...")
             self.duration_matrix_cache = self._calculate_duration_matrix_manually(coordinates)

        return self.duration_matrix_cache

    def _calculate_duration_matrix_manually(self, coordinates: List[Tuple[float, float]]) -> List[List[float]]:
        """
        Calculate duration matrix manually, pair by pair.
        """
        n = len(coordinates)
        matrix = [[0.0 for _ in range(n)] for _ in range(n)]

        for i in range(n):
            for j in range(n):
                if i != j:
                    if self.use_real_roads:
                        route_info = self.get_road_route_info(coordinates[i], coordinates[j])
                        if route_info and 'duration_hours' in route_info:
                            matrix[i][j] = route_info['duration_hours']
                        else:
                            # Fallback: estimate from straight-line distance
                            distance = self.haversine_distance(coordinates[i], coordinates[j])
                            matrix[i][j] = self.estimate_travel_time(distance)
                    else:
                        distance = self.haversine_distance(coordinates[i], coordinates[j])
                        matrix[i][j] = self.estimate_travel_time(distance)

        return matrix

    def estimate_travel_time(self, distance_km: float,
                           avg_speed_kmh: float = 50.0) -> float:
        """
        Estimate travel time based on distance and average speed.

        Args:
            distance_km: Distance in kilometers
            avg_speed_kmh: Average speed in km/h (default: 50 km/h for city driving)

        Returns:
            Travel time in hours
        """
        return distance_km / avg_speed_kmh

    def calculate_total_route_distance(self, coordinates: List[Tuple[float, float]],
                                     route_order: List[int]) -> float:
        """
        Calculate total distance for a specific route order.

        Args:
            coordinates: List of all coordinates
            route_order: Order to visit coordinates (list of indices)

        Returns:
            Total distance in kilometers
        """
        total_distance = 0.0

        for i in range(len(route_order) - 1):
            current_idx = route_order[i]
            next_idx = route_order[i + 1]

            distance = self.haversine_distance(
                coordinates[current_idx],
                coordinates[next_idx]
            )
            total_distance += distance

        # Add distance back to start (if it's a round trip)
        if len(route_order) > 1:
            last_idx = route_order[-1]
            first_idx = route_order[0]
            total_distance += self.haversine_distance(
                coordinates[last_idx],
                coordinates[first_idx]
            )

        return total_distance

    def get_route_duration_matrix(self, coordinates: List[Tuple[float, float]]) -> List[List[float]]:
        """
        Calculate duration matrix between all pairs of coordinates.

        Args:
            coordinates: List of (latitude, longitude) tuples

        Returns:
            2D matrix where matrix[i][j] is travel time in hours from point i to point j
        """
        n = len(coordinates)
        matrix = [[0.0 for _ in range(n)] for _ in range(n)]

        for i in range(n):
            for j in range(n):
                if i != j:
                    if self.use_real_roads:
                        route_info = self.get_road_route_info(coordinates[i], coordinates[j])
                        if route_info:
                            matrix[i][j] = route_info['duration_hours']
                        else:
                            # Fallback: estimate from straight-line distance
                            distance = self.haversine_distance(coordinates[i], coordinates[j])
                            matrix[i][j] = self.estimate_travel_time(distance)
                    else:
                        distance = self.haversine_distance(coordinates[i], coordinates[j])
                        matrix[i][j] = self.estimate_travel_time(distance)

        return matrix
