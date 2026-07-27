"""
API Endpoint: Recommend Journeys
=================================
The main endpoint of the application. Takes a source, destination, and departure time,
then runs the full recommendation pipeline:

    User Input → Landmark Resolution → Nearest Stops → Journey Generation → Scoring → Response

Example:
    POST /api/recommend
    {
        "source": "IIT Hyderabad",
        "destination": "IKEA",
        "departure_time": "21:30"
    }

    Response: {
        "recommended": { ... journey with best score ... },
        "alternatives": [ ... other options ... ],
        "source_info": { "name": ..., "lat": ..., "lon": ... },
        "destination_info": { "name": ..., "lat": ..., "lon": ... }
    }
"""

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.journey import SearchRequest
from app.services.landmark_service import resolve_landmark
from app.services.stop_service import find_nearby_stops
from app.services.route_service import generate_journeys
from app.services.recommendation_service import rank_journeys

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/recommend")
def recommend_journeys(request: SearchRequest, db: Session = Depends(get_db)):
    """
    Full recommendation pipeline.

    This is the core feature of the app. The pipeline has 5 stages:
    1. Resolve landmarks to coordinates (using Nominatim or cache)
    2. Find nearest bus stops to source and destination
    3. Generate possible journeys (direct + one-transfer)
    4. Score and rank journeys using weighted criteria
    5. Return the best recommendation with alternatives

    Why we structure it as a pipeline:
    - Each stage is independent and testable
    - We can swap out any stage (e.g., use Google Maps instead of Nominatim)
    - Errors at any stage produce clear, specific error messages
    """

    # ── Stage 1: Resolve landmarks to coordinates ──────────────────────
    source_info = resolve_landmark(name=request.source, db=db)
    if not source_info:
        raise HTTPException(
            status_code=404,
            detail=f"Could not find location: '{request.source}'. Try a more specific name.",
        )

    dest_info = resolve_landmark(name=request.destination, db=db)
    if not dest_info:
        raise HTTPException(
            status_code=404,
            detail=f"Could not find location: '{request.destination}'. Try a more specific name.",
        )

    logger.info(
        f"Resolved: '{request.source}' -> ({source_info['lat']}, {source_info['lon']})"
    )
    logger.info(
        f"Resolved: '{request.destination}' -> ({dest_info['lat']}, {dest_info['lon']})"
    )

    # ── Stage 2: Find nearest bus stops ────────────────────────────────
    # First try within 1.5 km. If no stops found, expand search to 5 km.
    # This handles remote locations like IIT Hyderabad (campus is far from city routes).
    source_stops = find_nearby_stops(
        lat=source_info["lat"], lon=source_info["lon"], db=db, max_radius=1500.0
    )
    if not source_stops:
        source_stops = find_nearby_stops(
            lat=source_info["lat"], lon=source_info["lon"], db=db, max_radius=5000.0
        )
    if not source_stops:
        raise HTTPException(
            status_code=404,
            detail=f"No bus stops found near '{request.source}'. This location may be too far from transit routes.",
        )

    dest_stops = find_nearby_stops(
        lat=dest_info["lat"], lon=dest_info["lon"], db=db, max_radius=1500.0
    )
    if not dest_stops:
        dest_stops = find_nearby_stops(
            lat=dest_info["lat"], lon=dest_info["lon"], db=db, max_radius=5000.0
        )
    if not dest_stops:
        raise HTTPException(
            status_code=404,
            detail=f"No bus stops found near '{request.destination}'. This location may be too far from transit routes.",
        )

    logger.info(
        f"Found {len(source_stops)} source stops, {len(dest_stops)} destination stops"
    )

    # ── Stage 3: Generate possible journeys ────────────────────────────
    # Convert departure_time from "HH:MM" to "HH:MM:SS" format for GTFS matching
    departure_time = request.departure_time
    if departure_time and len(departure_time) == 5:
        departure_time += ":00"

    journeys = generate_journeys(
        source_stops=source_stops,
        dest_stops=dest_stops,
        departure_time=departure_time,
        db=db,
    )

    if not journeys:
        raise HTTPException(
            status_code=404,
            detail="No bus routes found between these locations at the specified time. Try a different time.",
        )

    logger.info(f"Generated {len(journeys)} possible journeys")

    # ── Stage 4: Score and rank ────────────────────────────────────────
    # Build walking distance lookup for the scorer
    source_walking = {s["stop_id"]: s["distance_meters"] for s in source_stops}
    dest_walking = {s["stop_id"]: s["distance_meters"] for s in dest_stops}

    ranked = rank_journeys(
        journeys=journeys,
        source_walking=source_walking,
        dest_walking=dest_walking,
    )

    # ── Stage 5: Build response ────────────────────────────────────────
    return {
        "recommended": ranked["recommended"],
        "alternatives": ranked["alternatives"],
        "source_info": {
            "name": source_info["name"],
            "lat": source_info["lat"],
            "lon": source_info["lon"],
            "display_name": source_info.get("display_name", ""),
        },
        "destination_info": {
            "name": dest_info["name"],
            "lat": dest_info["lat"],
            "lon": dest_info["lon"],
            "display_name": dest_info.get("display_name", ""),
        },
    }
