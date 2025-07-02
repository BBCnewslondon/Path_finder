<!-- Use this file to provide workspace-specific custom instructions to Copilot. For more details, visit https://code.visualstudio.com/docs/copilot/copilot-customization#_use-a-githubcopilotinstructionsmd-file -->

# Delivery Route Optimization Project Instructions

This is a Python project that solves the Traveling Salesman Problem (TSP) for delivery route optimization. The goal is to find the shortest path between multiple addresses to minimize delivery time.

## Key Technologies
- Python 3.8+
- Google OR-Tools for optimization
- Geopy for geocoding
- Folium for map visualization
- NumPy/SciPy for mathematical operations

## Code Style Guidelines
- Follow PEP 8 Python style guidelines
- Use type hints for function parameters and return values
- Write descriptive docstrings for all classes and functions
- Prefer composition over inheritance
- Keep functions small and focused on single responsibilities

## Architecture Principles
- Separate concerns: geocoding, optimization, visualization, and I/O
- Use dependency injection for external services (APIs)
- Implement error handling for network requests and invalid addresses
- Support multiple optimization algorithms (nearest neighbor, 2-opt, OR-Tools)
- Design for extensibility to support different distance metrics and constraints

## Testing Approach
- Write unit tests for core algorithms
- Mock external API calls in tests
- Include integration tests with sample data
- Test edge cases like single address, duplicate addresses, unreachable locations

## Performance Considerations
- Cache geocoding results to avoid repeated API calls
- Implement timeout handling for external requests
- Consider algorithm complexity for large address lists
- Optimize memory usage for distance matrices
