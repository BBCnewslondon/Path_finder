"""
Streamlit frontend for the Delivery Route Optimizer.
"""

import streamlit as st
from streamlit_folium import st_folium
import sys
import os

# This is a workaround to make the src module available to Streamlit
# In a real-world scenario, this would be handled by a proper package installation
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from main import DeliveryRouteApp
from src.utils import print_route_summary


st.set_page_config(layout="wide")

st.title("🚚 Delivery Route Optimizer")
st.write("Enter a list of addresses below (one per line) to find the optimal delivery route.")

# --- UI Inputs ---

col1, col2 = st.columns([2, 1])

with col1:
    addresses_input = st.text_area(
        "Delivery Addresses",
        height=250,
        placeholder="123 Main St, Anytown, USA\n456 Oak Ave, Anytown, USA\n..."
    )

with col2:
    st.subheader("Route Options")
    algorithm = st.selectbox("Optimization Algorithm", ['2opt', 'nearest_neighbor', 'ortools', 'genetic'])
    optimize_by = st.selectbox("Optimize For", ['distance', 'time'])
    use_real_roads = st.checkbox("Use Real Roads", value=True)

    start_address_override = st.text_input("Start Address (optional)", help="If blank, uses the first address in the list.")
    end_address_override = st.text_input("End Address (optional)", help="If blank, creates a round trip returning to the start.")

# --- Route Calculation ---

if st.button("Generate Optimized Route", type="primary"):
    addresses = [addr.strip() for addr in addresses_input.split('\n') if addr.strip()]

    if len(addresses) < 2:
        st.error("Please enter at least two addresses.")
    else:
        with st.spinner("Calculating route... This may take a moment."):
            try:
                # Initialize the main app
                app = DeliveryRouteApp(use_real_roads=use_real_roads)

                # We need to capture the output of print_route_summary
                # and the generated map from the backend logic.
                # This requires a slight refactor of the main app class.
                # For now, let's just call the optimizer and see if we can get a map.

                # A better approach would be for optimize_delivery_route to RETURN the results
                # instead of printing them. Let's assume we refactor it to do that.

                # --- Refactoring main.py would be ideal, but for now, let's adapt ---

                # 1. Geocode addresses
                geocode_results = app.geocoder.geocode_addresses(addresses)
                valid_addresses = [addr for addr, coords in geocode_results.items() if coords]
                valid_coordinates = [coords for coords in geocode_results.values() if coords]

                if len(valid_addresses) < 2:
                    st.error("Could not geocode at least two addresses. Please check your input.")
                else:
                    st.info(f"Successfully geocoded {len(valid_addresses)} out of {len(addresses)} addresses.")

                    # 2. Get cost matrix
                    if optimize_by == 'time':
                        cost_matrix = app.distance_calculator.get_duration_matrix(valid_coordinates)
                    else:
                        cost_matrix = app.distance_calculator.calculate_distance_matrix(valid_coordinates)

                    # 3. Determine start/end points
                    start_index = 0
                    if start_address_override and start_address_override in valid_addresses:
                        start_index = valid_addresses.index(start_address_override)

                    end_index = None
                    if end_address_override and end_address_override in valid_addresses:
                        end_index = valid_addresses.index(end_address_override)

                    # 4. Optimize route
                    app.route_optimizer.algorithm = algorithm
                    route_order, total_cost = app.route_optimizer.optimize_route(
                        cost_matrix, start_index, end_index
                    )

                    # 5. Display Results
                    st.subheader("Optimized Route")

                    ordered_addresses = [valid_addresses[i] for i in route_order]
                    for i, address in enumerate(ordered_addresses):
                        st.write(f"**{i+1}.** {address}")

                    cost_unit = "km" if optimize_by == 'distance' else 'hours'
                    st.success(f"**Total Optimized {optimize_by.capitalize()}:** {total_cost:.2f} {cost_unit}")

                    # 6. Generate and display map
                    map_file = "frontend_route_map.html"
                    map_path = app.map_generator.create_route_map(
                        valid_addresses, valid_coordinates, route_order, map_file, use_real_roads
                    )

                    with open(map_path, 'r', encoding='utf-8') as f:
                        map_html = f.read()

                    # Display the map outside the columns to use full width
                    st.components.v1.html(map_html, height=800, scrolling=True)

            except Exception as e:
                st.error(f"An error occurred: {e}")
else:
    st.info("Enter addresses and click 'Generate' to see your optimized route map here.")
