import React from 'react';
import { formatTime, formatDistance } from '../utils/formatters.js';

const JourneyTimeline = ({ journey, sourceInfo, destInfo }) => {
  if (!journey || !journey.legs) return null;

  return (
    <div className="relative ml-4 border-l-2 border-[#334155] py-2">
      
      {/* 1. Walk to first stop */}
      {journey.walking_to_source_meters > 0 && (
        <div className="mb-6 relative pl-6">
          <div className="absolute -left-[9px] top-1 w-4 h-4 rounded-full bg-[#1e293b] border-2 border-[#94a3b8] z-10"></div>
          <div className="text-[#e2e8f0] font-medium flex items-center gap-2">
            <span>🚶</span> Walk to first stop
          </div>
          <div className="text-[#94a3b8] text-sm mt-1">
            {formatDistance(journey.walking_to_source_meters)}
          </div>
        </div>
      )}

      {/* Bus legs */}
      {journey.legs.map((leg, index) => {
        const isLast = index === journey.legs.length - 1;
        
        // Calculate wait time for next bus if not last leg
        let waitMins = 0;
        if (!isLast && journey.legs[index + 1]?.departure_time && leg.arrival_time) {
          const arrival = new Date(leg.arrival_time);
          const nextDeparture = new Date(journey.legs[index + 1].departure_time);
          waitMins = Math.max(0, Math.round((nextDeparture - arrival) / 60000));
        }
        
        return (
          <div key={index} className="mb-6 relative pl-6">
            <div className="absolute -left-[9px] top-1 w-4 h-4 rounded-full bg-[#0ea5e9] ring-4 ring-[#0f172a] z-10"></div>
            
            <div className="text-[#f1f5f9] font-medium flex items-center gap-2">
              <span>🚌</span> Board Bus {leg.bus_number}
            </div>
            <div className="text-[#94a3b8] text-sm mt-1">
              at <span className="text-[#e2e8f0] font-medium">{leg.board_stop_name}</span> ({formatTime(leg.departure_time)})
            </div>
            
            <div className="text-[#64748b] text-sm mt-3 mb-3 flex items-center gap-3 bg-[#1e293b]/50 p-2 rounded border border-[#334155]/50 w-max">
              <span className="w-1.5 h-1.5 rounded-full bg-[#64748b]"></span>
              Ride {leg.num_intermediate_stops} stops
            </div>

            <div className="text-[#94a3b8] text-sm mt-1">
              Alight at <span className="text-[#e2e8f0] font-medium">{leg.alight_stop_name}</span> ({formatTime(leg.arrival_time)})
            </div>

            {/* Transfer wait */}
            {!isLast && (
              <div className="mt-4 text-[#f59e0b] text-sm flex items-center gap-2 bg-[#f59e0b]/10 px-3 py-2 rounded-lg border border-[#f59e0b]/30 w-max">
                <span>🔄</span> Transfer — wait ~{waitMins} mins
              </div>
            )}
          </div>
        );
      })}

      {/* Walk to destination */}
      {journey.walking_from_dest_meters > 0 && (
        <div className="mb-6 relative pl-6">
          <div className="absolute -left-[9px] top-1 w-4 h-4 rounded-full bg-[#1e293b] border-2 border-[#94a3b8] z-10"></div>
          <div className="text-[#e2e8f0] font-medium flex items-center gap-2">
            <span>🚶</span> Walk to destination
          </div>
          <div className="text-[#94a3b8] text-sm mt-1">
            {formatDistance(journey.walking_from_dest_meters)}
          </div>
        </div>
      )}

      {/* Arrive */}
      <div className="relative pl-6">
        <div className="absolute -left-[9px] top-1 w-4 h-4 rounded-full bg-[#14b8a6] ring-4 ring-[#0f172a] z-10 shadow-[0_0_10px_#14b8a6]"></div>
        <div className="text-[#f1f5f9] font-medium flex items-center gap-2">
          <span>📍</span> Arrive at destination
        </div>
        <div className="text-[#94a3b8] text-sm mt-1">
          {destInfo?.name || 'Your destination'}
        </div>
      </div>

    </div>
  );
};

export default JourneyTimeline;
