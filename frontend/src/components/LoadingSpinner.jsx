import React from 'react';

const LoadingSpinner = ({ message = "Finding the best routes..." }) => {
  return (
    <div className="fixed inset-0 bg-[#0f172a]/80 z-50 flex flex-col items-center justify-center backdrop-blur-sm">
      <div className="text-6xl animate-bus-move mb-6">🚌</div>
      <div className="text-[#0ea5e9] text-xl font-medium animate-pulse-glow">
        {message}
      </div>
    </div>
  );
};

export default LoadingSpinner;
