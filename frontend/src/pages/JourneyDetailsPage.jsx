/**
 * JourneyDetailsPage — Full Route View with Map
 * ================================================
 * Shows the complete journey with:
 * - Map with bus routes drawn as colored polylines
 * - Walking segments as dashed gray lines
 * - Step-by-step timeline
 * - Journey metrics
 */

import React, { useState, useMemo, useEffect } from "react";
import { useLocation, useNavigate, Link } from "react-router-dom";
import MapView from "../components/MapView.jsx";
import JourneyTimeline from "../components/JourneyTimeline.jsx";
import { snapSegmentsToRoads } from "../utils/routing.js";
import {
  formatDuration,
  formatDistance,
  formatTime,
  getBusColor,
} from "../utils/formatters.js";

const JourneyDetailsPage = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const state = location.state;

  useEffect(() => {
    if (!state || !state.journey) {
      navigate("/");
    }
  }, [state, navigate]);

  if (!state || !state.journey) return null;

  const { journey, sourceInfo, destInfo } = state;
  const legs = journey.legs || [];
  const walkTo = journey.walking_to_source_meters || 0;
  const walkFrom = journey.walking_from_dest_meters || 0;

  // ── Map data ──────────────────────────────────────────────────────
  // Route segments are snapped to actual roads via OSRM
  const [routeSegments, setRouteSegments] = useState([]);

  useEffect(() => {
    if (!legs || legs.length === 0) {
      setRouteSegments([]);
      return;
    }

    const rawSegments = legs.map((leg) => {
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

    snapSegmentsToRoads(rawSegments).then((snapped) => {
      setRouteSegments(snapped);
    });
  }, [legs]);

  const walkingSegments = useMemo(() => {
    const segments = [];
    if (legs.length > 0) {
      // Walk from source to first boarding stop
      segments.push({
        from: { lat: sourceInfo.lat, lon: sourceInfo.lon },
        to: { lat: legs[0].board_lat, lon: legs[0].board_lon },
      });
      // Walk from last alighting stop to destination
      const lastLeg = legs[legs.length - 1];
      segments.push({
        from: { lat: lastLeg.alight_lat, lon: lastLeg.alight_lon },
        to: { lat: destInfo.lat, lon: destInfo.lon },
      });
    }
    return segments;
  }, [legs, sourceInfo, destInfo]);

  const stopMarkers = useMemo(() => {
    const stops = [];
    legs.forEach((leg) => {
      if (leg.stop_coords && leg.stop_coords.length > 0) {
        leg.stop_coords.forEach((coord, i) => {
          const isFirst = i === 0;
          const isLast = i === leg.stop_coords.length - 1;
          stops.push({
            lat: coord.lat,
            lon: coord.lon,
            name: isFirst
              ? `🚌 Board Bus ${leg.bus_number}: ${coord.name}`
              : isLast
                ? `📍 Alight: ${coord.name}`
                : `🚏 ${coord.name}`,
            isIntermediate: !isFirst && !isLast,
          });
        });
      } else {
        stops.push({
          lat: leg.board_lat,
          lon: leg.board_lon,
          name: `Board Bus ${leg.bus_number}: ${leg.board_stop_name}`,
        });
        stops.push({
          lat: leg.alight_lat,
          lon: leg.alight_lon,
          name: `Alight: ${leg.alight_stop_name}`,
        });
      }
    });
    return stops;
  }, [legs]);

  // Total intermediate stops
  const totalStops = legs.reduce(
    (sum, leg) => sum + (leg.num_intermediate_stops || 0),
    0
  );

  // Bus numbers for the header
  const busNumbers = legs.map((l) => l.bus_number);

  return (
    <div className="flex flex-col min-h-[calc(100vh-60px)] bg-[#0f172a] text-[#f1f5f9]">
      {/* Header */}
      <div className="flex items-center px-4 py-3 bg-[#1e293b] border-b border-[#334155] shrink-0">
        <button
          onClick={() => navigate(-1)}
          className="mr-3 p-2 rounded-full hover:bg-[#334155] transition-colors text-[#94a3b8] hover:text-white"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
          </svg>
        </button>
        <div className="flex-1">
          <div className="flex items-center gap-2 flex-wrap">
            {busNumbers.map((num, i) => (
              <span key={i} className="flex items-center gap-1">
                <span
                  className="px-2 py-0.5 rounded text-white text-xs font-bold"
                  style={{ backgroundColor: getBusColor(num) }}
                >
                  {num}
                </span>
                {i < busNumbers.length - 1 && (
                  <span className="text-[#64748b]">→</span>
                )}
              </span>
            ))}
            <span className="text-sm text-[#94a3b8] ml-2">
              {formatDuration(journey.total_duration_mins)}
            </span>
          </div>
          <p className="text-xs text-[#94a3b8] mt-0.5">
            {sourceInfo.name} → {destInfo.name}
          </p>
        </div>
      </div>

      {/* Map — top half */}
      <div className="h-[45vh] md:h-[50vh] shrink-0">
        <MapView
          center={[sourceInfo.lat, sourceInfo.lon]}
          zoom={13}
          sourceMarker={{ lat: sourceInfo.lat, lon: sourceInfo.lon, name: sourceInfo.name }}
          destMarker={{ lat: destInfo.lat, lon: destInfo.lon, name: destInfo.name }}
          routeSegments={routeSegments}
          walkingSegments={walkingSegments}
          stops={stopMarkers}
        />
      </div>

      {/* Details section */}
      <div className="flex-1 overflow-y-auto p-4 md:p-6">
        {/* Metrics grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
          <MetricCard icon="⏱" label="Duration" value={formatDuration(journey.total_duration_mins)} />
          <MetricCard icon="🚶" label="Walking" value={formatDistance(walkTo + walkFrom)} />
          <MetricCard icon="🔄" label="Transfers" value={`${journey.transfers}`} />
          <MetricCard icon="🚏" label="Stops" value={`${totalStops}`} />
        </div>

        {/* Step-by-step journey */}
        <div className="glass-card p-5 rounded-xl">
          <h3 className="text-sm font-semibold text-[#94a3b8] uppercase tracking-wider mb-4">
            Step-by-step directions
          </h3>

          <div className="space-y-0">
            {/* Walk to first stop */}
            {walkTo > 30 && (
              <StepItem
                icon="🚶"
                iconColor="#94a3b8"
                title={`Walk to ${legs[0]?.board_stop_name}`}
                subtitle={formatDistance(walkTo)}
                showLine={true}
              />
            )}

            {legs.map((leg, i) => (
              <div key={i}>
                {/* Board bus */}
                <StepItem
                  icon="🚌"
                  iconColor={getBusColor(leg.bus_number)}
                  title={
                    <>
                      Board <span className="font-bold" style={{ color: getBusColor(leg.bus_number) }}>Bus {leg.bus_number}</span> at {leg.board_stop_name}
                    </>
                  }
                  subtitle={`Departs ${formatTime(leg.departure_time)}`}
                  showLine={true}
                />

                {/* Ride */}
                <StepItem
                  icon="→"
                  iconColor={getBusColor(leg.bus_number)}
                  title={`Ride ${leg.num_intermediate_stops} stop${leg.num_intermediate_stops !== 1 ? "s" : ""}`}
                  subtitle={`${formatTime(leg.departure_time)} → ${formatTime(leg.arrival_time)}`}
                  showLine={true}
                  isRide={true}
                />

                {/* Alight */}
                <StepItem
                  icon="📍"
                  iconColor={getBusColor(leg.bus_number)}
                  title={`Get off at ${leg.alight_stop_name}`}
                  subtitle={`Arrives ${formatTime(leg.arrival_time)}`}
                  showLine={i < legs.length - 1 || walkFrom > 30}
                />

                {/* Transfer */}
                {i < legs.length - 1 && (
                  <StepItem
                    icon="🔄"
                    iconColor="#f59e0b"
                    title={`Transfer at ${leg.alight_stop_name}`}
                    subtitle="Wait for next bus"
                    showLine={true}
                  />
                )}
              </div>
            ))}

            {/* Walk to destination */}
            {walkFrom > 30 && (
              <StepItem
                icon="🚶"
                iconColor="#94a3b8"
                title={`Walk to ${destInfo.name}`}
                subtitle={formatDistance(walkFrom)}
                showLine={false}
              />
            )}

            {/* Arrive */}
            <StepItem
              icon="🏁"
              iconColor="#10b981"
              title={`Arrive at ${destInfo.name}`}
              subtitle={legs.length > 0 ? formatTime(legs[legs.length - 1].arrival_time) : ""}
              showLine={false}
            />
          </div>
        </div>
      </div>
    </div>
  );
};

/**
 * MetricCard — small stat box for the metrics grid.
 */
function MetricCard({ icon, label, value }) {
  return (
    <div className="glass-card p-3 rounded-xl text-center">
      <div className="text-xl mb-1">{icon}</div>
      <div className="text-lg font-bold text-[#f1f5f9]">{value}</div>
      <div className="text-xs text-[#64748b]">{label}</div>
    </div>
  );
}

/**
 * StepItem — one step in the vertical timeline.
 */
function StepItem({ icon, iconColor, title, subtitle, showLine, isRide }) {
  return (
    <div className="flex items-stretch gap-3">
      {/* Timeline column: dot + line */}
      <div className="flex flex-col items-center w-8 shrink-0">
        <div
          className={`w-8 h-8 rounded-full flex items-center justify-center text-sm shrink-0 ${
            isRide ? "bg-transparent border border-[#334155]" : ""
          }`}
          style={!isRide ? { backgroundColor: `${iconColor}20`, border: `2px solid ${iconColor}` } : {}}
        >
          {icon}
        </div>
        {showLine && (
          <div className="w-0.5 flex-1 min-h-[20px] bg-[#334155]"></div>
        )}
      </div>

      {/* Content */}
      <div className={`pb-4 flex-1 ${isRide ? "text-[#94a3b8] text-sm" : ""}`}>
        <div className={`${isRide ? "text-sm" : "text-sm font-medium text-[#f1f5f9]"}`}>
          {title}
        </div>
        {subtitle && (
          <div className="text-xs text-[#64748b] mt-0.5">{subtitle}</div>
        )}
      </div>
    </div>
  );
}

export default JourneyDetailsPage;
