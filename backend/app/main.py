"""
FastAPI Application Entry Point
================================
Sets up the FastAPI application with:
- CORS middleware (so the React frontend can call the API)
- All API route registrations
- Health check endpoint
- Startup verification

Run with:
    cd backend/
    python -m uvicorn app.main:app --reload --port 8000

Then visit:
    http://localhost:8000       → API info
    http://localhost:8000/docs  → Interactive API documentation (Swagger UI)
"""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import search, recommend, route_details, nearby, reverse_geocode

# ── Configure logging ──────────────────────────────────────────────────
# This gives us useful debug output in the terminal while developing.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s │ %(name)s │ %(levelname)s │ %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


# ── Create the FastAPI app ─────────────────────────────────────────────
app = FastAPI(
    title="Hyderabad Transit Planner API",
    description=(
        "An intelligent public transit recommendation platform for Hyderabad. "
        "Analyzes GTFS transit data to recommend the best bus journeys "
        "based on travel time, walking distance, and transfers."
    ),
    version="1.0.0",
)


# ── CORS Middleware ────────────────────────────────────────────────────
# Why we need CORS:
# The React frontend runs on localhost:5173 (Vite dev server).
# The FastAPI backend runs on localhost:8000.
# Browsers block requests between different "origins" (protocol + domain + port)
# unless the server explicitly allows it with CORS headers.
#
# In production, you'd restrict this to your actual frontend domain.
# During development, we allow localhost origins.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",      # Vite dev server
        "http://localhost:3000",      # Alternative React port
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],    # Allow all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],    # Allow all headers
)


# ── Register API Routers ──────────────────────────────────────────────
# Each router handles a specific group of endpoints.
# The prefix="/api" means all routes start with /api/...
# This is a common pattern to separate API routes from frontend routes.
app.include_router(search.router, prefix="/api", tags=["Search"])
app.include_router(recommend.router, prefix="/api", tags=["Recommendations"])
app.include_router(route_details.router, prefix="/api", tags=["Routes"])
app.include_router(nearby.router, prefix="/api", tags=["Nearby"])
app.include_router(reverse_geocode.router, prefix="/api", tags=["Geocoding"])


# ── Root Endpoint ──────────────────────────────────────────────────────
@app.get("/")
def root():
    """
    Root endpoint — returns basic API information.
    Useful for quick health checks and API discovery.
    """
    return {
        "name": "Hyderabad Transit Planner API",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "search": "GET /api/search?q=<query>",
            "recommend": "POST /api/recommend",
            "route_details": "GET /api/route/<route_id>",
            "nearby_stops": "GET /api/nearby?lat=<lat>&lon=<lon>",
            "reverse_geocode": "GET /api/reverse-geocode?lat=<lat>&lon=<lon>",
        },
    }


@app.get("/health")
def health_check():
    """
    Health check endpoint for monitoring.
    Returns 200 OK if the server is running.
    In production, this would also verify the database connection.
    """
    return {"status": "healthy"}
