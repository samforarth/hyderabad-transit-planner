import React from 'react';
import { Link } from 'react-router-dom';

const NotFoundPage = () => {
  return (
    <div className="min-h-[calc(100vh-60px)] w-full flex flex-col items-center justify-center bg-[#0f172a] p-4">
      <div className="text-center animate-fade-in-up space-y-6 max-w-md">
        
        <h1 className="text-8xl md:text-9xl font-extrabold text-[#1e293b] tracking-widest drop-shadow-sm relative">
          <span className="bg-clip-text text-transparent bg-gradient-to-r from-[#0ea5e9] to-[#14b8a6]">
            404
          </span>
        </h1>
        
        <div className="bg-[#1e293b]/50 backdrop-blur-sm border border-[#334155] p-8 rounded-2xl shadow-xl">
          <h2 className="text-2xl font-bold text-[#f1f5f9] mb-2">
            Page not found
          </h2>
          <p className="text-[#94a3b8] mb-8">
            The route you're looking for doesn't exist or might have been moved.
          </p>
          
          <Link 
            to="/" 
            className="inline-flex items-center justify-center w-full px-6 py-3 text-sm font-medium text-white transition-all rounded-lg bg-gradient-to-r from-[#0ea5e9] to-[#14b8a6] hover:from-[#0284c7] hover:to-[#0d9488] shadow-lg shadow-[#0ea5e9]/20"
          >
            <span className="mr-2">🏠</span> Go Home
          </Link>
        </div>
        
      </div>
    </div>
  );
};

export default NotFoundPage;
