"""
Distance and time calculation module.
Calculates distances and travel times between coordinates using real road networks.
"""

from typing import List, Tuple, Optional, Dict, Any
import math
import requests
import os
import time
from dotenv import load_dotenv

load_dotenv()


class RoadRoutingService:
    """Base class for road routing services."""
    
    def get_route_info(self, origin: Tuple[float, float], 
                      destination: Tuple[float, float]) -> Optional[Dict[str, Any]]:
        """Get route information between two points."""
        raise NotImplementedError


class OpenRouteService(RoadRoutingService):
    """OpenRouteService routing (free with API key)."""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('OPENROUTESERVICE_API_KEY')
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
        self.api_key = api_key or os.getenv('GOOGLE_MAPS_API_KEY')
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
        self.routing_services = []
        
        if preferred_service == 'auto' or preferred_service == 'osrm':
            self.routing_services.append(OSRMRouting())
        
        if preferred_service == 'auto' or preferred_service == 'openroute':
            self.routing_services.append(OpenRouteService())
        
        if preferred_service == 'auto' or preferred_service == 'google':
            self.routing_services.append(GoogleMapsRouting())
        
        # Cache for route calculations
        self.route_cache = {}
        
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
        
        if cache_key in self.route_cache:
            return self.route_cache[cache_key]
        
        # Try each routing service
        for service in self.routing_services:
            route_info = service.get_route_info(origin, destination)
            if route_info:
                self.route_cache[cache_key] = route_info
                return route_info
            
            # Small delay between service attempts
            time.sleep(0.1)
        
        return None
    
    def calculate_distance_matrix(self, coordinates: List[Tuple[float, float]], 
                                 show_progress: bool = True) -> List[List[float]]:
        """
        Calculate distance matrix between all pairs of coordinates.
        
        Args:
            coordinates: List of (latitude, longitude) tuples
            show_progress: Whether to show calculation progress
            
        Returns:
            2D matrix where matrix[i][j] is distance from point i to point j
        """
        n = len(coordinates)
        matrix = [[0.0 for _ in range(n)] for _ in range(n)]
        
        total_calculations = n * (n - 1) // 2  # Only need upper triangle
        current_calculation = 0
        
        for i in range(n):
            for j in range(i + 1, n):  # Only calculate upper triangle
                current_calculation += 1
                
                if show_progress and total_calculations > 10:
                    print(f"  Calculating distances: {current_calculation}/{total_calculations}")
                
                distance = self._calculate_single_distance(coordinates[i], coordinates[j])
                matrix[i][j] = distance
                matrix[j][i] = distance  # Symmetric matrix
        
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
