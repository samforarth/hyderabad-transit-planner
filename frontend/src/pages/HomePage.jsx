/**
 * HomePage — Google Maps Style Layout
 * =====================================
 * Full-screen map with a compact search panel pinned to the top-left.
 * The map is always fully visible and interactive.
 *
 * Users can:
 * 1. Type locations in the top search bar (with autocomplete)
 * 2. Click directly on the map to pick source/destination
 */

import React, { useState, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { getRecommendations, reverseGeocode } from "../api/transit.js";
import SearchForm from "../components/SearchForm.jsx";
import MapView from "../components/MapView.jsx";
import LoadingSpinner from "../components/LoadingSpinner.jsx";

const HomePage = () => {
  const navigate = useNavigate();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  // Map-click location picking
  const [pickMode, setPickMode] = useState("source");
  const [sourcePin, setSourcePin] = useState(null);
  const [destPin, setDestPin] = useState(null);
  const [isResolving, setIsResolving] = useState(false);

  const handleMapClick = useCallback(async (lat, lng) => {
    setIsResolving(true);
    setError(null);
    try {
      const result = await reverseGeocode(lat, lng);
      const pin = { lat: result.lat, lon: result.lon, name: result.name };

      if (pickMode === "source") {
        setSourcePin(pin);
        setPickMode("destination");
      } else {
        setDestPin(pin);
        setPickMode("source");
      }
    } catch (err) {
      const pin = { lat, lon: lng, name: `(${lat.toFixed(4)}, ${lng.toFixed(4)})` };
      if (pickMode === "source") {
        setSourcePin(pin);
        setPickMode("destination");
      } else {
        setDestPin(pin);
        setPickMode("source");
      }
    } finally {
      setIsResolving(false);
    }
  }, [pickMode]);

  const handleSearch = async (source, destination, departureTime) => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await getRecommendations(source, destination, departureTime);
      navigate("/recommendations", {
        state: { data, source, destination, departureTime },
      });
    } catch (err) {
      setError(err.message || "Failed to find routes. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="relative w-full" style={{ height: "100vh" }}>
      {/* Full-screen map — always visible and interactive */}
      <div className="absolute inset-0 z-0">
        <MapView
          center={[17.385, 78.486]}
          zoom={12}
          onMapClick={handleMapClick}
          sourceMarker={sourcePin}
          destMarker={destPin}
        />
      </div>

      {/* Top-left search panel — well below the navbar */}
      <div className="absolute top-20 left-4 z-20 w-[380px] max-w-[calc(100vw-32px)]">
        {/* Search form card */}
        <div className="glass-card bg-[#1e293b]/90 backdrop-blur-xl rounded-2xl shadow-2xl border border-[#334155]/60 overflow-hidden animate-fade-in-up">

          {/* Search form or loading */}
          <div className="px-5 pt-4 pb-4">
            {isLoading ? (
              <div className="py-6 flex flex-col items-center">
                <div className="animate-bus-move text-3xl mb-3">🚌</div>
                <p className="text-[#94a3b8] text-sm">Finding best routes...</p>
              </div>
            ) : (
              <SearchForm
                onSearch={handleSearch}
                initialSource={sourcePin?.name || ""}
                initialDestination={destPin?.name || ""}
              />
            )}

            {error && (
              <div className="mt-3 p-2.5 rounded-lg bg-red-900/50 border border-red-500/50 text-red-200 text-xs">
                {error}
              </div>
            )}
          </div>
        </div>

        {/* Pick mode indicator */}
        <div className="mt-3 glass-card bg-[#1e293b]/80 backdrop-blur-md rounded-xl px-4 py-2.5 flex items-center gap-2 animate-fade-in">
          {isResolving ? (
            <span className="text-[#94a3b8] text-sm">📍 Resolving location...</span>
          ) : (
            <>
              <span className="text-[#94a3b8] text-xs">Click map to set:</span>
              <button
                onClick={() => setPickMode("source")}
                className={`px-3 py-1 rounded-full text-xs font-medium transition-all ${
                  pickMode === "source"
                    ? "bg-emerald-500/20 text-emerald-400 ring-1 ring-emerald-500/50"
                    : "bg-[#334155] text-[#94a3b8] hover:bg-[#475569]"
                }`}
              >
                🟢 Source
              </button>
              <button
                onClick={() => setPickMode("destination")}
                className={`px-3 py-1 rounded-full text-xs font-medium transition-all ${
                  pickMode === "destination"
                    ? "bg-red-500/20 text-red-400 ring-1 ring-red-500/50"
                    : "bg-[#334155] text-[#94a3b8] hover:bg-[#475569]"
                }`}
              >
                🔴 Destination
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default HomePage;
