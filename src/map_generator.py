"""
Map generation module for visualizing optimized routes.
Creates interactive maps showing delivery routes with real road paths.
"""

from typing import List, Tuple, Optional, Dict, Any
import folium
import os
import requests
import polyline  # For decoding route polylines
from dotenv import load_dotenv

load_dotenv()


class RoadRouteService:
    """Service for fetching detailed road routes for visualization."""
    
    def get_route_geometry(self, origin: Tuple[float, float], 
                          destination: Tuple[float, float]) -> Optional[List[Tuple[float, float]]]:
        """Get the actual road route geometry between two points."""
        raise NotImplementedError


class OSRMRouteService(RoadRouteService):
    """OSRM service for fetching route geometry."""
    
    def __init__(self, server_url: str = "http://router.project-osrm.org"):
        self.server_url = server_url
    
    def get_route_geometry(self, origin: Tuple[float, float], 
                          destination: Tuple[float, float]) -> Optional[List[Tuple[float, float]]]:
        """Get route geometry from OSRM."""
        try:
            # OSRM uses lon,lat format
            url = f"{self.server_url}/route/v1/driving/{origin[1]},{origin[0]};{destination[1]},{destination[0]}"
            params = {
                'overview': 'full',
                'geometries': 'polyline',
                'alternatives': 'false',
                'steps': 'false'
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('code') == 'Ok' and data.get('routes'):
                    route = data['routes'][0]
                    encoded_polyline = route['geometry']
                    
                    # Decode polyline to get coordinates
                    try:
                        import polyline as pl
                        coordinates = pl.decode(encoded_polyline)
                        return [(lat, lon) for lat, lon in coordinates]
                    except ImportError:
                        # Fallback to straight line if polyline package not available
                        return [origin, destination]
            
            return None
            
        except Exception as e:
            print(f"OSRM route geometry error: {e}")
            return None


class GoogleMapsRouteService(RoadRouteService):
    """Google Maps service for fetching route geometry."""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('GOOGLE_MAPS_API_KEY')
        self.base_url = "https://maps.googleapis.com/maps/api/directions/json"
    
    def get_route_geometry(self, origin: Tuple[float, float], 
                          destination: Tuple[float, float]) -> Optional[List[Tuple[float, float]]]:
        """Get route geometry from Google Maps."""
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
                    
                    # Extract all points from all legs and steps
                    coordinates = []
                    for leg in route['legs']:
                        for step in leg['steps']:
                            # Decode polyline points
                            try:
                                import polyline as pl
                                step_coords = pl.decode(step['polyline']['points'])
                                coordinates.extend([(lat, lon) for lat, lon in step_coords])
                            except ImportError:
                                # Just use start and end points
                                start = step['start_location']
                                end = step['end_location']
                                coordinates.extend([
                                    (start['lat'], start['lng']),
                                    (end['lat'], end['lng'])
                                ])
                    
                    return coordinates
            
            return None
            
        except Exception as e:
            print(f"Google Maps route geometry error: {e}")
            return None


class MapGenerator:
    """
    Generates interactive maps showing optimized delivery routes with real road paths.
    """
    
    def __init__(self, use_real_roads: bool = True):
        """Initialize map generator."""
        self.use_real_roads = use_real_roads
        
        # Initialize route services
        self.route_services = []
        if use_real_roads:
            self.route_services.append(OSRMRouteService())
            self.route_services.append(GoogleMapsRouteService())
    
    def _get_route_geometry(self, origin: Tuple[float, float], 
                           destination: Tuple[float, float]) -> List[Tuple[float, float]]:
        """Get route geometry between two points."""
        if not self.use_real_roads:
            return [origin, destination]
        
        # Try each route service
        for service in self.route_services:
            geometry = service.get_route_geometry(origin, destination)
            if geometry and len(geometry) > 2:  # More than just start/end points
                return geometry
        
        # Fallback to straight line
        return [origin, destination]
    
    def create_route_map(self, addresses: List[str], 
                        coordinates: List[Tuple[float, float]],
                        route_order: List[int],
                        output_file: str = "route_map.html",
                        use_real_roads: Optional[bool] = None) -> str:
        """
        Create an interactive map showing the optimized route with real road paths.
        
        Args:
            addresses: List of address strings
            coordinates: List of (latitude, longitude) tuples
            route_order: Optimized order to visit locations
            output_file: Output HTML file path
            use_real_roads: Override for using real road paths
            
        Returns:
            Path to generated HTML file
        """
        if not coordinates or not route_order:
            raise ValueError("Need coordinates and route order to generate map")
        
        # Use instance setting or override
        show_real_roads = use_real_roads if use_real_roads is not None else self.use_real_roads
        
        # Calculate map center
        center_lat = sum(coord[0] for coord in coordinates) / len(coordinates)
        center_lon = sum(coord[1] for coord in coordinates) / len(coordinates)
        
        # Create map
        route_map = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=12,
            tiles='OpenStreetMap'
        )
        
        # Add markers for each location
        for i, order_index in enumerate(route_order):
            coord = coordinates[order_index]
            address = addresses[order_index] if order_index < len(addresses) else f"Location {order_index}"
            
            # Determine marker properties
            if i == 0:
                # Start location
                icon_color = 'green'
                icon_symbol = 'play'
                popup_text = f"START: {address}"
            elif i == len(route_order) - 1:
                # End location  
                icon_color = 'red'
                icon_symbol = 'stop'
                popup_text = f"END: {address}"
            else:
                # Intermediate stops
                icon_color = 'blue'
                icon_symbol = 'info-sign'
                popup_text = f"Stop {i}: {address}"
            
            folium.Marker(
                location=[coord[0], coord[1]],
                popup=folium.Popup(popup_text, max_width=300),
                tooltip=f"Stop {i+1}",
                icon=folium.Icon(color=icon_color, icon=icon_symbol)
            ).add_to(route_map)
        
        # Add route lines with real road paths
        if show_real_roads:
            print("  Generating route paths using real roads...")
            
            # Create route segments between consecutive stops
            for i in range(len(route_order)):
                current_idx = route_order[i]
                next_idx = route_order[(i + 1) % len(route_order)]  # Wrap around for return trip
                
                current_coord = coordinates[current_idx]
                next_coord = coordinates[next_idx]
                
                print(f"    Fetching route segment {i+1}/{len(route_order)}")
                
                # Get real road geometry
                route_geometry = self._get_route_geometry(current_coord, next_coord)
                
                # Determine line color based on segment
                if i == len(route_order) - 1:
                    # Return to start - use dashed line
                    line_color = 'orange'
                    dash_array = '10,5'
                    popup_text = 'Return to Start'
                else:
                    line_color = 'red'
                    dash_array = None
                    popup_text = f'Route Segment {i+1}'
                
                # Add the route line
                folium.PolyLine(
                    locations=[[lat, lon] for lat, lon in route_geometry],
                    color=line_color,
                    weight=4,
                    opacity=0.8,
                    dash_array=dash_array,
                    popup=popup_text
                ).add_to(route_map)
        else:
            # Use straight lines (original behavior)
            route_coordinates = []
            for order_index in route_order:
                route_coordinates.append([coordinates[order_index][0], coordinates[order_index][1]])
            
            # Add line back to start for round trip
            if len(route_coordinates) > 1:
                route_coordinates.append(route_coordinates[0])
            
            folium.PolyLine(
                locations=route_coordinates,
                color='red',
                weight=3,
                opacity=0.8,
                popup='Optimized Route (Straight Lines)'
            ).add_to(route_map)
        
        # Add legend
        legend_html = '''
        <div style="position: fixed; 
                    bottom: 50px; left: 50px; width: 200px; height: 90px; 
                    background-color: white; border:2px solid grey; z-index:9999; 
                    font-size:14px; padding: 10px">
        <p><b>Route Legend</b></p>
        <p><i class="fa fa-play" style="color:green"></i> Start Location</p>
        <p><i class="fa fa-info-circle" style="color:blue"></i> Delivery Stops</p>
        <p><i class="fa fa-stop" style="color:red"></i> End Location</p>
        </div>
        '''
        route_map.get_root().html.add_child(folium.Element(legend_html))
        
        # Save map
        route_map.save(output_file)
        
        return os.path.abspath(output_file)
    
    def create_comparison_map(self, addresses: List[str],
                             coordinates: List[Tuple[float, float]],
                             original_route: List[int],
                             optimized_route: List[int],
                             output_file: str = "comparison_map.html") -> str:
        """
        Create a map comparing original vs optimized routes.
        
        Args:
            addresses: List of address strings
            coordinates: List of coordinates
            original_route: Original route order
            optimized_route: Optimized route order
            output_file: Output HTML file path
            
        Returns:
            Path to generated HTML file
        """
        if not coordinates or not original_route or not optimized_route:
            raise ValueError("Need coordinates and both routes to generate comparison")
        
        # Calculate map center
        center_lat = sum(coord[0] for coord in coordinates) / len(coordinates)
        center_lon = sum(coord[1] for coord in coordinates) / len(coordinates)
        
        # Create map
        comparison_map = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=12,
            tiles='OpenStreetMap'
        )
        
        # Add markers
        for i, coord in enumerate(coordinates):
            address = addresses[i] if i < len(addresses) else f"Location {i}"
            
            folium.Marker(
                location=[coord[0], coord[1]],
                popup=folium.Popup(address, max_width=300),
                tooltip=f"Location {i+1}",
                icon=folium.Icon(color='blue', icon='info-sign')
            ).add_to(comparison_map)
        
        # Add original route (red, dashed)
        original_coords = []
        for order_index in original_route:
            original_coords.append([coordinates[order_index][0], coordinates[order_index][1]])
        original_coords.append(original_coords[0])  # Return to start
        
        folium.PolyLine(
            locations=original_coords,
            color='red',
            weight=3,
            opacity=0.6,
            dash_array='10,5',
            popup='Original Route'
        ).add_to(comparison_map)
        
        # Add optimized route (green, solid)
        optimized_coords = []
        for order_index in optimized_route:
            optimized_coords.append([coordinates[order_index][0], coordinates[order_index][1]])
        optimized_coords.append(optimized_coords[0])  # Return to start
        
        folium.PolyLine(
            locations=optimized_coords,
            color='green',
            weight=4,
            opacity=0.8,
            popup='Optimized Route'
        ).add_to(comparison_map)
        
        # Add legend
        legend_html = '''
        <div style="position: fixed; 
                    bottom: 50px; left: 50px; width: 220px; height: 80px; 
                    background-color: white; border:2px solid grey; z-index:9999; 
                    font-size:14px; padding: 10px">
        <p><b>Route Comparison</b></p>
        <p><span style="color:red">━ ━ ━</span> Original Route</p>
        <p><span style="color:green">━━━━</span> Optimized Route</p>
        </div>
        '''
        comparison_map.get_root().html.add_child(folium.Element(legend_html))
        
        # Save map
        comparison_map.save(output_file)
        
        return os.path.abspath(output_file)
    
    def add_statistics_to_map(self, map_obj: folium.Map, 
                             total_distance: float,
                             total_time: float,
                             num_stops: int) -> None:
        """
        Add route statistics to an existing map.
        
        Args:
            map_obj: Folium map object
            total_distance: Total route distance in km
            total_time: Total estimated time in hours
            num_stops: Number of delivery stops
        """
        stats_html = f'''
        <div style="position: fixed; 
                    top: 10px; right: 10px; width: 200px; height: 120px; 
                    background-color: white; border:2px solid grey; z-index:9999; 
                    font-size:12px; padding: 10px">
        <p><b>Route Statistics</b></p>
        <p>Total Distance: {total_distance:.2f} km</p>
        <p>Estimated Time: {total_time:.2f} hours</p>
        <p>Number of Stops: {num_stops}</p>
        <p>Avg per Stop: {total_distance/max(num_stops,1):.2f} km</p>
        </div>
        '''
        map_obj.get_root().html.add_child(folium.Element(stats_html))
