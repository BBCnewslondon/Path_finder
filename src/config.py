"""
Configuration module for the delivery route optimizer.
Reads settings from config.ini and environment variables.
"""

import configparser
import os

# Create a config parser with default values
config = configparser.ConfigParser()

# --- General Defaults ---
config['defaults'] = {
    'map_output_file': 'route_map.html',
    'results_output_file': 'route_results.json'
}

# --- Optimization Defaults ---
config['optimization'] = {
    'default_algorithm': '2opt',
    'default_optimize_by': 'distance'
}

# --- Genetic Algorithm Defaults ---
config['genetic_algorithm'] = {
    'population_size': '100',
    'generations': '500'
}

# --- API Key Defaults ---
config['api_keys'] = {
    'OPENROUTESERVICE_API_KEY': '',
    'GOOGLE_MAPS_API_KEY': ''
}

# Read the config.ini file if it exists
config.read('config.ini')


# --- Helper functions to get config values ---

def get_api_key(key_name: str) -> str:
    """
    Get an API key.
    Priority: 1. Environment variable, 2. config.ini file.
    """
    # First, try to get from environment variable
    env_var = os.getenv(key_name)
    if env_var:
        return env_var

    # If not in env, get from config file
    return config.get('api_keys', key_name, fallback='')

# Expose settings for easy access
# API Keys are accessed via the helper function to respect env vars
ORS_API_KEY = get_api_key('OPENROUTESERVICE_API_KEY')
GOOGLE_API_KEY = get_api_key('GOOGLE_MAPS_API_KEY')

# Optimization settings
DEFAULT_ALGORITHM = config.get('optimization', 'default_algorithm')
DEFAULT_OPTIMIZE_BY = config.get('optimization', 'default_optimize_by')

# Genetic Algorithm settings
GA_POPULATION_SIZE = config.getint('genetic_algorithm', 'population_size')
GA_GENERATIONS = config.getint('genetic_algorithm', 'generations')

# Default filenames
DEFAULT_MAP_FILE = config.get('defaults', 'map_output_file')
DEFAULT_RESULTS_FILE = config.get('defaults', 'results_output_file')
