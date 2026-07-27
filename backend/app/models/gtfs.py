"""
SQLAlchemy ORM models mapped to the GTFS (General Transit Feed Specification) tables.

We mirror the GTFS standard exactly because it's a well-designed, widely-adopted 
relational structure for public transit data. Adhering to this standard allows us 
 to easily ingest standard GTFS feeds from transit agencies without major transformations.
"""

from sqlalchemy import Column, String, Integer, Float, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class Agency(Base):
    __tablename__ = "agency"

    agency_id = Column(String(50), primary_key=True, index=True)
    agency_name = Column(String(100), nullable=False)
    agency_url = Column(String(255), nullable=False)
    agency_timezone = Column(String(50), nullable=False)
    agency_lang = Column(String(10))

    # Relationships
    routes = relationship("Route", back_populates="agency")

    def __repr__(self) -> str:
        return f"<Agency(agency_id='{self.agency_id}', agency_name='{self.agency_name}')>"


class Calendar(Base):
    __tablename__ = "calendar"

    service_id = Column(String(50), primary_key=True, index=True)
    start_date = Column(String(8), nullable=False)
    end_date = Column(String(8), nullable=False)
    monday = Column(Integer, nullable=False, default=1)
    tuesday = Column(Integer, nullable=False, default=1)
    wednesday = Column(Integer, nullable=False, default=1)
    thursday = Column(Integer, nullable=False, default=1)
    friday = Column(Integer, nullable=False, default=1)
    saturday = Column(Integer, nullable=False, default=1)
    sunday = Column(Integer, nullable=False, default=1)

    # Relationships
    trips = relationship("Trip", back_populates="calendar")

    def __repr__(self) -> str:
        return f"<Calendar(service_id='{self.service_id}')>"


class Route(Base):
    __tablename__ = "routes"

    route_id = Column(String(50), primary_key=True, index=True)
    route_short_name = Column(String(50), nullable=False)
    agency_id = Column(String(50), ForeignKey("agency.agency_id"), nullable=False)
    route_type = Column(Integer, nullable=False)

    # Relationships
    agency = relationship("Agency", back_populates="routes")
    trips = relationship("Trip", back_populates="route")

    def __repr__(self) -> str:
        return f"<Route(route_id='{self.route_id}', route_short_name='{self.route_short_name}')>"


class Trip(Base):
    __tablename__ = "trips"

    # NOTE: trip_id in the raw data is often numeric, but we use String type here 
    # to provide flexibility for future feeds that might use alphanumeric IDs.
    trip_id = Column(String(50), primary_key=True, index=True)
    route_id = Column(String(50), ForeignKey("routes.route_id"), nullable=False)
    service_id = Column(String(50), ForeignKey("calendar.service_id"), nullable=False)
    direction_id = Column(Integer)
    trip_short_name = Column(String(100))

    # Relationships
    route = relationship("Route", back_populates="trips")
    calendar = relationship("Calendar", back_populates="trips")
    stop_times = relationship("StopTime", back_populates="trip")

    def __repr__(self) -> str:
        return f"<Trip(trip_id='{self.trip_id}', route_id='{self.route_id}')>"


class Stop(Base):
    __tablename__ = "stops"

    stop_id = Column(String(50), primary_key=True, index=True)
    stop_name = Column(String(255), nullable=False)
    zone_id = Column(String(50))
    stop_lat = Column(Float, nullable=False)
    stop_lon = Column(Float, nullable=False)
    stop_desc = Column(String(255))

    # Relationships
    stop_times = relationship("StopTime", back_populates="stop")

    def __repr__(self) -> str:
        return f"<Stop(stop_id='{self.stop_id}', stop_name='{self.stop_name}')>"


class StopTime(Base):
    __tablename__ = "stop_times"

    trip_id = Column(String(50), ForeignKey("trips.trip_id"), primary_key=True)
    stop_sequence = Column(Integer, primary_key=True)
    stop_id = Column(String(50), ForeignKey("stops.stop_id"), nullable=False, index=True)
    departure_time = Column(String(20), nullable=False)
    arrival_time = Column(String(20), nullable=False)
    timepoint = Column(Integer)

    # Relationships
    trip = relationship("Trip", back_populates="stop_times")
    stop = relationship("Stop", back_populates="stop_times")

    def __repr__(self) -> str:
        return f"<StopTime(trip_id='{self.trip_id}', stop_sequence={self.stop_sequence}, stop_id='{self.stop_id}')>"
