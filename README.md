# 🚌 Hyderabad Transit Planner

An intelligent public transit recommendation platform for Hyderabad that analyzes GTFS transit data, resolves landmarks into nearby bus stops, generates direct and one-transfer journeys, ranks them using travel time, walking distance, and transfers, and visualizes optimized routes on an interactive map.

---

## 🎯 What It Does

Instead of showing raw bus numbers, this app answers a simple question:

> **"What's the best way to get from IIT Hyderabad to IKEA by bus?"**

The system:
1. Resolves landmark names to GPS coordinates (via OpenStreetMap Nominatim)
2. Finds the nearest bus stops to source and destination
3. Generates all possible journeys (direct + one-transfer)
4. Scores and ranks them using a weighted algorithm
5. Explains **why** each route is recommended
6. Visualizes everything on an interactive map

---

## Architecture

```
User Search → Landmark Resolver → Nearest Stop Finder → Journey Generator → Journey Scorer → Frontend
                    ↓                      ↓                    ↓                  ↓
              Nominatim API          Haversine Distance     GTFS Data         Weighted Score
              (cached in DB)         (top 5 stops)        (MySQL queries)     (lower = better)
```

### Tech Stack

| Layer | Technology | Why |
|-------|-----------|-----|
| **Frontend** | React + Tailwind CSS | Fast, modern, huge ecosystem |
| **Maps** | Leaflet (react-leaflet) | Open-source, no billing |
| **Backend** | Python + FastAPI | Clean APIs, auto-documentation |
| **Database** | MySQL + SQLAlchemy | Perfect for relational GTFS data |
| **Geocoding** | OpenStreetMap Nominatim | Free landmark → coordinate lookup |
| **Data** | GTFS (TGSRTC) | Standardized transit data format |

---

##  Project Structure

```
hyderabad-transit-planner/
├── data/gtfs/                  # Raw GTFS transit data (CSV files)
│   ├── agency.txt              # Transit agency info (TGSRTC)
│   ├── calendar.txt            # Service schedules
│   ├── routes.txt              # 1,502 bus routes
│   ├── stops.txt               # 4,710 bus stops with coordinates
│   ├── trips.txt               # 31,766 individual trips
│   └── stop_times.txt          # 809,219 stop arrival/departure times
│
├── backend/                    # Python FastAPI backend
│   ├── requirements.txt
│   ├── import_gtfs.py          # Script to load GTFS into MySQL
│   └── app/
│       ├── main.py             # FastAPI entry point
│       ├── config.py           # Environment-based configuration
│       ├── database.py         # SQLAlchemy engine + session
│       ├── models/             # ORM models (GTFS tables + landmarks)
│       ├── schemas/            # Pydantic request/response schemas
│       ├── services/           # Business logic (the recommendation engine)
│       │   ├── landmark_service.py     # Nominatim geocoding + cache
│       │   ├── stop_service.py         # Nearest stop finder
│       │   ├── route_service.py        # Journey generator (direct + transfer)
│       │   ├── recommendation_service.py  # Scoring + ranking
│       │   └── map_service.py          # Map data for Leaflet
│       ├── api/                # REST endpoints
│       └── utils/              # Haversine, time parsing
│
├── frontend/                   # React + Tailwind CSS frontend
│   ├── src/
│   │   ├── App.jsx             # Router setup
│   │   ├── api/transit.js      # API client module
│   │   ├── components/         # Reusable UI components
│   │   │   ├── SearchForm.jsx          # Autocomplete search
│   │   │   ├── RecommendationCard.jsx  # Journey card
│   │   │   ├── JourneyTimeline.jsx     # Step-by-step timeline
│   │   │   ├── MapView.jsx             # Leaflet map wrapper
│   │   │   └── ...
│   │   ├── pages/              # Full page views
│   │   │   ├── HomePage.jsx            # Map + search
│   │   │   ├── RecommendationsPage.jsx # Ranked results
│   │   │   └── JourneyDetailsPage.jsx  # Full journey view
│   │   └── utils/
│   │       ├── formatters.js    # Display formatting helpers
│   │       └── routing.js       # OSRM road-snapped route geometry
│   └── index.html
│
├── .gitignore
├── .env.example
└── README.md
```

