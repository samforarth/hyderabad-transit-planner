"""
Service for resolving and searching landmarks.
Converts user-friendly location names into coordinates using Nominatim,
and provides autocomplete functionality.
"""

import logging
import httpx
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.models.landmarks import Landmark
from app.models.gtfs import Stop
from app.config import settings

logger = logging.getLogger(__name__)

def resolve_landmark(name: str, db: Session) -> dict | None:
    """
    Resolve a landmark name to coordinates.
    
    Resolution order (prioritizes exact matches over partial):
    1. Exact match in landmarks cache (e.g., "patancheru" → Patancheruvu Bus Stand)
    2. Exact match in GTFS stops (e.g., "Charminar" → the stop named Charminar)
    3. Partial match in landmarks cache (e.g., "iith" → "iit hyderabad")
    4. Partial match in GTFS stops (e.g., "miyapur" → Miyapur Metro Station)
    5. Nominatim API call (external geocoding as last resort)
    
    Exact cache matches come first because they represent manually curated locations
    (like IITH campus stops) that should take priority over partial GTFS matches.
    """
    # Step 1: Exact match in landmarks cache
    cached_exact = db.query(Landmark).filter(Landmark.name.ilike(name)).first()
    if cached_exact:
        return {
            "name": cached_exact.display_name or cached_exact.name,
            "lat": cached_exact.lat,
            "lon": cached_exact.lon,
            "display_name": cached_exact.display_name
        }

    # Step 2: Exact match in GTFS stops
    stop_exact = db.query(Stop).filter(Stop.stop_name.ilike(name)).first()
    if stop_exact:
        return {
            "name": stop_exact.stop_name,
            "lat": stop_exact.stop_lat,
            "lon": stop_exact.stop_lon,
            "display_name": stop_exact.stop_desc or stop_exact.stop_name
        }

    # Step 3: Partial match in landmarks cache
    cached = db.query(Landmark).filter(Landmark.name.ilike(f"%{name}%")).first()
    if cached:
        return {
            "name": cached.display_name or cached.name,
            "lat": cached.lat,
            "lon": cached.lon,
            "display_name": cached.display_name
        }

    # Step 4: Partial match in GTFS stops
    stop = db.query(Stop).filter(Stop.stop_name.ilike(f"%{name}%")).first()
    if stop:
        return {
            "name": stop.stop_name,
            "lat": stop.stop_lat,
            "lon": stop.stop_lon,
            "display_name": stop.stop_desc or stop.stop_name
        }

    # Step 3: Cache miss — call Nominatim geocoding API
    # We use a wider viewbox to include the entire Hyderabad metro area
    # (IIT Hyderabad is at 78.12, which is near the western edge)
    url = "https://nominatim.openstreetmap.org/search"
    params = {
        "q": name,
        "format": "json",
        "countrycodes": "in",
        "limit": 5,
        "viewbox": "77.9,17.0,78.9,17.7",
        "bounded": 1
    }

    try:
        # Create a client with the User-Agent set at the client level.
        # Nominatim returns 403 if the User-Agent looks like a bot/library default.
        with httpx.Client(
            headers={"User-Agent": settings.NOMINATIM_USER_AGENT},
            timeout=10.0
        ) as client:
            response = client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

        if not data:
            return None

        first_result = data[0]
        result_dict = {
            "name": name,
            "lat": float(first_result["lat"]),
            "lon": float(first_result["lon"]),
            "display_name": first_result.get("display_name", name)
        }

        # Cache the result to avoid redundant network calls and rate limiting
        new_landmark = Landmark(
            name=name,
            lat=result_dict["lat"],
            lon=result_dict["lon"],
            display_name=result_dict["display_name"]
        )
        db.add(new_landmark)
        db.commit()

        return result_dict
    except httpx.HTTPStatusError as e:
        logger.error(f"Nominatim API error for '{name}': {e.response.status_code}")
        return None
    except httpx.RequestError as e:
        logger.error(f"Network error while resolving landmark '{name}': {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error resolving landmark '{name}': {e}")
        return None


def reverse_geocode(lat: float, lon: float) -> dict | None:
    """
    Convert GPS coordinates to a human-readable place name.
    Used when the user clicks on the map to select a location.
    """
    url = "https://nominatim.openstreetmap.org/reverse"
    params = {
        "lat": lat,
        "lon": lon,
        "format": "json",
        "zoom": 16,
    }

    try:
        with httpx.Client(
            headers={"User-Agent": settings.NOMINATIM_USER_AGENT},
            timeout=10.0
        ) as client:
            response = client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

        # Extract a short, human-friendly name from the address components.
        # Nominatim returns an "address" dict with keys like road, neighbourhood, suburb, etc.
        # We pick the most specific short name available.
        address = data.get("address", {})
        short_name = (
            address.get("amenity")
            or address.get("building")
            or address.get("road")
            or address.get("neighbourhood")
            or address.get("suburb")
            or data.get("name")
            or data.get("display_name", "Selected Location")
        )
        return {
            "name": short_name,
            "lat": lat,
            "lon": lon,
            "display_name": data.get("display_name", short_name)
        }
    except Exception as e:
        logger.error(f"Reverse geocoding failed for ({lat}, {lon}): {e}")
        # Even if reverse geocoding fails, we can still use the coordinates
        return {
            "name": f"Location ({lat:.4f}, {lon:.4f})",
            "lat": lat,
            "lon": lon,
            "display_name": f"Location ({lat:.4f}, {lon:.4f})"
        }

def search_autocomplete(query: str, db: Session, limit: int = 8) -> list:
    """
    Autocomplete search for stops and cached landmarks.
    Searches both stops and previously cached landmarks, returning a combined deduplicated list.
    Exact/prefix matches are sorted before substring matches so the most relevant result is first.
    """
    results = []
    seen_names = set()

    # Search stops table (case insensitive), fetch extra to allow deduplication
    stops = db.query(Stop).filter(Stop.stop_name.ilike(f"%{query}%")).limit(limit * 3).all()
    for stop in stops:
        name_key = stop.stop_name.lower()
        if name_key in seen_names:
            continue
        seen_names.add(name_key)
        results.append({
            "name": stop.stop_name,
            "type": "stop",
            "lat": stop.stop_lat,
            "lon": stop.stop_lon
        })

    # Search landmarks cache
    landmarks = db.query(Landmark).filter(Landmark.name.ilike(f"%{query}%")).limit(limit).all()
    for lm in landmarks:
        name_key = lm.name.lower()
        if name_key in seen_names:
            continue
        seen_names.add(name_key)
        results.append({
            "name": lm.display_name or lm.name,
            "type": "landmark",
            "lat": lm.lat,
            "lon": lm.lon
        })

    # Sort: exact match first, then prefix match, then substring match
    q_lower = query.lower()
    def sort_key(r):
        name = r["name"].lower()
        if name == q_lower:
            return 0  # Exact match
        if name.startswith(q_lower):
            return 1  # Prefix match
        return 2      # Substring match

    results.sort(key=sort_key)
    return results[:limit]
