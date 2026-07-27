"""
Pydantic v2 schemas for journey planning API requests and responses.

These schemas are used by FastAPI for data validation, serialization, 
and generating OpenAPI documentation.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, ConfigDict, Field


class SearchRequest(BaseModel):
    source: str = Field(..., description="The starting location name or coordinates")
    destination: str = Field(..., description="The destination location name or coordinates")
    departure_time: str = Field(default="now", description="Time of departure, 'now' or HH:MM:SS format")


class StopInfo(BaseModel):
    stop_id: str
    stop_name: str
    lat: float = Field(alias="stop_lat")
    lon: float = Field(alias="stop_lon")
    distance_meters: Optional[float] = None

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class LegInfo(BaseModel):
    bus_number: str
    board_stop: StopInfo
    alight_stop: StopInfo
    departure_time: str
    arrival_time: str
    num_stops: int
    route_id: str

    model_config = ConfigDict(from_attributes=True)


class JourneyInfo(BaseModel):
    legs: List[LegInfo]
    total_duration_mins: int
    total_walking_meters: int
    transfers: int
    walking_to_source_meters: int
    walking_from_dest_meters: int

    model_config = ConfigDict(from_attributes=True)


class RecommendationResponse(BaseModel):
    recommended: JourneyInfo
    recommended_reason: str = Field(..., description="Reason why this journey was recommended")
    alternatives: List[Dict[str, Any]] = Field(default_factory=list, description="Alternative journeys with their reasons")
    source_info: Dict[str, Any]
    destination_info: Dict[str, Any]


class SearchSuggestion(BaseModel):
    name: str
    type: str = Field(..., description="'stop' or 'landmark'")
    lat: float
    lon: float

    model_config = ConfigDict(from_attributes=True)


class NearbyStopResponse(BaseModel):
    stops: List[StopInfo]
