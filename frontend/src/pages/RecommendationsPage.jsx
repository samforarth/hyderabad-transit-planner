/**
 * RecommendationsPage — Route Results with Map
 * ===============================================
 * Split view: map showing the route on the left, journey cards on the right.
 * 
 * Key features:
 * - Draws bus route segments as colored polylines on the map
 * - Shows walking segments as dashed gray lines
 * - Marks all boarding/alighting stops on the map
 * - Hovering a card highlights that route on the map
 * - Each card shows exactly which stops to board/alight at
 */

import React, { useState, useEffect, useMemo } from "react";
import { useLocation, useNavigate, Link } from "react-router-dom";
import MapView from "../components/MapView.jsx";
import { snapSegmentsToRoads } from "../utils/routing.js";
import {
  formatDuration,
  formatDistance,
  formatTime,
  getBusColor,
} from "../utils/formatters.js";
import { getRecommendations } from "../api/transit.js";

const RecommendationsPage = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const state = location.state;

  const [selectedIndex, setSelectedIndex] = useState(0);
  const [routeSegments, setRouteSegments] = useState([]);

  useEffect(() => {
    if (!state || !state.data) {
      navigate("/");
    }
  }, [state, navigate]);

  if (!state || !state.data) return null;

  const { data, source, destination, departureTime } = state;
  const { recommended, alternatives, source_info, destination_info } = data;

  // All journeys in one array for easy indexing
  const allJourneys = useMemo(
    () => [recommended, ...(alternatives || [])].filter(Boolean),
    [recommended, alternatives]
  );
  const activeJourney = allJourneys[selectedIndex] || recommended;

  // ── Build map data from the active journey ──────────────────────────
  // Route segments are snapped to actual roads via OSRM.
  // First we build raw segments from stop_coords, then async-snap them to roads.
  useEffect(() => {
    if (!activeJourney?.legs) {
      setRouteSegments([]);
      return;
    }

    // Build raw segments from stop coordinates
    const rawSegments = activeJourney.legs.map((leg) => {
      const points = leg.stop_coords && leg.stop_coords.length > 0
        ? leg.stop_coords.map((coord) => [coord.lat, coord.lon])
        : [[leg.board_lat, leg.board_lon], [leg.alight_lat, leg.alight_lon]];
      return {
        points,
        color: getBusColor(leg.bus_number),
        busNumber: leg.bus_number,
      };
    });

    // Show raw segments immediately, then upgrade to road-snapped
    setRouteSegments(rawSegments);

    // Snap to actual roads via OSRM
    snapSegmentsToRoads(rawSegments).then((snapped) => {
      setRouteSegments(snapped);
    });
  }, [activeJourney]);

  // Walking segments: dashed lines for walking portions
  const walkingSegments = useMemo(() => {
    if (!activeJourney?.legs) return [];
    const segments = [];
    const firstLeg = activeJourney.legs[0];
    const lastLeg = activeJourney.legs[activeJourney.legs.length - 1];

    // Walk from source to first boarding stop
    if (firstLeg) {
      segments.push({
        from: { lat: source_info.lat, lon: source_info.lon },
        to: { lat: firstLeg.board_lat, lon: firstLeg.board_lon },
      });
    }
    // Walk from last alighting stop to destination
    if (lastLeg) {
      segments.push({
        from: { lat: lastLeg.alight_lat, lon: lastLeg.alight_lon },
        to: { lat: destination_info.lat, lon: destination_info.lon },
      });
    }
    return segments;
  }, [activeJourney, source_info, destination_info]);

  // Stop markers: show all stops along the bus route (board, intermediate, alight)
  const stopMarkers = useMemo(() => {
    if (!activeJourney?.legs) return [];
    const stops = [];
    activeJourney.legs.forEach((leg) => {
      if (leg.stop_coords && leg.stop_coords.length > 0) {
        // Show every stop along the route
        leg.stop_coords.forEach((coord, i) => {
          const isFirst = i === 0;
          const isLast = i === leg.stop_coords.length - 1;
          stops.push({
            lat: coord.lat,
            lon: coord.lon,
            name: isFirst
              ? `🚌 Board: ${coord.name} (Bus ${leg.bus_number})`
              : isLast
                ? `📍 Alight: ${coord.name}`
                : `🚏 ${coord.name}`,
            isIntermediate: !isFirst && !isLast,
          });
        });
      } else {
        // Fallback: only board and alight
        stops.push({
          lat: leg.board_lat,
          lon: leg.board_lon,
          name: `🚌 Board: ${leg.board_stop_name} (Bus ${leg.bus_number})`,
        });
        stops.push({
          lat: leg.alight_lat,
          lon: leg.alight_lon,
          name: `📍 Alight: ${leg.alight_stop_name}`,
        });
      }
    });
    return stops;
  }, [activeJourney]);

  const handleCardClick = (index) => {
    navigate(`/journey/${index}`, {
      state: {
        journey: allJourneys[index],
        sourceInfo: source_info,
        destInfo: destination_info,
        allJourneys,
      },
    });
  };

  // ── Editable search bar state ────────────────────────────────────────
  const [editSource, setEditSource] = useState(source);
  const [editDest, setEditDest] = useState(destination);
  const [editTime, setEditTime] = useState(departureTime || "");
  const [isReSearching, setIsReSearching] = useState(false);

  const handleReSearch = async () => {
    if (!editSource || !editDest) return;
    setIsReSearching(true);
    try {
      const newData = await getRecommendations(editSource, editDest, editTime);
      navigate("/recommendations", {
        state: { data: newData, source: editSource, destination: editDest, departureTime: editTime },
        replace: true,
      });
      setSelectedIndex(0);
    } catch (err) {
      console.error("Re-search failed:", err);
    } finally {
      setIsReSearching(false);
    }
  };

  return (
    <div className="flex flex-col h-[calc(100vh-60px)] w-full bg-[#0f172a] text-[#f1f5f9]">
      {/* Editable search bar — tweak source, destination, or time and re-search */}
      <div className="flex items-center gap-2 px-4 py-2.5 bg-[#1e293b] border-b border-[#334155] z-10 shadow-sm shrink-0">
        <Link
          to="/"
          className="p-2 rounded-full hover:bg-[#334155] transition-colors text-[#94a3b8] hover:text-white shrink-0"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
          </svg>
        </Link>

        {/* Source */}
        <input
          type="text"
          value={editSource}
          onChange={(e) => setEditSource(e.target.value)}
          className="flex-1 min-w-0 bg-[#0f172a] text-[#f1f5f9] text-sm px-3 py-1.5 rounded-lg border border-[#334155] focus:border-[#0ea5e9] outline-none truncate"
        />

        <span className="text-[#64748b] text-sm shrink-0">→</span>

        {/* Destination */}
        <input
          type="text"
          value={editDest}
          onChange={(e) => setEditDest(e.target.value)}
          className="flex-1 min-w-0 bg-[#0f172a] text-[#f1f5f9] text-sm px-3 py-1.5 rounded-lg border border-[#334155] focus:border-[#0ea5e9] outline-none truncate"
        />

        {/* Time */}
        <input
          type="time"
          value={editTime}
          onChange={(e) => setEditTime(e.target.value)}
          className="bg-[#0f172a] text-[#f1f5f9] text-sm px-3 py-1.5 rounded-lg border border-[#334155] focus:border-[#0ea5e9] outline-none [color-scheme:dark] w-[100px] shrink-0"
        />

        {/* Re-search */}
        <button
          onClick={handleReSearch}
          disabled={isReSearching || !editSource || !editDest}
          className="bg-[#0ea5e9] hover:bg-[#0284c7] text-white text-sm font-semibold px-4 py-1.5 rounded-lg transition-colors shrink-0 disabled:opacity-50"
        >
          {isReSearching ? "..." : "Search"}
        </button>

        <div className="text-xs text-[#94a3b8] bg-[#334155] px-3 py-1 rounded-full shrink-0">
          {allJourneys.length} route{allJourneys.length !== 1 ? "s" : ""}
        </div>
      </div>

      {/* Main split: map + cards */}
      <div className="flex flex-col md:flex-row flex-1 overflow-hidden">
        {/* Map — shows the selected route */}
        <div className="w-full md:w-[60%] h-[40vh] md:h-full relative">
          <MapView
            center={[source_info.lat, source_info.lon]}
            zoom={13}
            sourceMarker={{ lat: source_info.lat, lon: source_info.lon, name: source_info.name }}
            destMarker={{ lat: destination_info.lat, lon: destination_info.lon, name: destination_info.name }}
            routeSegments={routeSegments}
            walkingSegments={walkingSegments}
            stops={stopMarkers}
          />

          {/* Map legend */}
          <div className="absolute bottom-4 left-4 z-10 glass-card bg-[#1e293b]/90 px-3 py-2 rounded-lg text-xs">
            <div className="flex items-center gap-3">
              <span className="flex items-center gap-1">
                <span className="w-4 h-0.5 bg-[#94a3b8] inline-block" style={{ borderTop: "2px dashed #94a3b8" }}></span>
                Walking
              </span>
              <span className="flex items-center gap-1">
                <span className="w-4 h-0.5 bg-[#0ea5e9] inline-block"></span>
                Bus route
              </span>
              <span className="flex items-center gap-1">
                <span className="w-2 h-2 rounded-full bg-emerald-500 inline-block"></span>
                Start
              </span>
              <span className="flex items-center gap-1">
                <span className="w-2 h-2 rounded-full bg-red-500 inline-block"></span>
                End
              </span>
            </div>
          </div>
        </div>

        {/* Journey cards — scrollable */}
        <div className="w-full md:w-[40%] h-[60vh] md:h-full overflow-y-auto bg-[#0f172a] p-4">
          {/* Recommended route */}
          <div className="mb-4 animate-fade-in-up">
            <h3 className="text-sm font-bold text-[#f59e0b] mb-3 flex items-center gap-1">
              ⭐ Best Route
            </h3>
            <JourneyCard
              journey={recommended}
              isRecommended={true}
              isActive={selectedIndex === 0}
              onHover={() => setSelectedIndex(0)}
              onClick={() => handleCardClick(0)}
              sourceInfo={source_info}
              destInfo={destination_info}
            />
          </div>

          {/* Alternatives */}
          {alternatives && alternatives.length > 0 && (
            <div className="animate-fade-in-up" style={{ animationDelay: "100ms" }}>
              <h3 className="text-sm font-semibold text-[#94a3b8] mb-3 border-t border-[#334155] pt-4">
                Other Options
              </h3>
              <div className="flex flex-col gap-3">
                {alternatives.map((alt, idx) => {
                  const globalIdx = idx + 1;
                  return (
                    <JourneyCard
                      key={globalIdx}
                      journey={alt}
                      isRecommended={false}
                      isActive={selectedIndex === globalIdx}
                      onHover={() => setSelectedIndex(globalIdx)}
                      onClick={() => handleCardClick(globalIdx)}
                      sourceInfo={source_info}
                      destInfo={destination_info}
                    />
                  );
                })}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

/**
 * JourneyCard — inline component showing route details clearly.
 * Shows exactly: "Take Bus 109A from Stop X → Stop Y, then walk"
 */
function JourneyCard({ journey, isRecommended, isActive, onHover, onClick, sourceInfo, destInfo }) {
  if (!journey) return null;
  const legs = journey.legs || [];
  const walkTo = journey.walking_to_source_meters || 0;
  const walkFrom = journey.walking_from_dest_meters || 0;

  return (
    <div
      onMouseEnter={onHover}
      onClick={onClick}
      className={`
        glass-card p-4 rounded-xl cursor-pointer transition-all duration-200
        hover:scale-[1.01] hover:shadow-lg
        ${isRecommended ? "recommended-glow" : "border border-[#334155]/50"}
        ${isActive ? "ring-1 ring-[#0ea5e9]/50 bg-[#1e293b]" : ""}
      `}
    >
      {/* Recommended badge */}
      {isRecommended && (
        <div className="flex items-center gap-1 mb-2">
          <span className="text-xs font-semibold text-[#f59e0b] bg-[#f59e0b]/10 px-2 py-0.5 rounded-full">
            ⭐ Recommended
          </span>
        </div>
      )}

      {/* Step-by-step route display */}
      <div className="space-y-2 mb-3">
        {/* Walk to first stop */}
        {walkTo > 50 && (
          <div className="flex items-center gap-2 text-xs text-[#94a3b8]">
            <span className="w-5 text-center">🚶</span>
            <span>Walk {formatDistance(walkTo)} to <span className="text-[#f1f5f9] font-medium">{legs[0]?.board_stop_name}</span></span>
          </div>
        )}

        {/* Bus legs */}
        {legs.map((leg, i) => (
          <div key={i}>
            <div className="flex items-start gap-2 text-sm">
              <span
                className="shrink-0 px-2 py-0.5 rounded-md text-white text-xs font-bold mt-0.5"
                style={{ backgroundColor: getBusColor(leg.bus_number) }}
              >
                {leg.bus_number}
              </span>
              <div className="flex-1 text-[#f1f5f9]">
                <div>
                  <span className="font-medium">{leg.board_stop_name}</span>
                  <span className="text-[#64748b] mx-1.5">→</span>
                  <span className="font-medium">{leg.alight_stop_name}</span>
                </div>
                <div className="text-xs text-[#94a3b8] mt-0.5">
                  {formatTime(leg.departure_time)} – {formatTime(leg.arrival_time)}
                  <span className="mx-1">·</span>
                  {leg.num_intermediate_stops} stop{leg.num_intermediate_stops !== 1 ? "s" : ""}
                </div>
              </div>
            </div>

            {/* Transfer indicator between legs */}
            {i < legs.length - 1 && (
              <div className="flex items-center gap-2 text-xs text-[#f59e0b] ml-7 my-1">
                <span>🔄</span>
                <span>Transfer at {leg.alight_stop_name}</span>
              </div>
            )}
          </div>
        ))}

        {/* Walk from last stop to destination */}
        {walkFrom > 50 && (
          <div className="flex items-center gap-2 text-xs text-[#94a3b8]">
            <span className="w-5 text-center">🚶</span>
            <span>Walk {formatDistance(walkFrom)} to destination</span>
          </div>
        )}
      </div>

      {/* Metrics row */}
      <div className="flex items-center gap-4 text-xs text-[#94a3b8] pt-2 border-t border-[#334155]/50">
        <span>⏱ {formatDuration(journey.total_duration_mins)}</span>
        <span>🚶 {formatDistance(walkTo + walkFrom)}</span>
        <span>🔄 {journey.transfers} transfer{journey.transfers !== 1 ? "s" : ""}</span>
      </div>

      {/* Reason */}
      {journey.reason && (
        <p className="text-xs text-[#64748b] italic mt-2">{journey.reason}</p>
      )}
    </div>
  );
}

export default RecommendationsPage;
