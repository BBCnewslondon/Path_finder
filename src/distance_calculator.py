"""
Distance and time calculation module.
Calculates distances and travel times between coordinates.
"""

from typing import List, Tuple, Optional
import math
import requests
import os
from dotenv import load_dotenv

load_dotenv()


class DistanceCalculator:
    """
    Calculates distances and travel times between coordinates.
    Supports both straight-line distances and road-based routing.
    """
    
    def __init__(self, use_real_roads: bool = False):
        """
        Initialize distance calculator.
        
        Args:
            use_real_roads: Whether to use real road distances (requires API key)
        """
        self.use_real_roads = use_real_roads
        self.google_api_key = os.getenv('GOOGLE_MAPS_API_KEY')
        
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
    
    def calculate_distance_matrix(self, coordinates: List[Tuple[float, float]]) -> List[List[float]]:
        """
        Calculate distance matrix between all pairs of coordinates.
        
        Args:
            coordinates: List of (latitude, longitude) tuples
            
        Returns:
            2D matrix where matrix[i][j] is distance from point i to point j
        """
        n = len(coordinates)
        matrix = [[0.0 for _ in range(n)] for _ in range(n)]
        
        for i in range(n):
            for j in range(n):
                if i != j:
                    if self.use_real_roads and self.google_api_key:
                        # Try to get real road distance
                        distance = self._get_road_distance(coordinates[i], coordinates[j])
                        if distance is not None:
                            matrix[i][j] = distance
                        else:
                            # Fallback to straight-line distance
                            matrix[i][j] = self.haversine_distance(coordinates[i], coordinates[j])
                    else:
                        matrix[i][j] = self.haversine_distance(coordinates[i], coordinates[j])
        
        return matrix
    
    def _get_road_distance(self, origin: Tuple[float, float], 
                          destination: Tuple[float, float]) -> Optional[float]:
        """
        Get real road distance using Google Maps API.
        
        Args:
            origin: (latitude, longitude) of starting point
            destination: (latitude, longitude) of ending point
            
        Returns:
            Distance in kilometers or None if API call fails
        """
        if not self.google_api_key:
            return None
        
        try:
            url = "https://maps.googleapis.com/maps/api/distancematrix/json"
            params = {
                'origins': f"{origin[0]},{origin[1]}",
                'destinations': f"{destination[0]},{destination[1]}",
                'units': 'metric',
                'mode': 'driving',
                'key': self.google_api_key
            }
            
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            
            if data['status'] == 'OK':
                element = data['rows'][0]['elements'][0]
                if element['status'] == 'OK':
                    # Convert meters to kilometers
                    return element['distance']['value'] / 1000.0
            
            return None
            
        except Exception as e:
            print(f"Error getting road distance: {e}")
            return None
    
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
