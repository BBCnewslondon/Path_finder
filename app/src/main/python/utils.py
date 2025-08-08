"""
Utility functions for the delivery route optimization project.
"""

from typing import List, Dict, Any, Tuple
import json
import csv
import os


def load_addresses_from_file(file_path: str) -> List[str]:
    """
    Load addresses from various file formats.

    Args:
        file_path: Path to file containing addresses

    Returns:
        List of address strings
    """
    addresses = []

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    file_ext = os.path.splitext(file_path)[1].lower()

    try:
        if file_ext == '.txt':
            with open(file_path, 'r', encoding='utf-8') as f:
                addresses = [line.strip() for line in f if line.strip()]

        elif file_ext == '.csv':
            with open(file_path, 'r', encoding='utf-8', newline='') as f:
                reader = csv.reader(f)
                for row in reader:
                    if row:  # Skip empty rows
                        # Assume first column contains addresses
                        addresses.append(row[0].strip())

        elif file_ext == '.json':
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    addresses = [str(addr).strip() for addr in data]
                elif isinstance(data, dict) and 'addresses' in data:
                    addresses = [str(addr).strip() for addr in data['addresses']]
                else:
                    raise ValueError("JSON file must contain a list of addresses or a dict with 'addresses' key")
        else:
            raise ValueError(f"Unsupported file format: {file_ext}. Supported: .txt, .csv, .json")

    except Exception as e:
        raise ValueError(f"Error reading file {file_path}: {e}")

    return [addr for addr in addresses if addr]  # Remove empty strings


def save_addresses_to_file(addresses: List[str], file_path: str) -> None:
    """
    Save addresses to a file.

    Args:
        addresses: List of address strings
        file_path: Output file path
    """
    file_ext = os.path.splitext(file_path)[1].lower()

    try:
        if file_ext == '.txt':
            with open(file_path, 'w', encoding='utf-8') as f:
                for address in addresses:
                    f.write(f"{address}\n")

        elif file_ext == '.csv':
            with open(file_path, 'w', encoding='utf-8', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['Address'])  # Header
                for address in addresses:
                    writer.writerow([address])

        elif file_ext == '.json':
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump({'addresses': addresses}, f, indent=2, ensure_ascii=False)
        else:
            raise ValueError(f"Unsupported file format: {file_ext}")

    except Exception as e:
        raise ValueError(f"Error writing file {file_path}: {e}")


def save_route_results(addresses: List[str],
                      coordinates: List[Tuple[float, float]],
                      route_order: List[int],
                      total_distance: float,
                      total_time: float,
                      output_file: str) -> None:
    """
    Save route optimization results to a JSON file.

    Args:
        addresses: List of addresses
        coordinates: List of coordinates
        route_order: Optimized route order
        total_distance: Total route distance
        total_time: Total estimated time
        output_file: Output file path
    """
    results = {
        'optimization_results': {
            'total_distance_km': round(total_distance, 2),
            'total_time_hours': round(total_time, 2),
            'number_of_stops': len(addresses),
            'algorithm_used': 'TSP Optimization'
        },
        'route_order': [
            {
                'stop_number': i + 1,
                'address': addresses[route_order[i]] if route_order[i] < len(addresses) else f"Location {route_order[i]}",
                'coordinates': {
                    'latitude': coordinates[route_order[i]][0],
                    'longitude': coordinates[route_order[i]][1]
                }
            }
            for i in range(len(route_order))
        ],
        'original_addresses': addresses
    }

    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
    except Exception as e:
        raise ValueError(f"Error saving results to {output_file}: {e}")


def validate_coordinates(coordinates: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
    """
    Validate and filter coordinate pairs.

    Args:
        coordinates: List of (latitude, longitude) tuples

    Returns:
        List of valid coordinates
    """
    valid_coords = []

    for i, coord in enumerate(coordinates):
        if coord is None:
            continue

        try:
            lat, lon = coord
            # Check if coordinates are within valid ranges
            if -90 <= lat <= 90 and -180 <= lon <= 180:
                valid_coords.append((float(lat), float(lon)))
            else:
                print(f"Invalid coordinates at index {i}: {coord}")
        except (TypeError, ValueError) as e:
            print(f"Error processing coordinates at index {i}: {e}")

    return valid_coords


def format_distance(distance_km: float) -> str:
    """
    Format distance for human-readable output.

    Args:
        distance_km: Distance in kilometers

    Returns:
        Formatted distance string
    """
    if distance_km < 1:
        return f"{distance_km * 1000:.0f} m"
    else:
        return f"{distance_km:.2f} km"


def format_time(time_hours: float) -> str:
    """
    Format time for human-readable output.

    Args:
        time_hours: Time in hours

    Returns:
        Formatted time string
    """
    if time_hours < 1:
        minutes = time_hours * 60
        return f"{minutes:.0f} min"
    else:
        hours = int(time_hours)
        minutes = int((time_hours - hours) * 60)
        if hours > 0 and minutes > 0:
            return f"{hours}h {minutes}m"
        elif hours > 0:
            return f"{hours}h"
        else:
            return f"{minutes}m"


def print_route_summary(addresses: List[str],
                       route_order: List[int],
                       total_cost: float,
                       optimize_by: str) -> None:
    """
    Print a summary of the optimized route.

    Args:
        addresses: List of addresses
        route_order: Optimized route order
        total_cost: Total cost (distance or time)
        optimize_by: The metric optimized for ('distance' or 'time')
    """
    print("\n" + "="*60)
    print("DELIVERY ROUTE OPTIMIZATION RESULTS")
    print("="*60)

    if optimize_by == 'time':
        print(f"Total Time: {format_time(total_cost)}")
    else:
        print(f"Total Distance: {format_distance(total_cost)}")

    print(f"Number of Stops: {len(addresses)}")

    print("\nOptimized Route Order:")
    print("-" * 40)

    for i, order_index in enumerate(route_order):
        address = addresses[order_index] if order_index < len(addresses) else f"Location {order_index}"
        if i == 0:
            print(f"START: {address}")
        elif i == len(route_order) - 1:
            print(f"END:   {address}")
        else:
            print(f"Stop {i}: {address}")

    print("-" * 40)
    print("Return to START to complete route")
    print("="*60)


def load_cost_matrix(file_path: str) -> List[List[float]]:
    """Load a cost matrix from a JSON file."""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except (IOError, json.JSONDecodeError) as e:
        raise ValueError(f"Error loading cost matrix from {file_path}: {e}")
