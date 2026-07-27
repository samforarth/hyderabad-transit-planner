"""
API Endpoint: Route Details
============================
Returns detailed information about a specific bus route,
including all stops it serves and their timings.

Example:
    GET /api/route/219

    Response: {
        "route_id": "219",
        "route_name": "219",
        "stops": [
            {"stop_name": "Charminar", "lat": 17.358, "lon": 78.474, ...},
            ...
        ]
    }
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.database import get_db
from app.models.gtfs import Route, Trip, StopTime, Stop

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/route/{route_id}")
def get_route_details(
    route_id: str,
    direction: int = Query(0, ge=0, le=1, description="Direction: 0 or 1"),
    db: Session = Depends(get_db),
):
    """
    Returns all stops for a given route, ordered by sequence.

    Why we need a direction parameter:
    - Most bus routes have two directions (e.g., Charminar→IKEA and IKEA→Charminar).
    - In GTFS, direction_id=0 is typically "outbound" and direction_id=1 is "inbound".
    - We pick ONE representative trip for the route to show the stop sequence.
    """

    # Verify route exists
    route = db.query(Route).filter(Route.route_id == route_id).first()
    if not route:
        raise HTTPException(
            status_code=404,
            detail=f"Route '{route_id}' not found.",
        )

    # Find one representative trip for this route and direction
    # We just need any trip to get the stop sequence — they all follow the same path
    trip = (
        db.query(Trip)
        .filter(
            and_(
                Trip.route_id == route_id,
                Trip.direction_id == direction,
            )
        )
        .first()
    )

    if not trip:
        raise HTTPException(
            status_code=404,
            detail=f"No trips found for route '{route_id}' in direction {direction}.",
        )

    # Get all stops for this trip, ordered by sequence
    stop_times = (
        db.query(StopTime, Stop)
        .join(Stop, StopTime.stop_id == Stop.stop_id)
        .filter(StopTime.trip_id == trip.trip_id)
        .order_by(StopTime.stop_sequence)
        .all()
    )

    stops = []
    for stop_time, stop in stop_times:
        stops.append(
            {
                "sequence": stop_time.stop_sequence,
                "stop_id": stop.stop_id,
                "stop_name": stop.stop_name,
                "lat": stop.stop_lat,
                "lon": stop.stop_lon,
                "arrival_time": stop_time.arrival_time,
                "departure_time": stop_time.departure_time,
            }
        )

    return {
        "route_id": route.route_id,
        "route_name": route.route_short_name,
        "direction": direction,
        "trip_id": trip.trip_id,
        "total_stops": len(stops),
        "stops": stops,
    }
