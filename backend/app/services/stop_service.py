"""
Service for bus stop operations.
Handles retrieval of stops, proximity searches, and identifying routes serving specific stops.
"""

import logging
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.gtfs import Stop, StopTime, Trip, Route
from app.utils.geo import haversine

logger = logging.getLogger(__name__)

# Module-level cache for stops. 
# We cache all 4,710 stops in memory because computing distances dynamically for thousands 
# of queries would be slow and memory usage for ~5k objects is minimal.
_STOPS_CACHE = []

def get_all_stops(db: Session) -> list[Stop]:
    """
    Returns all stops from DB. Caches them in a module-level variable after the first call.
    """
    global _STOPS_CACHE
    if not _STOPS_CACHE:
        logger.info("Loading all stops into memory cache.")
        _STOPS_CACHE = db.query(Stop).all()
    return _STOPS_CACHE

def find_nearby_stops(lat: float, lon: float, db: Session, limit: int = 5, max_radius: float = 1500.0) -> list[dict]:
    """
    Finds bus stops near a specific location.
    We return the top 'limit' stops rather than just the single nearest one because the absolute
    nearest stop might have very few active routes, whereas a slightly further one could be a major hub.
    """
    all_stops = get_all_stops(db)
    nearby = []
    
    for stop in all_stops:
        dist = haversine(lat, lon, stop.stop_lat, stop.stop_lon)
        if dist <= max_radius:
            nearby.append({
                "stop_id": stop.stop_id,
                "stop_name": stop.stop_name,
                "lat": stop.stop_lat,
                "lon": stop.stop_lon,
                "distance_meters": dist
            })
            
    # Sort by distance
    nearby.sort(key=lambda x: x["distance_meters"])
    
    return nearby[:limit]

def get_routes_at_stop(stop_id: str, db: Session) -> list[str]:
    """
    Finds all unique route_short_names (bus numbers) that serve a given stop.
    """
    # Join StopTime -> Trip -> Route to find all routes serving the stop
    # Distinct is used to get unique bus numbers
    routes = (
        db.query(Route.route_short_name)
        .join(Trip, Trip.route_id == Route.route_id)
        .join(StopTime, StopTime.trip_id == Trip.trip_id)
        .filter(StopTime.stop_id == stop_id)
        .distinct()
        .all()
    )
    
    return [r[0] for r in routes if r[0]]
