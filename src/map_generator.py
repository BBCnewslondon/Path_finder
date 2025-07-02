"""
Map generation module for visualizing optimized routes.
Creates interactive maps showing delivery routes.
"""

from typing import List, Tuple, Optional, Dict
import folium
import os


class MapGenerator:
    """
    Generates interactive maps showing optimized delivery routes.
    """
    
    def __init__(self):
        """Initialize map generator."""
        pass
    
    def create_route_map(self, addresses: List[str], 
                        coordinates: List[Tuple[float, float]],
                        route_order: List[int],
                        output_file: str = "route_map.html") -> str:
        """
        Create an interactive map showing the optimized route.
        
        Args:
            addresses: List of address strings
            coordinates: List of (latitude, longitude) tuples
            route_order: Optimized order to visit locations
            output_file: Output HTML file path
            
        Returns:
            Path to generated HTML file
        """
        if not coordinates or not route_order:
            raise ValueError("Need coordinates and route order to generate map")
        
        # Calculate map center
        center_lat = sum(coord[0] for coord in coordinates) / len(coordinates)
        center_lon = sum(coord[1] for coord in coordinates) / len(coordinates)
        
        # Create map
        route_map = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=12,
            tiles='OpenStreetMap'
        )
        
        # Define colors for different types of markers
        colors = ['red', 'blue', 'green', 'purple', 'orange', 'darkred', 
                 'lightred', 'beige', 'darkblue', 'darkgreen', 'cadetblue', 
                 'darkpurple', 'white', 'pink', 'lightblue', 'lightgreen', 
                 'gray', 'black', 'lightgray']
        
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
        
        # Add route lines
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
            popup='Optimized Route'
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
