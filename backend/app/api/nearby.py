"""
API Endpoint: Nearby Stops
============================
Returns bus stops within a given radius of a coordinate point.
Used by the map view to show stops near the user's location.

Example:
    GET /api/nearby?lat=17.3586&lon=78.4740&radius=1000

    Response: {
        "center": {"lat": 17.3586, "lon": 78.4740},
        "radius_meters": 1000,
        "count": 12,
        "stops": [
            {"stop_id": "RgqMpbyP", "stop_name": "Charminar", "lat": 17.358, ...},
            ...
        ]
    }
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.stop_service import find_nearby_stops

router = APIRouter()


@router.get("/nearby")
def get_nearby_stops(
    lat: float = Query(..., ge=-90, le=90, description="Latitude"),
    lon: float = Query(..., ge=-180, le=180, description="Longitude"),
    radius: float = Query(1000, ge=100, le=5000, description="Search radius in meters"),
    limit: int = Query(20, ge=1, le=50, description="Max number of stops"),
    db: Session = Depends(get_db),
):
    """
    Find bus stops near a given location.

    Why this is useful:
    - The map view shows nearby stops when the user pans/zooms.
    - Users can tap on the map to see what buses serve an area.
    - The radius parameter lets us adjust density based on zoom level.
    """
    stops = find_nearby_stops(
        lat=lat,
        lon=lon,
        db=db,
        limit=limit,
        max_radius=radius,
    )

    return {
        "center": {"lat": lat, "lon": lon},
        "radius_meters": radius,
        "count": len(stops),
        "stops": stops,
    }
