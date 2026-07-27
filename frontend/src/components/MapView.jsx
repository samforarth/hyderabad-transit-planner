import React, { useEffect } from 'react';
import { MapContainer, TileLayer, Polyline, useMap, useMapEvents, CircleMarker, Marker, Popup, Tooltip, ZoomControl } from 'react-leaflet';
import L from 'leaflet';

// Fix for default Leaflet marker icons in Vite, though we use CircleMarker mainly
import markerIcon from 'leaflet/dist/images/marker-icon.png';
import markerShadow from 'leaflet/dist/images/marker-shadow.png';

let DefaultIcon = L.icon({
  iconUrl: markerIcon,
  shadowUrl: markerShadow,
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41]
});
L.Marker.prototype.options.icon = DefaultIcon;

// Captures map click events and passes lat/lon to the parent component.
// This enables the "click on map to select location" feature.
const MapClickHandler = ({ onMapClick }) => {
  useMapEvents({
    click(e) {
      if (onMapClick) {
        onMapClick(e.latlng.lat, e.latlng.lng);
      }
    },
  });
  return null;
};

// Helper component to adjust bounds automatically when props change
const FitBoundsHelper = ({ routeSegments, stops, sourceMarker, destMarker }) => {
  const map = useMap();

  useEffect(() => {
    const bounds = L.latLngBounds();
    let hasPoints = false;

    if (routeSegments && routeSegments.length > 0) {
      routeSegments.forEach(segment => {
        if (segment.points && segment.points.length > 0) {
          segment.points.forEach(point => {
            bounds.extend(point);
            hasPoints = true;
          });
        }
      });
    }

    if (stops && stops.length > 0) {
      stops.forEach(stop => {
        bounds.extend([stop.lat, stop.lon]);
        hasPoints = true;
      });
    }

    if (sourceMarker) {
      bounds.extend([sourceMarker.lat, sourceMarker.lon]);
      hasPoints = true;
    }
    
    if (destMarker) {
      bounds.extend([destMarker.lat, destMarker.lon]);
      hasPoints = true;
    }

    if (hasPoints) {
      map.fitBounds(bounds, { padding: [50, 50], maxZoom: 15 });
    }
  }, [map, routeSegments, stops, sourceMarker, destMarker]);

  return null;
};

// Key landmarks shown on the homepage map so users can orient themselves
const LANDMARKS = [
  { name: 'IIT Hyderabad', lat: 17.5913, lon: 78.1195, emoji: '🎓' },
  { name: 'Charminar', lat: 17.3616, lon: 78.4747, emoji: '🕌' },
  { name: 'Secunderabad', lat: 17.4344, lon: 78.5013, emoji: '🚉' },
  { name: 'Miyapur', lat: 17.4967, lon: 78.3608, emoji: '🚇' },
  { name: 'IKEA', lat: 17.4258, lon: 78.3378, emoji: '🛒' },
  { name: 'Gachibowli', lat: 17.4401, lon: 78.3489, emoji: '💼' },
  { name: 'LB Nagar', lat: 17.3457, lon: 78.5522, emoji: '🏘️' },
  { name: 'Sangareddy', lat: 17.6166, lon: 78.0868, emoji: '🚏' },
];

const MapView = ({
  center = [17.385, 78.486], // Default Hyderabad center
  zoom = 12,
  stops = [],
  routeSegments = [],
  walkingSegments = [],
  sourceMarker,
  destMarker,
  onMapClick,
  showLandmarks = false,
  height = '100%'
}) => {
  
  return (
    <div style={{ height, width: '100%' }} className="rounded-xl overflow-hidden shadow-2xl border border-[#334155] z-0">
      <MapContainer 
        center={center} 
        zoom={zoom} 
        style={{ height: '100%', width: '100%', backgroundColor: '#0f172a' }}
        zoomControl={false}
      >
        {/* Zoom controls at bottom-right to avoid navbar overlap */}
        <ZoomControl position="bottomright" />
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OSM</a> &copy; <a href="https://carto.com/attributions">CARTO</a>'
          url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
        />
        
        {/* Map click handler — lets users click to pick source/destination */}
        {onMapClick && <MapClickHandler onMapClick={onMapClick} />}

        <FitBoundsHelper 
          routeSegments={routeSegments} 
          stops={stops} 
          sourceMarker={sourceMarker} 
          destMarker={destMarker} 
        />

        {/* Route Segments (Buses) */}
        {routeSegments.map((segment, idx) => (
          <Polyline 
            key={`route-${idx}`} 
            positions={segment.points} 
            color={segment.color || '#0ea5e9'} 
            weight={5}
            opacity={0.8}
            lineCap="round"
            lineJoin="round"
          />
        ))}

        {/* Walking Segments */}
        {walkingSegments.map((segment, idx) => (
          <Polyline 
            key={`walk-${idx}`} 
            positions={[
              [segment.from.lat, segment.from.lon],
              [segment.to.lat, segment.to.lon]
            ]} 
            color="#94a3b8" 
            weight={4}
            dashArray="8, 12"
            opacity={0.7}
          />
        ))}

        {/* Bus Stop Markers — intermediate stops are smaller, board/alight are larger */}
        {stops.map((stop, idx) => (
          <CircleMarker 
            key={`stop-${idx}`}
            center={[stop.lat, stop.lon]}
            radius={stop.isIntermediate ? 3 : 6}
            fillColor={stop.isIntermediate ? '#334155' : '#1e293b'}
            color={stop.isIntermediate ? '#64748b' : '#0ea5e9'}
            weight={stop.isIntermediate ? 1.5 : 2.5}
            fillOpacity={1}
          >
            <Popup className="dark-popup">
              <div className="font-medium text-slate-800 px-1 py-0.5">{stop.name}</div>
            </Popup>
          </CircleMarker>
        ))}

        {/* Source Marker */}
        {sourceMarker && (
          <CircleMarker 
            center={[sourceMarker.lat, sourceMarker.lon]}
            radius={9}
            fillColor="#10b981" // Green
            color="#ffffff"
            weight={3}
            fillOpacity={1}
          >
            <Popup className="dark-popup">
              <div className="font-medium text-slate-800 px-1 py-0.5">
                <div className="text-xs text-gray-500 mb-1">Source</div>
                {sourceMarker.name || 'Source'}
              </div>
            </Popup>
          </CircleMarker>
        )}

        {/* Destination Marker */}
        {destMarker && (
          <CircleMarker 
            center={[destMarker.lat, destMarker.lon]}
            radius={9}
            fillColor="#ef4444" // Red
            color="#ffffff"
            weight={3}
            fillOpacity={1}
          >
            <Popup className="dark-popup">
              <div className="font-medium text-slate-800 px-1 py-0.5">
                <div className="text-xs text-gray-500 mb-1">Destination</div>
                {destMarker.name || 'Destination'}
              </div>
            </Popup>
          </CircleMarker>
        )}

        {/* Landmark labels on the homepage map */}
        {showLandmarks && LANDMARKS.map((lm) => (
          <CircleMarker
            key={lm.name}
            center={[lm.lat, lm.lon]}
            radius={5}
            fillColor="#0ea5e9"
            color="#1e293b"
            weight={2}
            fillOpacity={0.9}
          >
            <Tooltip
              direction="top"
              offset={[0, -8]}
              permanent
              className="landmark-tooltip"
            >
              {lm.emoji} {lm.name}
            </Tooltip>
          </CircleMarker>
        ))}
      </MapContainer>
    </div>
  );
};

export default MapView;
