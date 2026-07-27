"""
GTFS Data Import Script
========================
Reads the GTFS CSV files from data/gtfs/ and loads them into MySQL.

GTFS (General Transit Feed Specification) is the global standard for
public transit data. Google, Apple Maps, and transit agencies worldwide
use this format. Our database mirrors the GTFS schema exactly.

Usage:
    cd backend/
    python import_gtfs.py

What this script does:
    1. Creates all database tables (if they don't exist)
    2. Reads each CSV file from the data/gtfs/ directory
    3. Bulk-inserts records into MySQL
    4. Prints progress and final counts

Why bulk insert instead of one-by-one:
    stop_times.txt has 809,219 records. Inserting one at a time would take
    ~10 minutes. Bulk inserting in batches of 5000 takes ~30 seconds.
"""

import csv
import os
import sys
import time

# Add parent directory to path so we can import app modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.config import settings
from app.database import engine, SessionLocal, Base
from app.models.gtfs import Agency, Calendar, Route, Trip, Stop, StopTime
from app.models.landmarks import Landmark  # noqa: F401 — needed for table creation


# Path to GTFS data files (relative to project root)
GTFS_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "gtfs")


def read_csv_file(filename: str) -> list[dict]:
    """
    Reads a GTFS CSV file and returns a list of dictionaries.
    Each dictionary represents one row, with column names as keys.
    """
    filepath = os.path.join(GTFS_DIR, filename)

    if not os.path.exists(filepath):
        print(f"  ⚠ File not found: {filename}")
        return []

    with open(filepath, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        rows = [row for row in reader]

    return rows


def bulk_insert(session, model_class, rows: list[dict], batch_size: int = 5000):
    """
    Inserts rows in batches for performance.

    Why batching matters:
    - MySQL has a max packet size. Sending 800K rows at once would fail.
    - Batching gives us progress feedback and handles memory efficiently.
    - 5000 rows per batch is a good balance between speed and memory usage.
    """
    total = len(rows)
    inserted = 0

    for i in range(0, total, batch_size):
        batch = rows[i : i + batch_size]
        session.bulk_insert_mappings(model_class, batch)
        session.commit()
        inserted += len(batch)

        # Show progress for large tables
        if total > batch_size:
            percent = (inserted / total) * 100
            print(f"    Progress: {inserted:,}/{total:,} ({percent:.0f}%)", end="\r")

    if total > batch_size:
        print()  # New line after progress


def clean_row(row: dict, model_class) -> dict:
    """
    Cleans a CSV row to match the SQLAlchemy model's expected types.

    Why this is needed:
    - CSV files read everything as strings
    - Our models expect specific types (Float for lat/lon, Integer for sequence)
    - Empty strings need to become None for nullable fields
    """
    cleaned = {}

    for key, value in row.items():
        # Skip empty strings — they should be None in the database
        if value == "":
            cleaned[key] = None
            continue

        # Type conversions based on the model
        if model_class == Stop and key in ("stop_lat", "stop_lon"):
            cleaned[key] = float(value)
        elif model_class == StopTime and key == "stop_sequence":
            cleaned[key] = int(value)
        elif model_class == StopTime and key == "timepoint":
            cleaned[key] = int(value)
        elif model_class == Calendar and key in (
            "monday", "tuesday", "wednesday", "thursday",
            "friday", "saturday", "sunday",
        ):
            cleaned[key] = int(value)
        elif model_class == Route and key == "route_type":
            cleaned[key] = int(value)
        elif model_class == Trip and key == "direction_id":
            cleaned[key] = int(value)
        else:
            cleaned[key] = value

    return cleaned


def import_table(session, model_class, filename: str, table_name: str):
    """Imports a single GTFS file into its corresponding database table."""
    print(f"\n📦 Importing {table_name}...")

    rows = read_csv_file(filename)
    if not rows:
        print(f"  ⚠ No data found in {filename}")
        return 0

    # Clean each row to match model types
    cleaned_rows = [clean_row(row, model_class) for row in rows]

    start_time = time.time()
    bulk_insert(session, model_class, cleaned_rows)
    elapsed = time.time() - start_time

    print(f"  ✓ Imported {len(cleaned_rows):,} {table_name} records ({elapsed:.1f}s)")
    return len(cleaned_rows)


def main():
    """
    Main import function. Runs the full GTFS data pipeline.

    Order matters because of foreign key relationships:
    1. agency (no dependencies)
    2. calendar (no dependencies)
    3. stops (no dependencies)
    4. routes (depends on agency)
    5. trips (depends on routes + calendar)
    6. stop_times (depends on trips + stops)
    """
    print("=" * 60)
    print("  Hyderabad Transit Planner — GTFS Data Import")
    print("=" * 60)
    print(f"\nDatabase: {settings.DB_NAME}@{settings.DB_HOST}")
    print(f"GTFS Directory: {os.path.abspath(GTFS_DIR)}")

    # Step 1: Create all tables
    print("\n🔧 Creating database tables...")
    Base.metadata.drop_all(bind=engine)  # Fresh start — drop existing tables
    Base.metadata.create_all(bind=engine)
    print("  ✓ Tables created")

    # Step 2: Import data in dependency order
    session = SessionLocal()
    total_records = 0

    try:
        import_order = [
            (Agency, "agency.txt", "agencies"),
            (Calendar, "calendar.txt", "calendar entries"),
            (Stop, "stops.txt", "stops"),
            (Route, "routes.txt", "routes"),
            (Trip, "trips.txt", "trips"),
            (StopTime, "stop_times.txt", "stop_times"),
        ]

        for model_class, filename, table_name in import_order:
            count = import_table(session, model_class, filename, table_name)
            total_records += count

    except Exception as e:
        session.rollback()
        print(f"\n❌ Import failed: {e}")
        raise
    finally:
        session.close()

    # Step 3: Summary
    print("\n" + "=" * 60)
    print(f"  ✅ Import complete! Total records: {total_records:,}")
    print("=" * 60)

    # Step 4: Quick verification
    print("\n🔍 Verification:")
    session = SessionLocal()
    try:
        agency_count = session.query(Agency).count()
        route_count = session.query(Route).count()
        stop_count = session.query(Stop).count()
        trip_count = session.query(Trip).count()
        stop_time_count = session.query(StopTime).count()

        print(f"  Agencies:   {agency_count:,}")
        print(f"  Routes:     {route_count:,}")
        print(f"  Stops:      {stop_count:,}")
        print(f"  Trips:      {trip_count:,}")
        print(f"  Stop Times: {stop_time_count:,}")
    finally:
        session.close()


if __name__ == "__main__":
    main()
