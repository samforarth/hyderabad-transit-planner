/**
 * Road-snapped routing via OSRM (Open Source Routing Machine)
 * =============================================================
 * OSRM is an open-source routing engine that returns actual road geometry.
 * We use it to convert our stop-to-stop straight lines into road-following curves.
 *
 * The public OSRM demo server is used here (fine for a student project).
 * For production, you would host your own OSRM instance.
 *
 * API format:
 *   GET /route/v1/driving/lon1,lat1;lon2,lat2;...?overview=full&geometries=geojson
 *   Note: OSRM uses lon,lat order (opposite of Leaflet's lat,lon)
 */

const OSRM_BASE = "https://router.project-osrm.org/route/v1/driving";

/**
 * Fetches road-snapped route geometry for a series of waypoints.
 *
 * @param {Array<[number, number]>} points - Array of [lat, lon] pairs (Leaflet order)
 * @returns {Promise<Array<[number, number]>>} Dense array of [lat, lon] pairs following roads
 *
 * Falls back to the original straight-line points if OSRM fails or returns no result.
 */
export async function getRouteGeometry(points) {
  // Need at least 2 points to create a route
  if (!points || points.length < 2) {
    return points || [];
  }

  // Convert from Leaflet [lat, lon] to OSRM "lon,lat" format and join with semicolons
  const coordString = points
    .map(([lat, lon]) => `${lon},${lat}`)
    .join(";");

  try {
    const response = await fetch(
      `${OSRM_BASE}/${coordString}?overview=full&geometries=geojson`,
      { signal: AbortSignal.timeout(5000) } // 5 second timeout
    );

    if (!response.ok) {
      return points; // Fallback to straight lines
    }

    const data = await response.json();

    if (data.code !== "Ok" || !data.routes || data.routes.length === 0) {
      return points; // Fallback to straight lines
    }

    // OSRM returns GeoJSON coordinates as [lon, lat] — flip to [lat, lon] for Leaflet
    const roadCoords = data.routes[0].geometry.coordinates.map(
      ([lon, lat]) => [lat, lon]
    );

    return roadCoords;
  } catch (error) {
    // Network error, timeout, etc. — silently fall back to straight lines
    return points;
  }
}

/**
 * Fetches road geometry for multiple route segments in parallel.
 * Each segment is an object with a `points` array.
 *
 * @param {Array<{points: Array<[number, number]>, ...rest}>} segments
 * @returns {Promise<Array<{points: Array<[number, number]>, ...rest}>>} Segments with road-snapped points
 */
export async function snapSegmentsToRoads(segments) {
  if (!segments || segments.length === 0) return [];

  const snapped = await Promise.all(
    segments.map(async (segment) => {
      const roadPoints = await getRouteGeometry(segment.points);
      return { ...segment, points: roadPoints };
    })
  );

  return snapped;
}
