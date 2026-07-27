"""
SQLAlchemy ORM models for landmarks and caching.

We cache Nominatim geocoding results because external APIs often have strict 
rate limits and network calls can be slow. By caching searched landmarks locally,
we improve overall API response times and reduce the load on external services.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime
from app.database import Base


class Landmark(Base):
    __tablename__ = "landmarks"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(255), index=True, nullable=False)
    lat = Column(Float, nullable=False)
    lon = Column(Float, nullable=False)
    display_name = Column(String(500), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<Landmark(id={self.id}, name='{self.name}', display_name='{self.display_name}')>"
