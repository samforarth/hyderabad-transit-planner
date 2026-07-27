"""
Import IIT Hyderabad Campus Bus Schedules
==========================================
Imports three bus services into the GTFS database:

1. CAMPUS SHUTTLE (Bus1–Bus4 + 10-Seater)
   Route: Maingate ↔ Hospital ↔ Hostel Circle
   Runs every 10-15 minutes from ~7:30 AM to ~11:45 PM

2. MIYAPUR BUS
   Route: Miyapur ↔ IITH (Mon-Fri only)
   Departs: 7:40 from Miyapur, 17:45 from IITH

3. PATANCHERU (PTC) BUS
   Route: Patancheru ↔ IITH
   Runs: 6 trips each way, all days

These buses connect IITH campus to the TSRTC city bus network at Miyapur
and Patancheru, enabling journeys like "IIT Hyderabad → Charminar" via transfers.

Source: IIT Hyderabad Transport Office schedule (PDF)
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text
from app.database import SessionLocal, engine
from app.models.gtfs import Agency, Calendar, Route, Trip, Stop, StopTime


# ──────────────────────────────────────────────────────────────────────
# IITH Campus Stop Coordinates (approximate, from campus map)
# ──────────────────────────────────────────────────────────────────────
IITH_STOPS = {
    "IITH_MAINGATE":      {"name": "IITH Main Gate",       "lat": 17.5913, "lon": 78.1195},
    "IITH_HOSPITAL":      {"name": "IITH Hospital",        "lat": 17.5935, "lon": 78.1175},
    "IITH_HOSTEL_CIRCLE": {"name": "IITH Hostel Circle",   "lat": 17.5960, "lon": 78.1150},
}

# Existing TSRTC stops (already in DB) that IITH buses connect to
MIYAPUR_STOP_ID = "NZVBKXVQ"      # Miyapur (17.4967, 78.3608)
PATANCHERU_STOP_ID = "enXMW3fY"    # Patancheruvu (17.529, 78.2643)


# ──────────────────────────────────────────────────────────────────────
# Campus Shuttle Schedule (extracted from PDF)
# Direction 0: Maingate → Hospital → Hostel Circle
# Direction 1: Hostel Circle → Hospital → Maingate
# Travel time between adjacent stops: ~5 minutes
# ──────────────────────────────────────────────────────────────────────

# Departure times from starting point (HH:MM:SS)
# Each pair represents: (direction, departure_time)
# direction 0 = Maingate→Hostel, direction 1 = Hostel→Maingate

SHUTTLE_SCHEDULE = []

# Bus1 departures (from the PDF table)
bus1_maingate = [
    "08:00", "08:40", "09:10", "09:20", "09:40", "09:50",
    "10:15", "10:30", "12:00", "12:30", "12:45", "13:10",
    "13:20", "13:40", "13:50", "14:10", "14:20", "14:45",
    "15:00", "15:30", "15:45", "16:15", "16:30", "17:00",
    "17:15", "17:40", "17:50", "18:10", "18:20", "18:40",
    "18:50", "19:10", "19:20",
]
bus1_hostel = [
    "08:15", "08:50", "09:00", "09:30", "09:40", "10:00",
    "10:15", "10:30", "11:45", "12:15", "12:30", "12:45",
    "13:00", "13:20", "13:30", "13:50", "14:00", "14:20",
    "14:30", "14:45", "15:00", "15:15", "15:30", "16:00",
    "16:15", "16:45", "17:00", "17:40", "17:50", "18:10",
    "18:20", "18:40", "18:50", "19:10",
]

# Bus2 departures
bus2_maingate = [
    "08:15", "08:50", "09:20", "09:40", "09:50", "10:30",
    "10:45", "11:15", "12:15", "12:45", "13:00", "13:20",
    "13:30", "13:50", "14:00", "14:20", "14:30", "15:00",
    "15:15", "15:45", "16:00", "16:30", "16:45", "17:15",
    "17:30", "17:50", "18:00", "18:20", "18:30", "18:50",
    "19:00", "19:20", "19:30", "20:30", "20:45",
]
bus2_hostel = [
    "07:45", "08:30", "09:00", "09:30", "09:50", "10:00",
    "10:30", "10:45", "11:15", "12:30", "12:45", "13:00",
    "13:10", "13:30", "13:40", "14:00", "14:10", "14:30",
    "14:45", "15:00", "15:15", "15:45", "16:00", "16:30",
    "16:45", "17:00", "17:30", "17:50", "18:00", "18:30",
    "18:50", "19:00", "19:30", "19:45", "21:00",
]

# Bus3 departures
bus3_maingate = [
    "08:30", "09:00", "09:30", "09:40", "10:00", "10:45",
    "11:00", "11:45", "12:00", "12:45", "13:00", "13:10",
    "13:30", "13:40", "14:00", "14:10", "14:30", "14:45",
    "15:15", "15:30", "16:00", "16:05", "16:35", "16:50",
    "17:30", "17:40", "18:00", "18:10", "18:30", "18:40",
    "19:00", "19:10", "19:30", "19:45", "20:00", "20:15",
    "20:30", "20:45",
]
bus3_hostel = [
    "07:45", "08:00", "08:40", "09:10", "09:30", "09:50",
    "10:00", "10:15", "10:45", "11:15", "11:30", "12:15",
    "12:30", "13:00", "13:10", "13:30", "13:40", "14:00",
    "14:10", "14:30", "14:45", "15:15", "15:30", "16:00",
    "16:20", "16:50", "17:05", "17:30", "17:50", "18:00",
    "18:30", "18:40", "19:00", "19:10", "19:30", "19:45",
    "20:00", "20:30",
]

# Bus4 departures (fewer trips, mostly evening)
bus4_maingate = [
    "16:05", "16:20", "16:50", "17:05", "17:30", "17:35",
    "17:50", "18:05", "18:20", "18:35",
]
bus4_hostel = [
    "16:50", "17:05", "17:30", "17:50", "18:00",
    "18:20", "18:35",
]

# 10-Seater (smaller shuttle, evening/night)
seater10_maingate = [
    "00:00", "00:20", "00:30", "00:40", "00:50", "01:00",
    "01:10", "01:20", "01:30", "01:40", "01:50", "02:00",
    "02:10", "02:20", "02:30", "03:30", "03:45", "04:00",
    "04:15", "04:30", "04:45", "05:00", "05:15", "05:30",
    "05:45", "06:00", "06:15", "06:30", "06:45", "07:00",
    "07:10", "07:20", "07:30", "20:20", "20:35", "20:50",
    "21:05", "21:20", "21:35", "21:50", "22:30", "22:45",
    "23:00", "23:05", "23:20", "23:35", "23:50",
]
seater10_hostel = [
    "00:10", "00:20", "00:30", "00:50", "01:00",
    "01:10", "01:20", "01:30", "01:40", "01:50", "02:05",
    "02:20", "02:35", "02:50", "03:30", "03:45", "04:00",
    "04:15", "04:30", "04:45", "05:00", "05:15", "05:30",
    "05:45", "06:00", "06:15", "06:30", "06:45", "07:00",
    "07:10", "07:20", "07:30", "20:10", "20:35", "20:50",
    "21:05", "21:20", "21:35", "21:50", "22:30", "22:45",
    "23:05", "23:20", "23:35", "23:50",
]

# Build the full schedule
for times in [bus1_maingate, bus2_maingate, bus3_maingate, bus4_maingate, seater10_maingate]:
    for t in times:
        SHUTTLE_SCHEDULE.append((0, t))  # direction 0 = Maingate → Hostel

for times in [bus1_hostel, bus2_hostel, bus3_hostel, bus4_hostel, seater10_hostel]:
    for t in times:
        SHUTTLE_SCHEDULE.append((1, t))  # direction 1 = Hostel → Maingate

# Remove duplicates and sort
SHUTTLE_SCHEDULE = sorted(set(SHUTTLE_SCHEDULE), key=lambda x: (x[0], x[1]))


# ──────────────────────────────────────────────────────────────────────
# Miyapur Bus Schedule
# ──────────────────────────────────────────────────────────────────────
# Miyapur → IITH: 7:40 (Mon-Fri), ~60 min travel
# IITH → Miyapur: 17:45 (Mon-Fri), ~60 min travel

MIYAPUR_SCHEDULE = [
    # (direction, departure_time, travel_mins)
    (0, "07:40", 60),   # Miyapur → IITH
    (1, "17:45", 60),   # IITH → Miyapur
]


# ──────────────────────────────────────────────────────────────────────
# Patancheru (PTC) Bus Schedule
# ──────────────────────────────────────────────────────────────────────
# PTC → IITH and IITH → PTC, all days, ~35 min travel

PTC_SCHEDULE = [
    # (direction, departure_time, travel_mins)
    # PTC to IITH (direction 0)
    (0, "08:00", 35),
    (0, "10:00", 35),
    (0, "16:00", 35),
    (0, "18:00", 35),
    (0, "20:00", 35),
    (0, "22:00", 35),
    # IITH to PTC (direction 1)
    (1, "09:00", 35),
    (1, "11:00", 35),
    (1, "17:00", 35),
    (1, "19:00", 35),
    (1, "21:00", 35),
    (1, "23:00", 35),
]


def time_add_minutes(time_str: str, minutes: int) -> str:
    """Add minutes to a HH:MM or HH:MM:SS time string, returns HH:MM:SS."""
    parts = time_str.split(":")
    h, m = int(parts[0]), int(parts[1])
    total_mins = h * 60 + m + minutes
    new_h = total_mins // 60
    new_m = total_mins % 60
    return f"{new_h:02d}:{new_m:02d}:00"


def ensure_time_format(t: str) -> str:
    """Ensure time is in HH:MM:SS format."""
    if len(t) == 5:
        return t + ":00"
    return t


def main():
    db = SessionLocal()
    trip_counter = 0

    try:
        # ── 1. Create IITH Agency ──────────────────────────────────────
        existing_agency = db.query(Agency).filter(Agency.agency_id == "IITH").first()
        if not existing_agency:
            db.add(Agency(
                agency_id="IITH",
                agency_name="IIT Hyderabad Transport",
                agency_url="https://iith.ac.in",
                agency_timezone="Asia/Kolkata",
                agency_lang="en"
            ))
            print("✅ Created agency: IITH")
        else:
            print("ℹ️  Agency IITH already exists")

        # ── 2. Create Calendar (service all days) ──────────────────────
        existing_cal = db.query(Calendar).filter(Calendar.service_id == "IITH_DAILY").first()
        if not existing_cal:
            db.add(Calendar(
                service_id="IITH_DAILY",
                start_date="20240101",
                end_date="20271231",
                monday=1, tuesday=1, wednesday=1, thursday=1,
                friday=1, saturday=1, sunday=1
            ))
            print("✅ Created calendar: IITH_DAILY (all days)")

        existing_cal_wk = db.query(Calendar).filter(Calendar.service_id == "IITH_WEEKDAY").first()
        if not existing_cal_wk:
            db.add(Calendar(
                service_id="IITH_WEEKDAY",
                start_date="20240101",
                end_date="20271231",
                monday=1, tuesday=1, wednesday=1, thursday=1,
                friday=1, saturday=0, sunday=0
            ))
            print("✅ Created calendar: IITH_WEEKDAY (Mon-Fri)")

        db.flush()

        # ── 3. Create IITH Stops ───────────────────────────────────────
        for stop_id, info in IITH_STOPS.items():
            existing = db.query(Stop).filter(Stop.stop_id == stop_id).first()
            if not existing:
                db.add(Stop(
                    stop_id=stop_id,
                    stop_name=info["name"],
                    stop_lat=info["lat"],
                    stop_lon=info["lon"],
                    zone_id="IITH"
                ))
                print(f"  ✅ Created stop: {info['name']} ({info['lat']}, {info['lon']})")
            else:
                print(f"  ℹ️  Stop {info['name']} already exists")

        db.flush()

        # ── 4. Create Routes ──────────────────────────────────────────
        routes_to_create = [
            ("IITH_SHUTTLE", "IITH Shuttle", 3),     # route_type 3 = bus
            ("IITH_MIYAPUR", "IITH-Miyapur", 3),
            ("IITH_PTC",     "IITH-Patancheru", 3),
        ]
        for route_id, name, rtype in routes_to_create:
            existing = db.query(Route).filter(Route.route_id == route_id).first()
            if not existing:
                db.add(Route(
                    route_id=route_id,
                    route_short_name=name,
                    agency_id="IITH",
                    route_type=rtype
                ))
                print(f"  ✅ Created route: {name}")
            else:
                print(f"  ℹ️  Route {name} already exists")

        db.flush()

        # ── 5. Delete old IITH trips (for clean re-import) ────────────
        old_trips = db.query(Trip).filter(Trip.route_id.in_(["IITH_SHUTTLE", "IITH_MIYAPUR", "IITH_PTC"])).all()
        if old_trips:
            old_trip_ids = [t.trip_id for t in old_trips]
            db.query(StopTime).filter(StopTime.trip_id.in_(old_trip_ids)).delete(synchronize_session=False)
            db.query(Trip).filter(Trip.trip_id.in_(old_trip_ids)).delete(synchronize_session=False)
            print(f"  🗑️  Cleaned up {len(old_trips)} old IITH trips")

        db.flush()

        # ── 6. Import Campus Shuttle Trips ─────────────────────────────
        print("\n📋 Importing campus shuttle schedule...")
        shuttle_trips = 0
        for direction, dep_time in SHUTTLE_SCHEDULE:
            trip_counter += 1
            trip_id = f"IITH_SH_{trip_counter:04d}"
            dep_time_fmt = ensure_time_format(dep_time)

            db.add(Trip(
                trip_id=trip_id,
                route_id="IITH_SHUTTLE",
                service_id="IITH_DAILY",
                direction_id=direction
            ))

            if direction == 0:
                # Maingate → Hospital → Hostel Circle
                stops_seq = [
                    ("IITH_MAINGATE",      dep_time_fmt,                    dep_time_fmt),
                    ("IITH_HOSPITAL",      time_add_minutes(dep_time, 5),   time_add_minutes(dep_time, 5)),
                    ("IITH_HOSTEL_CIRCLE", time_add_minutes(dep_time, 10),  time_add_minutes(dep_time, 10)),
                ]
            else:
                # Hostel Circle → Hospital → Maingate
                stops_seq = [
                    ("IITH_HOSTEL_CIRCLE", dep_time_fmt,                    dep_time_fmt),
                    ("IITH_HOSPITAL",      time_add_minutes(dep_time, 5),   time_add_minutes(dep_time, 5)),
                    ("IITH_MAINGATE",      time_add_minutes(dep_time, 10),  time_add_minutes(dep_time, 10)),
                ]

            for seq, (stop_id, arr, dep) in enumerate(stops_seq, start=1):
                db.add(StopTime(
                    trip_id=trip_id,
                    stop_sequence=seq,
                    stop_id=stop_id,
                    arrival_time=arr,
                    departure_time=dep
                ))
            shuttle_trips += 1

        print(f"  ✅ Created {shuttle_trips} campus shuttle trips")

        # ── 7. Import Miyapur Bus Trips ────────────────────────────────
        print("\n📋 Importing Miyapur bus schedule...")
        miyapur_trips = 0
        for direction, dep_time, travel_mins in MIYAPUR_SCHEDULE:
            trip_counter += 1
            trip_id = f"IITH_MY_{trip_counter:04d}"
            dep_fmt = ensure_time_format(dep_time)
            arr_fmt = time_add_minutes(dep_time, travel_mins)

            db.add(Trip(
                trip_id=trip_id,
                route_id="IITH_MIYAPUR",
                service_id="IITH_WEEKDAY",
                direction_id=direction
            ))

            if direction == 0:
                # Miyapur → IITH
                stops = [
                    (MIYAPUR_STOP_ID,  dep_fmt, dep_fmt,  1),
                    ("IITH_MAINGATE",  arr_fmt, arr_fmt,  2),
                ]
            else:
                # IITH → Miyapur
                stops = [
                    ("IITH_MAINGATE",  dep_fmt, dep_fmt,  1),
                    (MIYAPUR_STOP_ID,  arr_fmt, arr_fmt,  2),
                ]

            for stop_id, arr, dep, seq in stops:
                db.add(StopTime(
                    trip_id=trip_id,
                    stop_sequence=seq,
                    stop_id=stop_id,
                    arrival_time=arr,
                    departure_time=dep
                ))
            miyapur_trips += 1

        print(f"  ✅ Created {miyapur_trips} Miyapur bus trips")

        # ── 8. Import Patancheru Bus Trips ─────────────────────────────
        print("\n📋 Importing Patancheru bus schedule...")
        ptc_trips = 0
        for direction, dep_time, travel_mins in PTC_SCHEDULE:
            trip_counter += 1
            trip_id = f"IITH_PT_{trip_counter:04d}"
            dep_fmt = ensure_time_format(dep_time)
            arr_fmt = time_add_minutes(dep_time, travel_mins)

            db.add(Trip(
                trip_id=trip_id,
                route_id="IITH_PTC",
                service_id="IITH_DAILY",
                direction_id=direction
            ))

            if direction == 0:
                # Patancheru → IITH
                stops = [
                    (PATANCHERU_STOP_ID, dep_fmt, dep_fmt, 1),
                    ("IITH_MAINGATE",    arr_fmt, arr_fmt, 2),
                ]
            else:
                # IITH → Patancheru
                stops = [
                    ("IITH_MAINGATE",    dep_fmt, dep_fmt, 1),
                    (PATANCHERU_STOP_ID, arr_fmt, arr_fmt, 2),
                ]

            for stop_id, arr, dep, seq in stops:
                db.add(StopTime(
                    trip_id=trip_id,
                    stop_sequence=seq,
                    stop_id=stop_id,
                    arrival_time=arr,
                    departure_time=dep
                ))
            ptc_trips += 1

        print(f"  ✅ Created {ptc_trips} Patancheru bus trips")

        # ── Commit everything ──────────────────────────────────────────
        db.commit()
        print(f"\n{'='*60}")
        print(f"✅ IITH bus import complete!")
        print(f"   Shuttle trips: {shuttle_trips}")
        print(f"   Miyapur trips: {miyapur_trips}")
        print(f"   PTC trips:     {ptc_trips}")
        print(f"   Total:         {shuttle_trips + miyapur_trips + ptc_trips} trips")
        print(f"{'='*60}")

    except Exception as e:
        db.rollback()
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    main()
