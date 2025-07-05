"""
Visual route comparison example.
Creates maps showing the difference between straight-line and real road visualization.
"""

import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.geocoder import AddressGeocoder
from src.distance_calculator import DistanceCalculator
from src.route_optimizer import RouteOptimizer
from src.map_generator import MapGenerator


def create_visual_comparison():
    """Create side-by-side visual comparison of routing methods."""
    print("=" * 70)
    print("VISUAL ROUTE COMPARISON")
    print("=" * 70)
    
    # Sample addresses in London
    addresses = [
        "10 Downing Street, London, UK",
        "Buckingham Palace, London, UK", 
        "Tower of London, London, UK",
        "Westminster Abbey, London, UK",
        "Big Ben, London, UK"
    ]
    
    print(f"Creating visual comparison for {len(addresses)} London locations...")
    
    # Initialize components
    geocoder = AddressGeocoder()
    
    # Geocode addresses
    print("\nGeocoding addresses...")
    geocode_results = geocoder.geocode_addresses(addresses)
    
    valid_addresses = []
    valid_coordinates = []
    
    for addr, coords in geocode_results.items():
        if coords:
            valid_addresses.append(addr)
            valid_coordinates.append(coords)
    
    if len(valid_addresses) < 3:
        print("Not enough valid addresses for comparison")
        return
    
    # Calculate route using real roads for distance
    print("\nOptimizing route using real road distances...")
    distance_calc = DistanceCalculator(use_real_roads=True)
    optimizer = RouteOptimizer(algorithm="2opt")
    
    distance_matrix = distance_calc.calculate_distance_matrix(valid_coordinates)
    route_order, total_distance = optimizer.optimize_route(distance_matrix)
    
    print(f"Optimized route: {total_distance:.2f} km total distance")
    
    # Create maps with different visualizations
    print("\nGenerating comparison maps...")
    
    # Map 1: Straight-line visualization
    print("  Creating straight-line visualization map...")
    map_gen_straight = MapGenerator(use_real_roads=False)
    straight_map_path = map_gen_straight.create_route_map(
        valid_addresses, valid_coordinates, route_order, 
        "comparison_straight_lines.html", use_real_roads=False
    )
    
    # Map 2: Real road visualization
    print("  Creating real road visualization map...")
    map_gen_roads = MapGenerator(use_real_roads=True)
    roads_map_path = map_gen_roads.create_route_map(
        valid_addresses, valid_coordinates, route_order, 
        "comparison_real_roads.html", use_real_roads=True
    )
    
    print("\n" + "=" * 70)
    print("VISUAL COMPARISON COMPLETE")
    print("=" * 70)
    print(f"Straight-line map: {straight_map_path}")
    print(f"Real roads map: {roads_map_path}")
    print()
    print("Open both HTML files in your browser to see the difference!")
    print("- Straight-line map shows direct lines between points")
    print("- Real roads map shows actual driving routes following streets")


if __name__ == "__main__":
    try:
        create_visual_comparison()
    except KeyboardInterrupt:
        print("\nComparison interrupted by user")
    except Exception as e:
        print(f"\nError creating visual comparison: {e}")
