"""
Road routing comparison example.
Demonstrates the difference between straight-line and real road distances.
"""

import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.geocoder import AddressGeocoder
from src.distance_calculator import DistanceCalculator
from src.route_optimizer import RouteOptimizer
from src.utils import print_route_summary


def compare_routing_methods():
    """Compare straight-line vs real road routing."""
    print("=" * 70)
    print("ROUTING METHOD COMPARISON")
    print("=" * 70)
    
    # Sample addresses in London
    addresses = [
        "10 Downing Street, London, UK",
        "Buckingham Palace, London, UK", 
        "Tower of London, London, UK",
        "Westminster Abbey, London, UK"
    ]
    
    print(f"Comparing routing methods for {len(addresses)} London locations...")
    
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
    
    if len(valid_addresses) < 2:
        print("Not enough valid addresses for comparison")
        return
    
    # Compare methods
    methods = [
        ("Straight-line distances", False),
        ("Real road distances", True)
    ]
    
    results = {}
    
    for method_name, use_roads in methods:
        print(f"\n{'-' * 50}")
        print(f"Testing: {method_name}")
        print(f"{'-' * 50}")
        
        # Initialize calculator
        distance_calc = DistanceCalculator(use_real_roads=use_roads)
        optimizer = RouteOptimizer(algorithm="2opt")
        
        # Calculate distances
        distance_matrix = distance_calc.calculate_distance_matrix(valid_coordinates)
        
        # Optimize route
        route_order, total_distance = optimizer.optimize_route(distance_matrix)
        
        # Calculate time estimate
        total_time = distance_calc.estimate_travel_time(total_distance)
        
        results[method_name] = {
            'route': route_order,
            'distance': total_distance,
            'time': total_time,
            'matrix': distance_matrix
        }
        
        print_route_summary(valid_addresses, route_order, total_distance, total_time)
    
    # Show comparison
    print("\n" + "=" * 70)
    print("COMPARISON SUMMARY")
    print("=" * 70)
    
    straight_line = results["Straight-line distances"]
    real_roads = results["Real road distances"]
    
    distance_diff = real_roads['distance'] - straight_line['distance']
    distance_percent = (distance_diff / straight_line['distance']) * 100
    
    time_diff = real_roads['time'] - straight_line['time']
    
    print(f"Straight-line total distance: {straight_line['distance']:.2f} km")
    print(f"Real roads total distance:    {real_roads['distance']:.2f} km")
    print(f"Difference:                   +{distance_diff:.2f} km ({distance_percent:+.1f}%)")
    print()
    print(f"Straight-line total time:     {straight_line['time']:.2f} hours")
    print(f"Real roads total time:        {real_roads['time']:.2f} hours") 
    print(f"Difference:                   +{time_diff:.2f} hours")
    print()
    
    # Show individual distance comparisons
    print("Individual segment comparisons:")
    print("-" * 40)
    
    n = len(valid_coordinates)
    for i in range(n):
        for j in range(i + 1, n):
            straight = straight_line['matrix'][i][j]
            roads = real_roads['matrix'][i][j]
            diff_percent = ((roads - straight) / straight) * 100
            
            addr1 = valid_addresses[i].split(',')[0]  # Just building name
            addr2 = valid_addresses[j].split(',')[0]
            
            print(f"{addr1} → {addr2}:")
            print(f"  Straight-line: {straight:.2f} km")
            print(f"  Real roads:    {roads:.2f} km (+{diff_percent:.1f}%)")
            print()
    
    print("This demonstrates why real road routing is important for")
    print("accurate delivery route optimization!")


if __name__ == "__main__":
    try:
        compare_routing_methods()
    except KeyboardInterrupt:
        print("\nComparison interrupted by user")
    except Exception as e:
        print(f"\nError running comparison: {e}")
