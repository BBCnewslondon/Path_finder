from geocoder import AddressGeocoder
from distance_calculator import DistanceCalculator
from route_optimizer import RouteOptimizer
from map_generator import MapGenerator
import os

def run_optimization(addresses_raw, algorithm, optimize_by, use_real_roads, app_home):
    """
    This function is the main entry point from the Android app.
    """
    # Modify file paths to use the app's private storage
    geocode_cache_path = os.path.join(app_home, "geocode_cache.json")
    route_cache_path = os.path.join(app_home, "route_cache.json")
    map_output_path = os.path.join(app_home, "route_map.html")

    addresses = [addr.strip() for addr in addresses_raw.split('\\n') if addr.strip()]
    if len(addresses) < 2:
        return {"error": "Please enter at least two addresses."}

    try:
        # Initialize components with correct cache paths
        geocoder = AddressGeocoder(cache_file=geocode_cache_path)
        dist_calc = DistanceCalculator(use_real_roads=use_real_roads)
        dist_calc.route_cache.cache_file = route_cache_path # Set cache file path
        optimizer = RouteOptimizer(algorithm=algorithm)
        map_gen = MapGenerator()

        # 1. Geocode addresses
        geocode_results = geocoder.geocode_addresses(addresses)
        valid_addresses = [addr for addr, coords in geocode_results.items() if coords]
        valid_coordinates = [coords for coords in geocode_results.values() if coords]

        if len(valid_addresses) < 2:
            return {"error": "Could not geocode at least two valid addresses."}

        # 2. Get cost matrix
        if optimize_by == 'time':
            cost_matrix = dist_calc.get_duration_matrix(valid_coordinates)
        else:
            cost_matrix = dist_calc.calculate_distance_matrix(valid_coordinates)

        # 3. Optimize route
        route_indices, total_cost = optimizer.optimize_route(cost_matrix)

        # 4. Prepare results
        ordered_addresses = [valid_addresses[i] for i in route_indices]

        # 5. Generate map
        map_file_path = map_gen.create_route_map(
            valid_addresses, valid_coordinates, route_indices, map_output_path, use_real_roads
        )

        return {
            "success": True,
            "ordered_addresses": ordered_addresses,
            "total_cost": f"{total_cost:.2f}",
            "cost_unit": "hours" if optimize_by == 'time' else "km",
            "map_path": map_file_path
        }

    except Exception as e:
        return {"error": f"An error occurred in Python: {e}"}
