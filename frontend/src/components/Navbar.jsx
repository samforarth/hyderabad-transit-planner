import React from 'react';
import { Link } from 'react-router-dom';

const Navbar = () => {
  return (
    <nav className="fixed top-0 left-0 right-0 z-50 h-[60px] glass-card flex items-center justify-between px-6">
      <Link to="/" className="flex items-center gap-2 text-[#f1f5f9] hover:text-[#0ea5e9] transition-colors">
        <span className="text-2xl">🚌</span>
        <span className="font-bold text-lg">Hyderabad Transit</span>
      </Link>
      <div className="bg-gradient-to-r from-[#0ea5e9] to-[#14b8a6] px-3 py-1 rounded-full shadow-lg shadow-[#0ea5e9]/20">
        <span className="text-sm font-semibold text-white">Planner</span>
      </div>
    </nav>
  );
};

export default Navbar;
