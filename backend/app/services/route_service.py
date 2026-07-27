"""
Service for generating possible bus journeys.
This is the core recommendation engine, producing direct and transfer-based itineraries.

Key design decision: Each journey leg includes a `stop_coords` array containing the
lat/lon of EVERY stop the bus passes through (board → intermediate → alight). This lets
the frontend draw realistic route lines that follow actual roads instead of straight lines.
"""

import logging
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.gtfs import StopTime, Trip, Route, Stop
from app.utils.time_utils import time_to_minutes, is_time_after

logger = logging.getLogger(__name__)


def get_leg_stop_coords(trip_id: str, board_seq: int, alight_seq: int, db: Session) -> list[dict]:
    """
    Fetches coordinates of ALL stops between board and alight (inclusive) for a trip.

    Why this matters:
    - Without this, we only have 2 points (board + alight) → straight line on the map
    - With this, we get 5–30 points → the line follows the actual bus route through each stop

    Returns a list of [lat, lon] pairs ordered by stop_sequence.
    """
    rows = (
        db.query(Stop.stop_lat, Stop.stop_lon, Stop.stop_name)
        .join(StopTime, StopTime.stop_id == Stop.stop_id)
        .filter(
            StopTime.trip_id == trip_id,
            StopTime.stop_sequence >= board_seq,
            StopTime.stop_sequence <= alight_seq,
        )
        .order_by(StopTime.stop_sequence)
        .all()
    )
    return [{"lat": row.stop_lat, "lon": row.stop_lon, "name": row.stop_name} for row in rows]


def find_direct_journeys(source_stops: list, dest_stops: list, departure_time: str, db: Session) -> list[dict]:
    """
    Finds trips that visit a source stop and then a destination stop directly without transfers.
    """
    journeys = []
    source_ids = [s["stop_id"] for s in source_stops]
    dest_ids = [d["stop_id"] for d in dest_stops]
    
    if not source_ids or not dest_ids:
        return journeys

    # Retrieve potential source stop times
    source_st_query = (
        db.query(StopTime, Trip, Route)
        .join(Trip, StopTime.trip_id == Trip.trip_id)
        .join(Route, Trip.route_id == Route.route_id)
        .filter(StopTime.stop_id.in_(source_ids))
        .all()
    )
    
    # Filter by departure time programmatically or in DB (doing in Python for simplicity here)
    valid_source_st = [
        (st, trip, route) for st, trip, route in source_st_query
        if is_time_after(st.departure_time, departure_time)
    ]
    
    # Sort to prioritize earliest departures
    valid_source_st.sort(key=lambda x: time_to_minutes(x[0].departure_time))
    
    # Check if these trips reach a destination stop later
    for st, trip, route in valid_source_st:
        dest_st = (
            db.query(StopTime)
            .filter(
                StopTime.trip_id == trip.trip_id,
                StopTime.stop_id.in_(dest_ids),
                StopTime.stop_sequence > st.stop_sequence
            )
            .first()
        )
        
        if dest_st:
            # Find matching stop metadata
            src_stop_meta = next((s for s in source_stops if s["stop_id"] == st.stop_id), None)
            dest_stop_meta = next((s for s in dest_stops if s["stop_id"] == dest_st.stop_id), None)
            
            if not src_stop_meta or not dest_stop_meta:
                continue

            board_time_mins = time_to_minutes(st.departure_time)
            alight_time_mins = time_to_minutes(dest_st.arrival_time)

            # Fetch all intermediate stop coordinates for this leg
            stop_coords = get_leg_stop_coords(
                trip.trip_id, st.stop_sequence, dest_st.stop_sequence, db
            )
            
            journeys.append({
                "legs": [{
                    "bus_number": route.route_short_name,
                    "route_id": route.route_id,
                    "trip_id": trip.trip_id,
                    "board_stop_id": st.stop_id,
                    "board_stop_name": src_stop_meta["stop_name"],
                    "alight_stop_id": dest_st.stop_id,
                    "alight_stop_name": dest_stop_meta["stop_name"],
                    "board_lat": src_stop_meta["lat"],
                    "board_lon": src_stop_meta["lon"],
                    "alight_lat": dest_stop_meta["lat"],
                    "alight_lon": dest_stop_meta["lon"],
                    "departure_time": st.departure_time,
                    "arrival_time": dest_st.arrival_time,
                    "num_intermediate_stops": dest_st.stop_sequence - st.stop_sequence - 1,
                    "stop_coords": stop_coords
                }],
                "total_duration_mins": alight_time_mins - board_time_mins,
                "transfers": 0
            })
            
            if len(journeys) >= 10:
                break
                
    return journeys

