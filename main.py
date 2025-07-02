#!/usr/bin/env python3
"""
Delivery Route Optimizer - Main Application
Command-line interface for optimizing delivery routes.
"""

import argparse
import sys
import os
from typing import List, Optional

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.geocoder import AddressGeocoder
from src.distance_calculator import DistanceCalculator
from src.route_optimizer import RouteOptimizer
from src.map_generator import MapGenerator
from src.utils import (
    load_addresses_from_file, save_route_results, 
    print_route_summary, validate_coordinates
)


class DeliveryRouteApp:
    """Main application class for delivery route optimization."""
    
    def __init__(self):
        """Initialize the application."""
        self.geocoder = AddressGeocoder()
        self.distance_calculator = DistanceCalculator()
        self.route_optimizer = RouteOptimizer()
        self.map_generator = MapGenerator()
    
    def optimize_delivery_route(self, 
                               addresses: List[str],
                               algorithm: str = "2opt",
                               start_address: Optional[str] = None,
                               generate_map: bool = False,
                               map_output: str = "route_map.html",
                               save_results: bool = False,
                               results_output: str = "route_results.json") -> None:
        """
        Main function to optimize a delivery route.
        
        Args:
            addresses: List of delivery addresses
            algorithm: Optimization algorithm to use
            start_address: Starting address (if None, uses first address)
            generate_map: Whether to generate an interactive map
            map_output: Output file for map
            save_results: Whether to save results to file
            results_output: Output file for results
        """
        if not addresses:
            print("Error: No addresses provided")
            return
        
        print(f"Optimizing route for {len(addresses)} addresses...")
        print(f"Using algorithm: {algorithm}")
        
        # Step 1: Geocode all addresses
        print("\nStep 1: Geocoding addresses...")
        geocode_results = self.geocoder.geocode_addresses(addresses)
        
        # Filter out failed geocoding results
        valid_addresses = []
        valid_coordinates = []
        
        for address, coords in geocode_results.items():
            if coords is not None:
                valid_addresses.append(address)
                valid_coordinates.append(coords)
        
        if len(valid_addresses) < 2:
            print("Error: Need at least 2 valid addresses to optimize route")
            return
        
        print(f"Successfully geocoded {len(valid_addresses)} out of {len(addresses)} addresses")
        
        # Step 2: Calculate distance matrix
        print("\nStep 2: Calculating distances...")
        distance_matrix = self.distance_calculator.calculate_distance_matrix(valid_coordinates)
        
        # Step 3: Determine starting point
        start_index = 0
        if start_address:
            try:
                start_index = valid_addresses.index(start_address)
                print(f"Starting from: {start_address}")
            except ValueError:
                print(f"Warning: Start address '{start_address}' not found, using first address")
        
        # Step 4: Optimize route
        print(f"\nStep 3: Optimizing route using {algorithm}...")
        self.route_optimizer.algorithm = algorithm
        
        try:
            route_order, total_distance = self.route_optimizer.optimize_route(
                distance_matrix, start_index
            )
        except Exception as e:
            print(f"Error during optimization: {e}")
            return
        
        # Step 5: Calculate estimated time
        avg_speed = 50.0  # km/h average city driving speed
        total_time = self.distance_calculator.estimate_travel_time(total_distance, avg_speed)
        
        # Step 6: Display results
        print_route_summary(valid_addresses, route_order, total_distance, total_time)
        
        # Step 7: Generate map if requested
        if generate_map:
            try:
                print(f"\nGenerating interactive map: {map_output}")
                map_path = self.map_generator.create_route_map(
                    valid_addresses, valid_coordinates, route_order, map_output
                )
                print(f"Map saved to: {map_path}")
            except Exception as e:
                print(f"Error generating map: {e}")
        
        # Step 8: Save results if requested
        if save_results:
            try:
                print(f"\nSaving results to: {results_output}")
                save_route_results(
                    valid_addresses, valid_coordinates, route_order,
                    total_distance, total_time, results_output
                )
            except Exception as e:
                print(f"Error saving results: {e}")


def main():
    """Main entry point for the command-line interface."""
    parser = argparse.ArgumentParser(
        description="Optimize delivery routes to minimize travel time",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --addresses "123 Main St, City" "456 Oak Ave, City"
  python main.py --file addresses.txt --algorithm ortools --map route.html
  python main.py --addresses "Start Address" "Stop 1" "Stop 2" --start "Start Address"
        """
    )
    
    # Input options
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument(
        '--addresses', nargs='+', 
        help='List of delivery addresses'
    )
    input_group.add_argument(
        '--file', type=str,
        help='File containing addresses (txt, csv, or json)'
    )
    
    # Algorithm options
    parser.add_argument(
        '--algorithm', choices=['nearest_neighbor', '2opt', 'ortools', 'genetic'],
        default='2opt', help='Optimization algorithm (default: 2opt)'
    )
    
    # Route options
    parser.add_argument(
        '--start', type=str,
        help='Starting address (if not specified, uses first address)'
    )
    
    # Output options
    parser.add_argument(
        '--map', type=str, nargs='?', const='route_map.html',
        help='Generate interactive map (optional filename)'
    )
    parser.add_argument(
        '--save', type=str, nargs='?', const='route_results.json',
        help='Save results to file (optional filename)'
    )
    
    # Parse arguments
    args = parser.parse_args()
    
    # Load addresses
    try:
        if args.addresses:
            addresses = args.addresses
        else:
            addresses = load_addresses_from_file(args.file)
    except Exception as e:
        print(f"Error loading addresses: {e}")
        sys.exit(1)
    
    if not addresses:
        print("Error: No addresses found")
        sys.exit(1)
    
    # Create and run application
    app = DeliveryRouteApp()
    
    app.optimize_delivery_route(
        addresses=addresses,
        algorithm=args.algorithm,
        start_address=args.start,
        generate_map=args.map is not None,
        map_output=args.map or "route_map.html",
        save_results=args.save is not None,
        results_output=args.save or "route_results.json"
    )


if __name__ == "__main__":
    main()
