import pandas as pd
from typing import Union

def compute_travel_speed(
    ship_row: Union[dict, pd.Series, None], 
    engine_row: Union[dict, pd.Series, None]
) -> float:
    """
    Compute realistic X4-style travel speed.

    Formula:
        travel_speed = (forward_thrust * travel_thrust * engine_connections) / drag_forward

    Required fields:
        ship_row: {
            "drag (forward)": float,
            "engine_connections": int,    # number of engine connection points
        }
        engine_row: {
            "forward_thrust": float,      # from <thrust forward="3159" reverse="3001.05" />
            "travel_thrust": float,       # from <travel thrust="42.4" ... />
        }
    """
    
    # Treat pandas Series/empty rows correctly: only bail out on None or empty Series/Mapping
    if ship_row is None or engine_row is None:
        return 0.0
    
    # Check for empty pandas Series
    if isinstance(ship_row, pd.Series) and ship_row.empty:
        return 0.0
    if isinstance(engine_row, pd.Series) and engine_row.empty:
        return 0.0
    
    # Check for empty dictionaries
    if isinstance(ship_row, dict) and not ship_row:
        return 0.0
    if isinstance(engine_row, dict) and not engine_row:
        return 0.0

    # Calculate travel speed using X4 formula
    engine_thrust_forward = engine_row.get("forward_thrust", 0.0)
    travel_thrust = engine_row.get("travel_thrust", 0.0)
    ship_drag_forward = ship_row.get("drag (forward)", 1.0)
    engine_connections = ship_row.get("engine_connections", 1)
    
    if ship_drag_forward <= 0:
        ship_drag_forward = 1e-6
    if engine_connections <= 0:
        engine_connections = 1  # Minimum of 1 engine
    
    travel_speed = (engine_thrust_forward * travel_thrust * engine_connections) / ship_drag_forward
    return travel_speed