---

##  Setup Instructions

### Prerequisites
- Python 3.13+
- Node.js 20+
- MySQL 8.0+

### 1. Clone the repository
```bash
git clone https://github.com/samforarth/hyderabad-transit-planner.git
cd hyderabad-transit-planner
```

### 2. Set up the database
```bash
# Start MySQL and create the database
mysql -u root -p -e "CREATE DATABASE hyderabad_transit CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
```

### 3. Set up the backend
```bash
cd backend

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp ../.env.example .env
# Edit .env with your MySQL credentials

# Import GTFS data into MySQL
python import_gtfs.py

# Import IIT Hyderabad campus bus schedules
python import_iith_buses.py

# Start the backend server
python -m uvicorn app.main:app --reload --port 8000
```

The API documentation is available at: http://localhost:8000/docs

### 4. Set up the frontend
```bash
cd frontend

# Install dependencies
npm install

# Start the development server
npm run dev
```

The app is available at: http://localhost:5173

---

##  API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/search?q=char` | Autocomplete search for stops and landmarks |
| `POST` | `/api/recommend` | Get ranked journey recommendations |
| `GET` | `/api/route/{id}` | Get all stops for a route |
| `GET` | `/api/nearby?lat=17.38&lon=78.47` | Find nearby bus stops |

### Example: Get Recommendations

```bash
curl -X POST http://localhost:8000/api/recommend \
  -H "Content-Type: application/json" \
  -d '{"source": "IIT Hyderabad", "destination": "IKEA", "departure_time": "21:30"}'
```

---

##  Recommendation Engine

The scoring algorithm ranks journeys using weighted criteria:

```
score = riding_time × 1.0 + transfer_wait × 1.5 + walking_distance × 0.005 + transfers × 15
```

| Factor | Weight | Rationale |
|--------|--------|-----------|
| Riding time | 1.0 | Actual time on the bus — most important |
| Transfer wait | 1.5 | Waiting at a stop feels 50% worse than riding |
| Walking distance | 0.005 | 200m walk = 1 point penalty |
| Transfers | 15 | Each transfer = 15 min equivalent penalty |

Transfer wait is capped at 45 minutes — if no connecting bus arrives within that window, the transfer is rejected.

The lowest score is **recommended**. Others are **alternatives** with explanations.

---

##  Data Summary

| Table | Records | Description |
|-------|---------|-------------|
| Agency | 2 | TGSRTC + IIT Hyderabad Transport |
| Routes | 1,505 | City buses (219, 100B, etc.) + IITH Shuttle, Miyapur, PTC buses |
| Stops | 4,713 | City bus stops + 3 IITH campus stops |
| Trips | 32,002 | City trips + 236 IITH campus trips |
| Stop Times | 809,927 | Arrival/departure times per stop |
| Calendar | 3 | All-day (TSRTC + IITH) + weekday-only (Miyapur bus) |

---

## 🗺 Key Algorithms

### Haversine Formula
Calculates great-circle distance between GPS coordinates. Used to find walking distances to bus stops.

### Modified BFS for Route Finding
- **Depth 1**: Direct journeys (find trips visiting both source and destination stops)
- **Depth 2**: One-transfer journeys (find intermediate stops connecting two trips)

### Landmark Resolution
Uses OpenStreetMap Nominatim API with Hyderabad bounding box. Results are cached in MySQL to respect rate limits.

---

##  Future Enhancements

- [x] IIT Hyderabad campus shuttle integration
- [x] OSRM road-following route visualization
- [ ] Live bus tracking
- [ ] Metro route integration
- [ ] Delay prediction using historical data
- [ ] User accounts and favorites
- [ ] Search history
- [ ] Push notifications for route updates

---

##  Built With

- **Frontend**: React, Tailwind CSS v4, Leaflet, React Router
- **Backend**: Python, FastAPI, SQLAlchemy, Pydantic
- **Database**: MySQL
- **APIs**: OpenStreetMap Nominatim, OSRM (route geometry)
- **Data**: GTFS (General Transit Feed Specification), IITH Transport Office schedules
