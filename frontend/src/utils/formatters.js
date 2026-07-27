/**
 * Formatting Utility Functions
 * =============================
 * Helper functions to format data for display in the UI.
 * Keeps formatting logic out of components for cleaner code.
 */

/**
 * Formats minutes into a human-readable duration string.
 * @param {number} minutes - Duration in minutes
 * @returns {string} Formatted string like "1h 15m" or "45 mins"
 */
export function formatDuration(minutes) {
  if (minutes < 0) return "N/A";
  if (minutes < 60) return `${Math.round(minutes)} mins`;

  const hours = Math.floor(minutes / 60);
  const mins = Math.round(minutes % 60);

  if (mins === 0) return `${hours}h`;
  return `${hours}h ${mins}m`;
}

/**
 * Formats distance in meters to a readable string.
 * @param {number} meters - Distance in meters
 * @returns {string} Formatted string like "1.2 km" or "350 m"
 */
export function formatDistance(meters) {
  if (meters < 0) return "N/A";
  if (meters < 1000) return `${Math.round(meters)} m`;
  return `${(meters / 1000).toFixed(1)} km`;
}

/**
 * Formats a GTFS time string for display.
 * GTFS times can exceed 24:00:00 (for overnight trips).
 * We convert them to normal 12-hour format.
 *
 * @param {string} timeStr - GTFS time like "21:30:00" or "25:15:00"
 * @returns {string} Formatted time like "9:30 PM" or "1:15 AM"
 */
export function formatTime(timeStr) {
  if (!timeStr) return "";

  const parts = timeStr.split(":");
  let hours = parseInt(parts[0], 10);
  const minutes = parts[1];

  // Handle overnight times (25:00 = 1:00 AM next day)
  hours = hours % 24;

  const period = hours >= 12 ? "PM" : "AM";
  const displayHour = hours % 12 || 12;

  return `${displayHour}:${minutes} ${period}`;
}

/**
 * Generates a consistent color for a bus route number.
 * Uses a hash function so the same bus number always gets the same color.
 *
 * @param {string} busNumber - Route number like "219"
 * @returns {string} CSS color string in HSL format
 */
export function getBusColor(busNumber) {
  // Simple hash: sum of char codes
  let hash = 0;
  for (let i = 0; i < busNumber.length; i++) {
    hash = busNumber.charCodeAt(i) + ((hash << 5) - hash);
  }

  // Map hash to a hue (0-360), keep saturation and lightness fixed
  const hue = Math.abs(hash) % 360;
  return `hsl(${hue}, 70%, 55%)`;
}

/**
 * Truncates text to a maximum length with ellipsis.
 * @param {string} text - The text to truncate
 * @param {number} maxLength - Maximum character count
 * @returns {string} Truncated text
 */
export function truncateText(text, maxLength = 30) {
  if (!text || text.length <= maxLength) return text;
  return text.substring(0, maxLength) + "...";
}
