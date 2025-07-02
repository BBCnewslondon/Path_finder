# Delivery Route Optimizer

A Python application that finds the shortest delivery routes for multiple addresses, optimizing for minimum travel time. This software solves the Traveling Salesman Problem (TSP) to help delivery personnel minimize their time on the road.

## Features

- **Address Geocoding**: Convert street addresses to GPS coordinates
- **Route Optimization**: Find the shortest path visiting all delivery locations
- **Multiple Algorithms**: Support for different TSP solving approaches
- **Visual Maps**: Generate interactive maps showing optimized routes
- **Time Estimation**: Calculate estimated travel times between locations
- **Flexible Input**: Support for various address formats

## Quick Start

To test the application immediately with sample data:

```bash
# Activate the virtual environment (if not already active)
.venv\Scripts\activate

# Run with sample addresses and generate a map
python main.py --file examples/sample_addresses.txt --algorithm 2opt --map route_map.html

# Run the examples script to see all features
python examples/example_usage.py
```

This will create an optimized delivery route and generate an interactive HTML map that you can open in your web browser.

## Installation

1. Clone or download this repository
2. **Activate the virtual environment** (already created):
   ```bash
   # On Windows
   .venv\Scripts\activate
   
   # On macOS/Linux  
   source .venv/bin/activate
   ```
3. Install required dependencies (if not already installed):
   ```bash
   pip install -r requirements.txt
   ```
4. (Optional) Get a free API key from a mapping service for enhanced geocoding
5. (Optional) Create a `.env` file and add your API keys (see `.env.example`)

## Usage

### Basic Command Line Usage

```bash
# Optimize a route with a list of addresses
python main.py --addresses "123 Main St, City, State" "456 Oak Ave, City, State" "789 Pine Rd, City, State"

# Load addresses from a file
python main.py --file addresses.txt

# Generate an interactive map
python main.py --addresses "Address 1" "Address 2" "Address 3" --map output_map.html

# Try the sample data
python main.py --file examples/sample_addresses.txt --algorithm 2opt --map route_map.html
```

### Python API Usage

```python
from route_optimizer import RouteOptimizer

# Create optimizer instance
optimizer = RouteOptimizer()

# Add addresses
addresses = [
    "123 Main Street, Springfield, IL",
    "456 Oak Avenue, Springfield, IL", 
    "789 Pine Road, Springfield, IL"
]

# Find optimal route
route = optimizer.optimize_route(addresses)
print(f"Optimized route: {route}")
```

## Project Structure

```
Path_finder/
├── src/
│   ├── __init__.py
│   ├── geocoder.py          # Address to coordinate conversion
│   ├── route_optimizer.py   # Main optimization logic
│   ├── distance_calculator.py # Calculate distances/times
│   ├── map_generator.py     # Generate visual maps
│   └── utils.py            # Helper functions
├── tests/
│   ├── __init__.py
│   ├── test_geocoder.py
│   ├── test_optimizer.py
│   └── test_distance.py
├── examples/
│   ├── sample_addresses.txt
│   └── example_usage.py
├── main.py                 # CLI entry point
├── requirements.txt
├── .env.example
└── README.md
```

## Algorithm Details

The software implements multiple approaches to solve the TSP:

1. **Nearest Neighbor**: Fast heuristic for quick results
2. **2-opt Improvement**: Local search optimization
3. **OR-Tools**: Google's optimization library for exact solutions
4. **Genetic Algorithm**: Evolutionary approach for larger datasets

## Contributing

Feel free to submit issues and enhancement requests!

## License

This project is open source and available under the MIT License.
