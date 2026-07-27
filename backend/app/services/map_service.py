"""
Service for generating map data for the Leaflet frontend.
Provides geometry, bounds, and styling information for rendering journeys.
"""

import logging
import hashlib
from sqlalchemy.orm import Session
from app.models.gtfs import StopTime, Stop

logger = logging.getLogger(__name__)

def generate_route_color(bus_number: str) -> str:
    """
    Hash a bus number to generate a consistent hex color.
    Uses HSL concept to keep saturation/lightness pleasant but varying hue.
    """
    hash_val = int(hashlib.md5(bus_number.encode('utf-8')).hexdigest(), 16)
    hue = hash_val % 360
    # Simple mapping to vibrant colors, skipping actual HSL to HEX math for brevity,
    # just generating a pseudo-random hex based on hash.
    r = (hash_val & 0xFF0000) >> 16
    g = (hash_val & 0x00FF00) >> 8
    b = hash_val & 0x0000FF
    
    # Ensure it's not too bright or too dark
    r = max(50, min(200, r))
    g = max(50, min(200, g))
    b = max(50, min(200, b))
    
    return f"#{r:02x}{g:02x}{b:02x}"

def get_route_stops(route_id: str, trip_id: str, db: Session) -> list[dict]:
    """
    Returns ordered list of all stops for a specific trip.
    """
    stops_query = (
        db.query(StopTime, Stop)
        .join(Stop, StopTime.stop_id == Stop.stop_id)
        .filter(StopTime.trip_id == trip_id)
        .order_by(StopTime.stop_sequence)
        .all()
    )
    
    result = []
    for st, stop in stops_query:
        result.append({
            "stop_id": stop.stop_id,
            "stop_name": stop.stop_name,
            "lat": stop.stop_lat,
            "lon": stop.stop_lon,
            "arrival_time": st.arrival_time,
            "departure_time": st.departure_time,
            "sequence": st.stop_sequence
        })
    return result

def get_journey_map_data(journey: dict, source_coords: dict, dest_coords: dict, db: Session) -> dict:
    """
    Compiles all geographical data needed by the frontend to draw a journey on the map.
    """
    bus_segments = []
    transfer_points = []
    
    lats = [source_coords["lat"], dest_coords["lat"]]
    lons = [source_coords["lon"], dest_coords["lon"]]
    
    for i, leg in enumerate(journey["legs"]):
        color = generate_route_color(leg["bus_number"])
        
        # We put the boarding and alighting stops as a straight line 
        # (or fetch intermediate stops via get_route_stops if we had trip_id in the leg).
        
        bus_segments.append({
            "bus_number": leg["bus_number"],
            "color": color,
            "stops": [
                {
                    "lat": leg["board_lat"],
                    "lon": leg["board_lon"],
                    "name": leg["board_stop_name"],
                    "is_board": True,
                    "is_alight": False
                },
                {
                    "lat": leg["alight_lat"],
                    "lon": leg["alight_lon"],
                    "name": leg["alight_stop_name"],
                    "is_board": False,
                    "is_alight": True
                }
            ]
        })
        
        lats.extend([leg["board_lat"], leg["alight_lat"]])
        lons.extend([leg["board_lon"], leg["alight_lon"]])
        
        # If there's a subsequent leg, the alight point is a transfer point
        if i < len(journey["legs"]) - 1:
            transfer_points.append({
                "lat": leg["alight_lat"],
                "lon": leg["alight_lon"],
                "name": leg["alight_stop_name"]
            })

    bounds = {
        "north": max(lats),
        "south": min(lats),
        "east": max(lons),
        "west": min(lons)
    }
    
    return {
        "source_marker": {"lat": source_coords["lat"], "lon": source_coords["lon"], "name": source_coords.get("name", "Origin")},
        "dest_marker": {"lat": dest_coords["lat"], "lon": dest_coords["lon"], "name": dest_coords.get("name", "Destination")},
        "walking_segments": [], # Simplified for this requirement
        "bus_segments": bus_segments,
        "transfer_points": transfer_points,
        "bounds": bounds
    }