def find_transfer_journeys(source_stops: list, dest_stops: list, departure_time: str, db: Session) -> list[dict]:
    """
    Finds 1-transfer journeys.
    Conceptually similar to BFS: direct = depth 1, transfer = depth 2.

    Critical constraints:
    - Max 45 min wait at transfer stop (nobody waits 6 hours for a bus)
    - Connecting trips sorted by departure time (take earliest connection)
    - Only the best (earliest) connection per transfer stop is kept
    """
    MAX_TRANSFER_WAIT_MINS = 45  # No one waits longer than 45 minutes

    journeys = []
    source_ids = [s["stop_id"] for s in source_stops]
    dest_ids = [d["stop_id"] for d in dest_stops]
    
    if not source_ids or not dest_ids:
        return journeys

    # Get initial trips from sources
    source_st_query = (
        db.query(StopTime, Trip, Route)
        .join(Trip, StopTime.trip_id == Trip.trip_id)
        .join(Route, Trip.route_id == Route.route_id)
        .filter(StopTime.stop_id.in_(source_ids))
        .all()
    )
    
    valid_source_st = [
        (st, trip, route) for st, trip, route in source_st_query
        if is_time_after(st.departure_time, departure_time)
    ]

    # Filter out trips where we're boarding at the LAST stop (bus doesn't go anywhere from here).
    # Example: PTC→IITH bus arriving at IITH — boarding here has no onward stops for a transfer.
    filtered_source_st = []
    for st, trip, route in valid_source_st:
        has_onward = db.query(StopTime).filter(
            StopTime.trip_id == trip.trip_id,
            StopTime.stop_sequence > st.stop_sequence
        ).first()
        if has_onward:
            filtered_source_st.append((st, trip, route))
    valid_source_st = filtered_source_st
    valid_source_st.sort(key=lambda x: time_to_minutes(x[0].departure_time))

    # Deduplicate: guarantee every unique route gets its earliest trip included.
    # Without this, 30 campus shuttle trips could crowd out the PTC/Miyapur bus.
    # Two-pass approach:
    #   Pass 1: One trip per unique route (ensures diversity)
    #   Pass 2: Fill remaining slots with additional trips
    seen_routes = set()
    priority_entries = []  # One per route (guaranteed slots)
    extra_entries = []     # Additional trips (fill remaining capacity)

    for entry in valid_source_st:
        route_key = entry[2].route_id
        if route_key not in seen_routes:
            seen_routes.add(route_key)
            priority_entries.append(entry)
        else:
            extra_entries.append(entry)

    # Combine: priority first, then extras up to 30 total
    max_trips = 30
    valid_source_st = priority_entries + extra_entries[:max_trips - len(priority_entries)]

    # Track seen route combinations to avoid duplicates (same bus1 + bus2 combo)
    seen_combos = set()

    for leg1_st, leg1_trip, leg1_route in valid_source_st:
        # Get intermediate stops on leg1
        intermediate_stops = (
            db.query(StopTime, Stop)
            .join(Stop, StopTime.stop_id == Stop.stop_id)
            .filter(
                StopTime.trip_id == leg1_trip.trip_id,
                StopTime.stop_sequence > leg1_st.stop_sequence
            )
            .order_by(StopTime.stop_sequence)
            .limit(50)
            .all()
        )
        
        for leg1_dest_st, transfer_stop in intermediate_stops:
            arrival_at_transfer = time_to_minutes(leg1_dest_st.arrival_time)
            # Transfer window: wait at least 5 min, at most MAX_TRANSFER_WAIT_MINS
            min_transfer_time_mins = arrival_at_transfer + 5
            max_transfer_time_mins = arrival_at_transfer + MAX_TRANSFER_WAIT_MINS
            
            # Find connecting trips — SORTED by departure time so we get earliest first
            transfer_trips = (
                db.query(StopTime, Trip, Route)
                .join(Trip, StopTime.trip_id == Trip.trip_id)
                .join(Route, Trip.route_id == Route.route_id)
                .filter(StopTime.stop_id == transfer_stop.stop_id)
                .all()
            )

            # Sort by departure time in Python (faster than additional SQL sort for small sets)
            transfer_trips.sort(key=lambda x: time_to_minutes(x[0].departure_time))
            
            for leg2_st, leg2_trip, leg2_route in transfer_trips:
                leg2_depart_mins = time_to_minutes(leg2_st.departure_time)

                # Must not be the same bus
                if leg2_trip.trip_id == leg1_trip.trip_id:
                    continue

                # Too early — hasn't arrived yet + 5 min buffer
                if leg2_depart_mins < min_transfer_time_mins:
                    continue

                # Too late — exceeds max wait, skip remaining (they're sorted, so all later ones are worse)
                if leg2_depart_mins > max_transfer_time_mins:
                    break
                    
                # Does it reach destination?
                final_dest_st = (
                    db.query(StopTime)
                    .filter(
                        StopTime.trip_id == leg2_trip.trip_id,
                        StopTime.stop_id.in_(dest_ids),
                        StopTime.stop_sequence > leg2_st.stop_sequence
                    )
                    .first()
                )
                
                if final_dest_st:
                    src_stop_meta = next((s for s in source_stops if s["stop_id"] == leg1_st.stop_id), None)
                    dest_stop_meta = next((s for s in dest_stops if s["stop_id"] == final_dest_st.stop_id), None)
                    
                    if not src_stop_meta or not dest_stop_meta:
                        continue

                    # Deduplicate: skip if we already have this bus combination
                    combo_key = (leg1_route.route_short_name, leg2_route.route_short_name, 
                                 leg1_st.stop_id, final_dest_st.stop_id)
                    if combo_key in seen_combos:
                        continue
                    seen_combos.add(combo_key)
                        
                    board1_mins = time_to_minutes(leg1_st.departure_time)
                    alight2_mins = time_to_minutes(final_dest_st.arrival_time)
                    transfer_wait_mins = leg2_depart_mins - arrival_at_transfer

                    # Fetch intermediate stop coords for both legs
                    leg1_coords = get_leg_stop_coords(
                        leg1_trip.trip_id, leg1_st.stop_sequence, leg1_dest_st.stop_sequence, db
                    )
                    leg2_coords = get_leg_stop_coords(
                        leg2_trip.trip_id, leg2_st.stop_sequence, final_dest_st.stop_sequence, db
                    )

                    journeys.append({
                        "legs": [
                            {
                                "bus_number": leg1_route.route_short_name,
                                "route_id": leg1_route.route_id,
                                "trip_id": leg1_trip.trip_id,
                                "board_stop_id": leg1_st.stop_id,
                                "board_stop_name": src_stop_meta["stop_name"],
                                "alight_stop_id": leg1_dest_st.stop_id,
                                "alight_stop_name": transfer_stop.stop_name,
                                "board_lat": src_stop_meta["lat"],
                                "board_lon": src_stop_meta["lon"],
                                "alight_lat": transfer_stop.stop_lat,
                                "alight_lon": transfer_stop.stop_lon,
                                "departure_time": leg1_st.departure_time,
                                "arrival_time": leg1_dest_st.arrival_time,
                                "num_intermediate_stops": leg1_dest_st.stop_sequence - leg1_st.stop_sequence - 1,
                                "stop_coords": leg1_coords
                            },
                            {
                                "bus_number": leg2_route.route_short_name,
                                "route_id": leg2_route.route_id,
                                "trip_id": leg2_trip.trip_id,
                                "board_stop_id": leg2_st.stop_id,
                                "board_stop_name": transfer_stop.stop_name,
                                "alight_stop_id": final_dest_st.stop_id,
                                "alight_stop_name": dest_stop_meta["stop_name"],
                                "board_lat": transfer_stop.stop_lat,
                                "board_lon": transfer_stop.stop_lon,
                                "alight_lat": dest_stop_meta["lat"],
                                "alight_lon": dest_stop_meta["lon"],
                                "departure_time": leg2_st.departure_time,
                                "arrival_time": final_dest_st.arrival_time,
                                "num_intermediate_stops": final_dest_st.stop_sequence - leg2_st.stop_sequence - 1,
                                "stop_coords": leg2_coords
                            }
                        ],
                        "total_duration_mins": alight2_mins - board1_mins,
                        "transfer_wait_mins": transfer_wait_mins,
                        "transfers": 1
                    })
                    
                    # Found earliest valid connection at this transfer stop — move on
                    break
                    
            if len(journeys) >= 10:
                break
        if len(journeys) >= 10:
            break
                            
    return journeys

def generate_journeys(source_stops: list, dest_stops: list, departure_time: str, db: Session) -> list[dict]:
    """
    Main entry point for generating journeys. Try direct first, fallback/supplement with transfers.
    """
    direct = find_direct_journeys(source_stops, dest_stops, departure_time, db)
    
    # If we have very few direct journeys, add transfers to provide alternatives
    if len(direct) < 3:
        transfers = find_transfer_journeys(source_stops, dest_stops, departure_time, db)
        return direct + transfers
        
    return direct
