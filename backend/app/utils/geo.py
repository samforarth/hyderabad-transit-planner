"""
Geographic utility functions.

Contains functions for calculating distances between coordinates and finding 
nearby geographic entities.
"""

import math
from typing import List, Tuple, Any

def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great circle distance between two points on the earth.
    
    Returns the distance in METERS.
    """
    # Convert latitude and longitude from degrees to radians
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)

    # Difference in coordinates
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad

    # Haversine formula
    # a is the square of half the chord length between the points
    a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
    
    # c is the angular distance in radians
    c = 2 * math.asin(math.sqrt(a))

    # Radius of earth in meters (mean radius)
    r = 6371000.0
    
    # Calculate the result
    return c * r

def find_nearest_stops(lat: float, lon: float, all_stops: List[Any], limit: int = 5, max_radius: float = 1500.0) -> List[Tuple[Any, float]]:
    """
    Find the closest stops to a given geographic coordinate.
    
    We pick the top `limit` stops (default 5) instead of just the absolute nearest one,
    because the closest stop might not have routes going to the user's destination,
    or a stop slightly further away might offer a direct route (avoiding a transfer).
    """
    stops_with_distances = []
    
    for stop in all_stops:
        distance = haversine(lat, lon, stop.stop_lat, stop.stop_lon)
        if distance <= max_radius:
            stops_with_distances.append((stop, distance))
            
    # Sort by distance (the second element of the tuple)
    stops_with_distances.sort(key=lambda x: x[1])
    
    # Return the top 'limit' stops
    return stops_with_distances[:limit]
