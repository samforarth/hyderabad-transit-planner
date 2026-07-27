"""
API Endpoint: Reverse Geocode
==============================
Converts GPS coordinates from a map click into a place name.
Used by the frontend when users click on the map to select source/destination.
"""

from fastapi import APIRouter, Query
from app.services.landmark_service import reverse_geocode

router = APIRouter()


@router.get("/reverse-geocode")
def reverse_geocode_endpoint(
    lat: float = Query(..., description="Latitude"),
    lon: float = Query(..., description="Longitude"),
):
    """
    Takes lat/lon coordinates and returns a place name using Nominatim reverse geocoding.
    This powers the "click on map" feature.
    """
    result = reverse_geocode(lat, lon)
    return result or {"name": f"({lat:.4f}, {lon:.4f})", "lat": lat, "lon": lon}
