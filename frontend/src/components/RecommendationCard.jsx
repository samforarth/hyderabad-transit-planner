import React from 'react';
import { formatDuration, formatDistance, getBusColor } from '../utils/formatters.js';

const RecommendationCard = ({ journey, isRecommended, onClick, index }) => {
  if (!journey) return null;

  const { 
    legs = [], 
    total_duration_mins = 0, 
    transfers = 0, 
    reason, 
    walking_to_source_meters = 0, 
    walking_from_dest_meters = 0 
  } = journey;
  
  const totalWalkMeters = walking_to_source_meters + walking_from_dest_meters;

  return (
    <div 
      onClick={onClick}
      className={`glass-card p-5 rounded-xl cursor-pointer transition-all duration-300 hover:scale-[1.02] hover:shadow-xl animate-fade-in-up stagger-${index} 
        ${isRecommended ? 'recommended-glow border-2 border-[#f59e0b]' : 'border border-[#334155]'}`}
    >
      {isRecommended && (
        <div className="flex items-center gap-1.5 mb-3 text-[#f59e0b] font-medium text-sm">
          <span>⭐</span> Recommended
        </div>
      )}
      
      {/* Top section: Bus Numbers */}
      <div className="flex flex-wrap items-center gap-2 mb-5">
        {legs.map((leg, i) => (
          <React.Fragment key={i}>
            <div 
              className="px-3 py-1.5 rounded-full text-white text-sm font-semibold shadow-sm flex items-center gap-1"
              style={{ backgroundColor: getBusColor(leg.bus_number) || '#0ea5e9' }}
            >
              <span>🚌</span> {leg.bus_number}
            </div>
            {i < legs.length - 1 && <span className="text-[#64748b] font-bold">→</span>}
          </React.Fragment>
        ))}
      </div>

      {/* Middle section: Metrics */}
      <div className="flex items-center gap-6 mb-4 text-[#e2e8f0] bg-[#0f172a]/50 p-3 rounded-lg border border-[#334155]/50">
        <div className="flex items-center gap-2" title="Total Duration">
          <span className="text-lg">⏱</span>
          <span className="font-medium text-sm">{formatDuration(total_duration_mins)}</span>
        </div>
        <div className="flex items-center gap-2" title="Total Walking Distance">
          <span className="text-lg">🚶</span>
          <span className="font-medium text-sm">{formatDistance(totalWalkMeters)}</span>
        </div>
        <div className="flex items-center gap-2" title="Number of Transfers">
          <span className="text-lg">🔄</span>
          <span className="font-medium text-sm">{transfers} {transfers === 1 ? 'transfer' : 'transfers'}</span>
        </div>
      </div>

      {/* Bottom section: Reason */}
      {reason && (
        <div className="text-[#94a3b8] text-sm italic mt-2 border-t border-[#334155] pt-3">
          "{reason}"
        </div>
      )}
    </div>
  );
};

export default RecommendationCard;
