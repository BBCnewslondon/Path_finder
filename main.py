#!/usr/bin/env python3
"""
Delivery Route Optimizer - Main Application
Command-line interface for optimizing delivery routes.
"""

import argparse
import sys
import os
from typing import List, Optional

from src.geocoder import AddressGeocoder
from src.distance_calculator import DistanceCalculator
from src.route_optimizer import RouteOptimizer
from src.map_generator import MapGenerator
from src.utils import (
    load_addresses_from_file, save_route_results, 
    print_route_summary, validate_coordinates, load_cost_matrix
)
from src.config import (
    DEFAULT_ALGORITHM, DEFAULT_OPTIMIZE_BY,
    DEFAULT_MAP_FILE, DEFAULT_RESULTS_FILE
)


class DeliveryRouteApp:
    """Main application class for delivery route optimization."""
    
    def __init__(self, use_real_roads: bool = True):
        """Initialize the application."""
        self.geocoder = AddressGeocoder()
        self.distance_calculator = DistanceCalculator(use_real_roads=use_real_roads)
        self.route_optimizer = RouteOptimizer()
        self.map_generator = MapGenerator(use_real_roads=use_real_roads)
        self.use_real_roads = use_real_roads
    
    def optimize_delivery_route(self, 
                               addresses: List[str],
                               algorithm: str = "2opt",
                               start_address: Optional[str] = None,
                               end_address: Optional[str] = None,
                               optimize_by: str = "distance",
                               cost_matrix_file: Optional[str] = None,
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
            end_address: Ending address (if None, returns to start)
            optimize_by: What to optimize for ('distance' or 'time')
            cost_matrix_file: Path to a pre-calculated cost matrix file
            generate_map: Whether to generate an interactive map
            map_output: Output file for map
            save_results: Whether to save results to file
            results_output: Output file for results
        """
        if not addresses and not cost_matrix_file:
            print("Error: No addresses or cost matrix provided")
            return
        
        print(f"Optimizing route for {len(addresses)} addresses...")
        print(f"Using algorithm: {algorithm}, optimizing by: {optimize_by}")
        
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
        
        if len(valid_addresses) < 2 and not cost_matrix_file:
            print("Error: Need at least 2 valid addresses to optimize route")
            return
        
        print(f"Successfully geocoded {len(valid_addresses)} out of {len(addresses)} addresses")
        
        # Step 2: Get cost matrix
        if cost_matrix_file:
            print(f"\nStep 2: Loading cost matrix from {cost_matrix_file}...")
            cost_matrix = load_cost_matrix(cost_matrix_file)
        else:
            print(f"\nStep 2: Calculating {optimize_by} matrix...")
            if optimize_by == 'time':
                cost_matrix = self.distance_calculator.get_duration_matrix(valid_coordinates)
            else:
                cost_matrix = self.distance_calculator.calculate_distance_matrix(valid_coordinates)

        # Step 3: Determine starting and ending points
        start_index = 0
        if start_address:
            try:
                start_index = valid_addresses.index(start_address)
                print(f"Starting from: {start_address}")
            except ValueError:
                print(f"Warning: Start address '{start_address}' not found, using first address.")
        
        end_index = None
        if end_address:
            try:
                end_index = valid_addresses.index(end_address)
                print(f"Ending at: {end_address}")
            except ValueError:
                print(f"Warning: End address '{end_address}' not found, will perform a round trip.")

        # Step 4: Optimize route
        print(f"\nStep 3: Optimizing route using {algorithm}...")
        self.route_optimizer.algorithm = algorithm
        
        try:
            route_order, total_cost = self.route_optimizer.optimize_route(
                cost_matrix, start_index, end_index
            )
        except Exception as e:
            print(f"Error during optimization: {e}")
            return
        
        # Step 5: Calculate total distance and time for summary
        # Note: total_cost is what was optimized, but we might want to see both results
        total_distance = self.distance_calculator.calculate_total_route_distance(valid_coordinates, route_order)
        total_time = self.distance_calculator.estimate_travel_time(total_distance, 50.0)

        # Step 6: Display results
        print_route_summary(valid_addresses, route_order, total_cost, optimize_by)
        
        # Step 7: Generate map if requested
        if generate_map:
            try:
                print(f"\nGenerating interactive map: {map_output}")
                if self.use_real_roads:
                    print("  Using real road paths for route visualization")
                map_path = self.map_generator.create_route_map(
                    valid_addresses, valid_coordinates, route_order, map_output, 
                    use_real_roads=self.use_real_roads
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
        default=DEFAULT_ALGORITHM, help=f'Optimization algorithm (default: {DEFAULT_ALGORITHM})'
    )
    parser.add_argument(
        '--optimize-by', choices=['distance', 'time'], default=DEFAULT_OPTIMIZE_BY,
        help=f"Optimize for shortest distance or fastest time (default: {DEFAULT_OPTIMIZE_BY})"
    )
    
    # Route options
    parser.add_argument(
        '--start', type=str,
        help='Starting address (if not specified, uses first address)'
    )
    parser.add_argument(
        '--end', type=str,
        help='Ending address (if not specified, returns to the start address)'
    )
    parser.add_argument(
        '--cost-matrix', type=str,
        help="Path to a file containing a pre-calculated cost matrix in JSON format"
    )
    parser.add_argument(
        '--roads', action='store_true', default=True,
        help='Use real road distances (default: True)'
    )
    parser.add_argument(
        '--straight-line', action='store_true',
        help='Use straight-line distances instead of roads'
    )
    
    # Output options
    parser.add_argument(
        '--map', type=str, nargs='?', const=DEFAULT_MAP_FILE,
        help=f'Generate interactive map (default filename: {DEFAULT_MAP_FILE})'
    )
    parser.add_argument(
        '--save', type=str, nargs='?', const=DEFAULT_RESULTS_FILE,
        help=f'Save results to file (default filename: {DEFAULT_RESULTS_FILE})'
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
    use_real_roads = not args.straight_line
    app = DeliveryRouteApp(use_real_roads=use_real_roads)
    
    app.optimize_delivery_route(
        addresses=addresses,
        algorithm=args.algorithm,
        start_address=args.start,
        end_address=args.end,
        optimize_by=args.optimize_by,
        cost_matrix_file=args.cost_matrix,
        generate_map=args.map is not None,
        map_output=args.map or DEFAULT_MAP_FILE,
        save_results=args.save is not None,
        results_output=args.save or DEFAULT_RESULTS_FILE
    )


if __name__ == "__main__":
    main()
