"""
Route optimization module implementing multiple TSP solving algorithms.
"""

from typing import List, Tuple, Optional, Dict, Any
import random
import numpy as np
from itertools import permutations
import time

from src.config import GA_POPULATION_SIZE, GA_GENERATIONS

try:
    from ortools.constraint_solver import routing_enums_pb2
    from ortools.constraint_solver import pywrapcp
    ORTOOLS_AVAILABLE = True
except ImportError:
    ORTOOLS_AVAILABLE = False


class RouteOptimizer:
    """
    Main route optimization class implementing multiple TSP algorithms.
    """

    def __init__(self, algorithm: str = "nearest_neighbor"):
        """
        Initialize route optimizer.

        Args:
            algorithm: Algorithm to use ('nearest_neighbor', '2opt', 'ortools', 'genetic')
        """
        self.algorithm = algorithm
        self.algorithms = {
            'nearest_neighbor': self._nearest_neighbor,
            '2opt': self._two_opt,
            'ortools': self._ortools_solver,
            'genetic': self._genetic_algorithm
        }

    def optimize_route(self, distance_matrix: List[List[float]],
                      start_index: int = 0,
                      end_index: Optional[int] = None) -> Tuple[List[int], float]:
        """
        Find optimal route given a distance matrix.

        Args:
            distance_matrix: 2D matrix of distances between points
            start_index: Index of starting point
            end_index: Index of ending point. If None, it's a round trip.

        Returns:
            Tuple of (route_indices, total_distance)
        """
        if self.algorithm not in self.algorithms:
            raise ValueError(f"Unknown algorithm: {self.algorithm}")

        if len(distance_matrix) <= 1:
            return [0], 0.0

        # If end_index is not provided, it's a round trip starting and ending at start_index
        if end_index is None:
            end_index = start_index

        return self.algorithms[self.algorithm](distance_matrix, start_index, end_index)

    def _nearest_neighbor(self, distance_matrix: List[List[float]],
                         start_index: int = 0,
                         end_index: int = 0) -> Tuple[List[int], float]:
        """
        Nearest neighbor heuristic algorithm.
        Fast but not optimal for large datasets.
        """
        n = len(distance_matrix)
        unvisited = set(range(n))
        route = [start_index]
        unvisited.remove(start_index)
        total_distance = 0.0
        current = start_index

        # Handle open and closed tours differently
        is_round_trip = start_index == end_index

        # If it's an open tour, the end node should not be visited until the end
        if not is_round_trip:
            unvisited.remove(end_index)

        while unvisited:
            # Find nearest unvisited node
            nearest = min(unvisited, key=lambda x: distance_matrix[current][x])
            total_distance += distance_matrix[current][nearest]
            route.append(nearest)
            unvisited.remove(nearest)
            current = nearest

        # For an open tour, add the final leg to the end_index
        if not is_round_trip:
            total_distance += distance_matrix[current][end_index]
            route.append(end_index)
        else: # For a round trip, return to start
            total_distance += distance_matrix[current][start_index]

        return route, total_distance

    def _two_opt(self, distance_matrix: List[List[float]],
                start_index: int = 0,
                end_index: int = 0) -> Tuple[List[int], float]:
        """
        2-opt improvement algorithm.
        Starts with nearest neighbor and improves with local search.
        """
        is_round_trip = start_index == end_index
        # Start with nearest neighbor solution
        route, _ = self._nearest_neighbor(distance_matrix, start_index, end_index)

        if len(route) <= 2: # No optimization possible for 2 or fewer stops
            return route, self._calculate_route_distance(route, distance_matrix, is_round_trip)

        improved = True
        while improved:
            improved = False
            # For round trips, we can swap up to the last edge. For open, only before the last stop.
            limit = len(route) if is_round_trip else len(route) -1
            for i in range(1, limit - 1):
                for j in range(i + 1, limit):
                    # Try swapping edges
                    new_route = route[:]
                    new_route[i:j] = reversed(new_route[i:j])

                    if self._calculate_route_distance(new_route, distance_matrix, is_round_trip) < \
                       self._calculate_route_distance(route, distance_matrix, is_round_trip):
                        route = new_route
                        improved = True

        total_distance = self._calculate_route_distance(route, distance_matrix, is_round_trip)
        return route, total_distance

    def _ortools_solver(self, distance_matrix: List[List[float]],
                       start_index: int = 0,
                       end_index: int = 0) -> Tuple[List[int], float]:
        """
        Google OR-Tools exact TSP solver.
        Provides optimal solutions for small to medium datasets.
        """
        if not ORTOOLS_AVAILABLE:
            print("OR-Tools not available, falling back to 2-opt")
            return self._two_opt(distance_matrix, start_index, end_index)

        n = len(distance_matrix)
        is_round_trip = start_index == end_index

        # Create the routing index manager
        if is_round_trip:
            manager = pywrapcp.RoutingIndexManager(n, 1, start_index)
        else:
            manager = pywrapcp.RoutingIndexManager(n, 1, [start_index], [end_index])

        # Create routing model
        routing = pywrapcp.RoutingModel(manager)

        def distance_callback(from_index, to_index):
            """Returns the distance between the two nodes."""
            from_node = manager.IndexToNode(from_index)
            to_node = manager.IndexToNode(to_index)
            return int(distance_matrix[from_node][to_node] * 1000)  # Convert to int

        transit_callback_index = routing.RegisterTransitCallback(distance_callback)
        routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

        # Setting search parameters
        search_parameters = pywrapcp.DefaultRoutingSearchParameters()
        search_parameters.first_solution_strategy = (
            routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC)
        search_parameters.time_limit.seconds = 30

        # Solve the problem
        solution = routing.SolveWithParameters(search_parameters)

        if solution:
            route = []
            index = routing.Start(0)
            while not routing.IsEnd(index):
                route.append(manager.IndexToNode(index))
                index = solution.Value(routing.NextVar(index))

            total_distance = solution.ObjectiveValue() / 1000.0  # Convert back to km
            return route, total_distance
        else:
            print("OR-Tools solver failed, falling back to 2-opt")
            return self._two_opt(distance_matrix, start_index)

    def _genetic_algorithm(self, distance_matrix: List[List[float]],
                          start_index: int = 0,
                          end_index: int = 0,
                          population_size: int = GA_POPULATION_SIZE,
                          generations: int = GA_GENERATIONS) -> Tuple[List[int], float]:
        """
        Genetic algorithm for TSP.
        Good for larger datasets where exact solutions are impractical.
        """
        n = len(distance_matrix)
        is_round_trip = start_index == end_index

        if n <= 3:
            return self._nearest_neighbor(distance_matrix, start_index, end_index)

        # Create initial population
        population = []

        nodes = list(range(n))
        nodes.remove(start_index)
        if not is_round_trip:
            nodes.remove(end_index)

        for _ in range(population_size):
            shuffled_middle = random.sample(nodes, len(nodes))
            if is_round_trip:
                route = [start_index] + shuffled_middle
            else:
                route = [start_index] + shuffled_middle + [end_index]
            population.append(route)

        for generation in range(generations):
            # Evaluate fitness (inverse of distance)
            fitness_scores = [1 / (self._calculate_route_distance(r, distance_matrix, is_round_trip) + 1) for r in population]

            # Selection and crossover
            new_population = []
            for _ in range(population_size):
                parent1 = self._tournament_selection(population, fitness_scores)
                parent2 = self._tournament_selection(population, fitness_scores)

                child = self._order_crossover(parent1, parent2, is_round_trip)

                # Mutation
                if random.random() < 0.1:
                    child = self._mutate_route(child, is_round_trip)

                new_population.append(child)

            population = new_population

        # Return best route
        best_route = min(population, key=lambda r: self._calculate_route_distance(r, distance_matrix, is_round_trip))
        best_distance = self._calculate_route_distance(best_route, distance_matrix, is_round_trip)

        return best_route, best_distance

    def _tournament_selection(self, population: List[List[int]],
                            fitness_scores: List[float],
                            tournament_size: int = 5) -> List[int]:
        """Tournament selection for genetic algorithm."""
        tournament_indices = random.sample(range(len(population)), tournament_size)
        tournament_fitness = [fitness_scores[i] for i in tournament_indices]
        winner_index = tournament_indices[tournament_fitness.index(max(tournament_fitness))]
        return population[winner_index]

    def _order_crossover(self, parent1: List[int], parent2: List[int], is_round_trip: bool) -> List[int]:
        """Order crossover operator for genetic algorithm."""
        n = len(parent1)

        # Determine the slice points, excluding start and end cities for open tours
        slice_start, slice_end = sorted(random.sample(range(1, n - (0 if is_round_trip else 1)), 2))

        child = [-1] * n
        child[0] = parent1[0]
        if not is_round_trip:
            child[-1] = parent1[-1]

        # Copy the slice from parent1
        child[slice_start:slice_end] = parent1[slice_start:slice_end]

        # Fill the rest from parent2
        parent2_subset = [item for item in parent2 if item not in child]

        j = 0
        for i in range(n):
            if child[i] == -1:
                child[i] = parent2_subset[j]
                j += 1

        return child

    def _mutate_route(self, route: List[int], is_round_trip: bool) -> List[int]:
        """Mutation operator for genetic algorithm (swap mutation)."""
        mutated_route = route[:]
        # Determine the range of indices that can be swapped
        swap_range = range(1, len(route) - (0 if is_round_trip else 1))

        if len(swap_range) >= 2:
            i, j = random.sample(swap_range, 2)
            mutated_route[i], mutated_route[j] = mutated_route[j], mutated_route[i]

        return mutated_route

    def _calculate_route_distance(self, route: List[int],
                                distance_matrix: List[List[float]],
                                is_round_trip: bool) -> float:
        """Calculate total distance for a route."""
        total = 0.0
        for i in range(len(route) - 1):
            total += distance_matrix[route[i]][route[i+1]]

        # If it's a round trip, add the distance from the last stop back to the start
        if is_round_trip and len(route) > 1:
            total += distance_matrix[route[-1]][route[0]]

        return total
