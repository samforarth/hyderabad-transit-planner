import React, { useState, useEffect, useRef, useCallback } from 'react';
import { searchLocations } from '../api/transit.js';

const SearchForm = ({ onSearch, initialSource = "", initialDestination = "" }) => {
  const [source, setSource] = useState(initialSource);
  const [destination, setDestination] = useState(initialDestination);
  const [departureTime, setDepartureTime] = useState('');
  
  const [sourceResults, setSourceResults] = useState([]);
  const [destResults, setDestResults] = useState([]);
  
  const [showSourceDropdown, setShowSourceDropdown] = useState(false);
  const [showDestDropdown, setShowDestDropdown] = useState(false);
  
  const [isSearching, setIsSearching] = useState(false);

  // Sync map-pinned locations into the form fields when they change
  useEffect(() => {
    if (initialSource) setSource(initialSource);
  }, [initialSource]);

  useEffect(() => {
    if (initialDestination) setDestination(initialDestination);
  }, [initialDestination]);

  const sourceRef = useRef(null);
  const destRef = useRef(null);

  // Set default time to current time on mount
  useEffect(() => {
    const now = new Date();
    const hours = String(now.getHours()).padStart(2, '0');
    const minutes = String(now.getMinutes()).padStart(2, '0');
    setDepartureTime(`${hours}:${minutes}`);
  }, []);

  // Handle click outside to close dropdowns
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (sourceRef.current && !sourceRef.current.contains(event.target)) {
        setShowSourceDropdown(false);
      }
      if (destRef.current && !destRef.current.contains(event.target)) {
        setShowDestDropdown(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Debounced search implementations
  const sourceTimeoutRef = useRef(null);
  const handleSourceSearch = useCallback((query) => {
    if (sourceTimeoutRef.current) clearTimeout(sourceTimeoutRef.current);
    sourceTimeoutRef.current = setTimeout(async () => {
      if (query.trim().length > 1) {
        try {
          const results = await searchLocations(query);
          setSourceResults(results || []);
        } catch (e) {
          console.error('Source search failed', e);
          setSourceResults([]);
        }
      } else {
        setSourceResults([]);
      }
    }, 300);
  }, []);

  const destTimeoutRef = useRef(null);
  const handleDestSearch = useCallback((query) => {
    if (destTimeoutRef.current) clearTimeout(destTimeoutRef.current);
    destTimeoutRef.current = setTimeout(async () => {
      if (query.trim().length > 1) {
        try {
          const results = await searchLocations(query);
          setDestResults(results || []);
        } catch (e) {
          console.error('Dest search failed', e);
          setDestResults([]);
        }
      } else {
        setDestResults([]);
      }
    }, 300);
  }, []);

  const handleSourceChange = (e) => {
    const val = e.target.value;
    setSource(val);
    setShowSourceDropdown(true);
    handleSourceSearch(val);
  };

  const handleDestChange = (e) => {
    const val = e.target.value;
    setDestination(val);
    setShowDestDropdown(true);
    handleDestSearch(val);
  };

  const swapLocations = () => {
    setSource(destination);
    setDestination(source);
    setSourceResults([]);
    setDestResults([]);
    setShowSourceDropdown(false);
    setShowDestDropdown(false);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!source || !destination) return;
    setIsSearching(true);
    try {
      await onSearch(source, destination, departureTime);
    } finally {
      setIsSearching(false);
    }
  };

  return (
      <form onSubmit={handleSubmit} className="flex flex-col gap-3">
        
        {/* Source Input */}
        <div className="relative" ref={sourceRef}>
          <div className="flex items-center bg-[#1e293b] rounded-lg border border-[#334155] focus-within:border-[#0ea5e9] p-3 transition-colors">
            <span className="text-xl mr-3">📍</span>
            <input 
              type="text" 
              className="search-input bg-transparent w-full outline-none text-[#f1f5f9] placeholder-[#64748b]"
              placeholder="Source location"
              value={source}
              onChange={handleSourceChange}
              onFocus={() => { if(source.length > 1) setShowSourceDropdown(true); }}
            />
          </div>
          {showSourceDropdown && sourceResults.length > 0 && (
            <div className="absolute z-10 w-full mt-1 bg-[#1e293b] border border-[#334155] rounded-lg shadow-xl max-h-60 overflow-y-auto">
              {sourceResults.map((result, idx) => (
                <div 
                  key={idx} 
                  className="p-3 hover:bg-[#334155] cursor-pointer flex justify-between items-center text-[#f1f5f9] border-b border-[#334155] last:border-0"
                  onClick={() => {
                    setSource(result.name);
                    setShowSourceDropdown(false);
                  }}
                >
                  <span className="truncate pr-2">{result.name}</span>
                  {result.type && <span className="text-xs bg-[#0f172a] text-[#94a3b8] px-2 py-1 rounded-md shrink-0">{result.type}</span>}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Swap Button */}
        <div className="flex justify-center -my-3 relative z-0">
          <button 
            type="button" 
            onClick={swapLocations}
            className="bg-[#334155] hover:bg-[#475569] text-[#f1f5f9] rounded-full p-2 border-4 border-[#0f172a] transition-colors shadow-md"
            title="Swap locations"
          >
            ↕️
          </button>
        </div>

        {/* Destination Input */}
        <div className="relative" ref={destRef}>
          <div className="flex items-center bg-[#1e293b] rounded-lg border border-[#334155] focus-within:border-[#0ea5e9] p-3 transition-colors">
            <span className="text-xl mr-3">📍</span>
            <input 
              type="text" 
              className="search-input bg-transparent w-full outline-none text-[#f1f5f9] placeholder-[#64748b]"
              placeholder="Destination location"
              value={destination}
              onChange={handleDestChange}
              onFocus={() => { if(destination.length > 1) setShowDestDropdown(true); }}
            />
          </div>
          {showDestDropdown && destResults.length > 0 && (
            <div className="absolute z-10 w-full mt-1 bg-[#1e293b] border border-[#334155] rounded-lg shadow-xl max-h-60 overflow-y-auto">
              {destResults.map((result, idx) => (
                <div 
                  key={idx} 
                  className="p-3 hover:bg-[#334155] cursor-pointer flex justify-between items-center text-[#f1f5f9] border-b border-[#334155] last:border-0"
                  onClick={() => {
                    setDestination(result.name);
                    setShowDestDropdown(false);
                  }}
                >
                  <span className="truncate pr-2">{result.name}</span>
                  {result.type && <span className="text-xs bg-[#0f172a] text-[#94a3b8] px-2 py-1 rounded-md shrink-0">{result.type}</span>}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Time Input */}
        <div className="flex items-center bg-[#1e293b] rounded-lg border border-[#334155] focus-within:border-[#0ea5e9] p-3 transition-colors">
          <span className="text-xl mr-3">🕐</span>
          <input 
            type="time" 
            className="search-input bg-transparent w-full outline-none text-[#f1f5f9] placeholder-[#64748b] [color-scheme:dark]"
            value={departureTime}
            onChange={(e) => setDepartureTime(e.target.value)}
          />
        </div>

        {/* Submit Button */}
        <button 
          type="submit" 
          disabled={!source || !destination || isSearching}
          className={`btn-primary mt-2 w-full py-3.5 rounded-lg font-semibold text-white transition-all
            ${(!source || !destination || isSearching) 
              ? 'opacity-50 cursor-not-allowed bg-[#334155]' 
              : 'bg-[#0ea5e9] hover:bg-[#0284c7] hover:shadow-lg hover:shadow-[#0ea5e9]/20'}`}
        >
          {isSearching ? (
            <span className="flex items-center justify-center gap-2">
              <span className="animate-spin inline-block w-4 h-4 border-2 border-white/30 border-t-white rounded-full"></span>
              Searching...
            </span>
          ) : 'Find Routes'}
        </button>
      </form>
  );
};

export default SearchForm;
