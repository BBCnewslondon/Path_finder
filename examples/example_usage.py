"""
Example usage of the Delivery Route Optimizer API.
This script demonstrates how to use the optimizer programmatically.
"""

import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.geocoder import AddressGeocoder
from src.distance_calculator import DistanceCalculator
from src.route_optimizer import RouteOptimizer
from src.map_generator import MapGenerator
from src.utils import print_route_summary


def example_basic_optimization():
    """Basic example of route optimization."""
    print("=" * 60)
    print("BASIC ROUTE OPTIMIZATION EXAMPLE")
    print("=" * 60)
    
    # Sample addresses in Springfield, IL
    addresses = [
        "Springfield City Hall, Springfield, IL",
        "Abraham Lincoln Presidential Library, Springfield, IL", 
        "Illinois State Capitol, Springfield, IL",
        "University of Illinois Springfield, Springfield, IL",
        "Memorial Medical Center, Springfield, IL"
    ]
    
    print(f"Optimizing route for {len(addresses)} locations...")
    
    # Initialize components
    geocoder = AddressGeocoder()
    distance_calc = DistanceCalculator()
    optimizer = RouteOptimizer(algorithm="2opt")
    
    # Geocode addresses
    print("\nGeocoding addresses...")
    geocode_results = geocoder.geocode_addresses(addresses)
    
    # Filter valid results
    valid_addresses = []
    valid_coordinates = []
    
    for addr, coords in geocode_results.items():
        if coords:
            valid_addresses.append(addr)
            valid_coordinates.append(coords)
    
    if len(valid_addresses) < 2:
        print("Not enough valid addresses for optimization")
        return
    
    # Calculate distances
    print("Calculating distance matrix...")
    distance_matrix = distance_calc.calculate_distance_matrix(valid_coordinates)
    
    # Optimize route
    print("Optimizing route...")
    route_order, total_distance = optimizer.optimize_route(distance_matrix)
    
    # Calculate time estimate
    total_time = distance_calc.estimate_travel_time(total_distance)
    
    # Display results
    print_route_summary(valid_addresses, route_order, total_distance, total_time)
    
    return valid_addresses, valid_coordinates, route_order


def example_algorithm_comparison():
    """Compare different optimization algorithms."""
    print("\n" + "=" * 60)
    print("ALGORITHM COMPARISON EXAMPLE")
    print("=" * 60)
    
    # Sample addresses
    addresses = [
        "100 N 1st St, Springfield, IL",
        "200 S 2nd St, Springfield, IL",
        "300 E 3rd St, Springfield, IL", 
        "400 W 4th St, Springfield, IL",
        "500 N 5th St, Springfield, IL",
        "600 S 6th St, Springfield, IL"
    ]
    
    # Geocode addresses
    geocoder = AddressGeocoder()
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
    
    # Calculate distance matrix
    distance_calc = DistanceCalculator()
    distance_matrix = distance_calc.calculate_distance_matrix(valid_coordinates)
    
    # Test different algorithms
    algorithms = ['nearest_neighbor', '2opt', 'genetic']
    results = {}
    
    for algorithm in algorithms:
        print(f"\nTesting {algorithm}...")
        optimizer = RouteOptimizer(algorithm=algorithm)
        
        try:
            route_order, total_distance = optimizer.optimize_route(distance_matrix)
            total_time = distance_calc.estimate_travel_time(total_distance)
            results[algorithm] = {
                'route': route_order,
                'distance': total_distance,
                'time': total_time
            }
            print(f"  Distance: {total_distance:.2f} km")
            print(f"  Time: {total_time:.2f} hours")
        except Exception as e:
            print(f"  Error: {e}")
    
    # Show best result
    if results:
        best_algorithm = min(results.keys(), key=lambda k: results[k]['distance'])
        print(f"\nBest algorithm: {best_algorithm}")
        print(f"Best distance: {results[best_algorithm]['distance']:.2f} km")


def example_map_generation():
    """Example of generating route maps."""
    print("\n" + "=" * 60)
    print("MAP GENERATION EXAMPLE")
    print("=" * 60)
    
    # Use results from basic optimization
    try:
        result = example_basic_optimization()
        if result is None:
            print("Could not get optimization results for map generation")
            return
            
        addresses, coordinates, route_order = result
        
        # Generate map
        map_generator = MapGenerator()
        
        output_file = "example_route_map.html"
        print(f"\nGenerating map: {output_file}")
        
        map_path = map_generator.create_route_map(
            addresses, coordinates, route_order, output_file
        )
        
        print(f"Map saved to: {map_path}")
        print("Open the HTML file in your web browser to view the interactive map.")
        
    except Exception as e:
        print(f"Error generating map: {e}")


def main():
    """Run all examples."""
    print("DELIVERY ROUTE OPTIMIZER - EXAMPLES")
    
    try:
        # Run basic optimization
        example_basic_optimization()
        
        # Compare algorithms
        example_algorithm_comparison()
        
        # Generate map
        example_map_generation()
        
        print("\n" + "=" * 60)
        print("EXAMPLES COMPLETED")
        print("=" * 60)
        
    except KeyboardInterrupt:
        print("\nExamples interrupted by user")
    except Exception as e:
        print(f"\nError running examples: {e}")


if __name__ == "__main__":
    main()
