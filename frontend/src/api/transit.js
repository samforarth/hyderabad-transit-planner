/**
 * API Client — Transit Service
 * ==============================
 * Centralizes all API calls to the backend in one module.
 *
 * Why we centralize:
 * - If the backend URL changes, we update ONE file
 * - Error handling is consistent across all endpoints
 * - Easy to add authentication headers later
 * - Follows the Single Responsibility Principle
 */

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000/api";

/**
 * Generic fetch wrapper with error handling.
 * All API calls go through this function.
 */
async function apiRequest(url, options = {}) {
  try {
    const response = await fetch(url, {
      headers: {
        "Content-Type": "application/json",
        ...options.headers,
      },
      ...options,
    });

    // If the server returned an error, extract the detail message
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(
        errorData.detail || `Server error: ${response.status}`
      );
    }

    return await response.json();
  } catch (error) {
    // Network errors (server not running, no internet, etc.)
    if (error.name === "TypeError" && error.message.includes("fetch")) {
      throw new Error("Cannot connect to server. Is the backend running?");
    }
    throw error;
  }
}

/**
 * Search for locations (bus stops + landmarks).
 * Used by the autocomplete dropdown in the search form.
 *
 * @param {string} query - The search text (e.g., "char" for "Charminar")
 * @param {number} limit - Max number of results (default: 8)
 * @returns {Promise<Array>} List of matching locations
 */
export async function searchLocations(query, limit = 8) {
  if (!query || query.length < 1) return [];

  const params = new URLSearchParams({ q: query, limit: String(limit) });
  return apiRequest(`${API_BASE}/search?${params}`);
}

/**
 * Get journey recommendations between two locations.
 * This is the MAIN feature of the app.
 *
 * @param {string} source - Source location name (e.g., "IIT Hyderabad")
 * @param {string} destination - Destination name (e.g., "IKEA")
 * @param {string} departureTime - Time in "HH:MM" format (e.g., "21:30")
 * @returns {Promise<Object>} { recommended, alternatives, source_info, destination_info }
 */
export async function getRecommendations(source, destination, departureTime) {
  return apiRequest(`${API_BASE}/recommend`, {
    method: "POST",
    body: JSON.stringify({
      source,
      destination,
      departure_time: departureTime,
    }),
  });
}

/**
 * Get detailed information about a specific bus route.
 *
 * @param {string} routeId - The route identifier (e.g., "219")
 * @param {number} direction - Direction: 0 (outbound) or 1 (inbound)
 * @returns {Promise<Object>} Route details with ordered stops
 */
export async function getRouteDetails(routeId, direction = 0) {
  const params = new URLSearchParams({ direction: String(direction) });
  return apiRequest(`${API_BASE}/route/${routeId}?${params}`);
}

/**
 * Find bus stops near a given coordinate.
 *
 * @param {number} lat - Latitude
 * @param {number} lon - Longitude
 * @param {number} radius - Search radius in meters (default: 1000)
 * @returns {Promise<Object>} { center, radius_meters, count, stops }
 */
export async function getNearbyStops(lat, lon, radius = 1000) {
  const params = new URLSearchParams({
    lat: String(lat),
    lon: String(lon),
    radius: String(radius),
  });
  return apiRequest(`${API_BASE}/nearby?${params}`);
}

/**
 * Reverse geocode coordinates to a place name.
 * Used when the user clicks on the map to pick a location.
 *
 * @param {number} lat - Latitude
 * @param {number} lon - Longitude
 * @returns {Promise<Object>} { name, lat, lon, display_name }
 */
export async function reverseGeocode(lat, lon) {
  const params = new URLSearchParams({
    lat: String(lat),
    lon: String(lon),
  });
  return apiRequest(`${API_BASE}/reverse-geocode?${params}`);
}
