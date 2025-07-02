"""
Route optimization module implementing multiple TSP solving algorithms.
"""

from typing import List, Tuple, Optional, Dict, Any
import random
import numpy as np
from itertools import permutations
import time

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
                      start_index: int = 0) -> Tuple[List[int], float]:
        """
        Find optimal route given a distance matrix.
        
        Args:
            distance_matrix: 2D matrix of distances between points
            start_index: Index of starting point
            
        Returns:
            Tuple of (route_indices, total_distance)
        """
        if self.algorithm not in self.algorithms:
            raise ValueError(f"Unknown algorithm: {self.algorithm}")
        
        if len(distance_matrix) <= 1:
            return [0], 0.0
        
        return self.algorithms[self.algorithm](distance_matrix, start_index)
    
    def _nearest_neighbor(self, distance_matrix: List[List[float]], 
                         start_index: int = 0) -> Tuple[List[int], float]:
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
        
        while unvisited:
            # Find nearest unvisited node
            nearest = min(unvisited, key=lambda x: distance_matrix[current][x])
            total_distance += distance_matrix[current][nearest]
            route.append(nearest)
            unvisited.remove(nearest)
            current = nearest
        
        # Return to start
        total_distance += distance_matrix[current][start_index]
        
        return route, total_distance
    
    def _two_opt(self, distance_matrix: List[List[float]], 
                start_index: int = 0) -> Tuple[List[int], float]:
        """
        2-opt improvement algorithm.
        Starts with nearest neighbor and improves with local search.
        """
        # Start with nearest neighbor solution
        route, _ = self._nearest_neighbor(distance_matrix, start_index)
        
        improved = True
        while improved:
            improved = False
            for i in range(1, len(route) - 1):
                for j in range(i + 1, len(route)):
                    # Try swapping edges
                    new_route = route[:]
                    new_route[i:j+1] = reversed(new_route[i:j+1])
                    
                    if self._calculate_route_distance(new_route, distance_matrix) < \
                       self._calculate_route_distance(route, distance_matrix):
                        route = new_route
                        improved = True
        
        total_distance = self._calculate_route_distance(route, distance_matrix)
        return route, total_distance
    
    def _ortools_solver(self, distance_matrix: List[List[float]], 
                       start_index: int = 0) -> Tuple[List[int], float]:
        """
        Google OR-Tools exact TSP solver.
        Provides optimal solutions for small to medium datasets.
        """
        if not ORTOOLS_AVAILABLE:
            print("OR-Tools not available, falling back to 2-opt")
            return self._two_opt(distance_matrix, start_index)
        
        n = len(distance_matrix)
        
        # Create the routing index manager
        manager = pywrapcp.RoutingIndexManager(n, 1, start_index)
        
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
                          population_size: int = 100,
                          generations: int = 500) -> Tuple[List[int], float]:
        """
        Genetic algorithm for TSP.
        Good for larger datasets where exact solutions are impractical.
        """
        n = len(distance_matrix)
        if n <= 3:
            return self._nearest_neighbor(distance_matrix, start_index)
        
        # Create initial population
        population = []
        for _ in range(population_size):
            route = list(range(n))
            if start_index != 0:
                route.remove(start_index)
                route = [start_index] + route
            else:
                route = route[1:]  # Remove start from middle
                random.shuffle(route)
                route = [start_index] + route
            population.append(route)
        
        for generation in range(generations):
            # Evaluate fitness (inverse of distance)
            fitness_scores = []
            for route in population:
                distance = self._calculate_route_distance(route, distance_matrix)
                fitness_scores.append(1 / (distance + 1))
            
            # Selection and crossover
            new_population = []
            for _ in range(population_size):
                # Tournament selection
                parent1 = self._tournament_selection(population, fitness_scores)
                parent2 = self._tournament_selection(population, fitness_scores)
                
                # Order crossover
                child = self._order_crossover(parent1, parent2)
                
                # Mutation
                if random.random() < 0.1:
                    child = self._mutate_route(child)
                
                new_population.append(child)
            
            population = new_population
        
        # Return best route
        best_route = min(population, 
                        key=lambda r: self._calculate_route_distance(r, distance_matrix))
        best_distance = self._calculate_route_distance(best_route, distance_matrix)
        
        return best_route, best_distance
    
    def _tournament_selection(self, population: List[List[int]], 
                            fitness_scores: List[float], 
                            tournament_size: int = 3) -> List[int]:
        """Tournament selection for genetic algorithm."""
        tournament_indices = random.sample(range(len(population)), tournament_size)
        tournament_fitness = [fitness_scores[i] for i in tournament_indices]
        winner_index = tournament_indices[tournament_fitness.index(max(tournament_fitness))]
        return population[winner_index]
    
    def _order_crossover(self, parent1: List[int], parent2: List[int]) -> List[int]:
        """Order crossover operator for genetic algorithm."""
        n = len(parent1)
        start, end = sorted(random.sample(range(1, n), 2))  # Skip start city
        
        child = [-1] * n
        child[0] = parent1[0]  # Keep start city
        child[start:end] = parent1[start:end]
        
        remaining = [x for x in parent2 if x not in child]
        j = 0
        for i in range(1, n):
            if child[i] == -1:
                child[i] = remaining[j]
                j += 1
        
        return child
    
    def _mutate_route(self, route: List[int]) -> List[int]:
        """Mutation operator for genetic algorithm."""
        route = route[:]
        # Swap two random cities (not the start city)
        if len(route) > 3:
            i, j = random.sample(range(1, len(route)), 2)
            route[i], route[j] = route[j], route[i]
        return route
    
    def _calculate_route_distance(self, route: List[int], 
                                distance_matrix: List[List[float]]) -> float:
        """Calculate total distance for a route."""
        total = 0.0
        for i in range(len(route) - 1):
            total += distance_matrix[route[i]][route[i + 1]]
        # Add return to start
        total += distance_matrix[route[-1]][route[0]]
        return total
