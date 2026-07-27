"""
API Endpoint: Search / Autocomplete
====================================
Provides search suggestions as the user types in the source or destination field.
Searches both bus stop names (from GTFS data) and cached landmark names.

Example:
    GET /api/search?q=char&limit=5

    Response: [
        {"name": "Charminar", "type": "stop", "lat": 17.358, "lon": 78.474},
        {"name": "Char Minar Road", "type": "landmark", "lat": 17.360, "lon": 78.475}
    ]
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.landmark_service import search_autocomplete

router = APIRouter()


@router.get("/search")
def search_locations(
    q: str = Query(..., min_length=1, description="Search query string"),
    limit: int = Query(8, ge=1, le=20, description="Max number of results"),
    db: Session = Depends(get_db),
):
    """
    Autocomplete endpoint for the search form.

    Why we combine stops + landmarks:
    - Users might type a bus stop name ("Charminar") or a landmark ("IKEA").
    - We search both sources and merge the results so the user always finds what they need.
    - Stop results come from our MySQL database (fast), landmark results from cache.
    """
    results = search_autocomplete(query=q, db=db, limit=limit)
    return results
