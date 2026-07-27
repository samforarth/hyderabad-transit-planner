/**
 * App Component — Root Router Setup
 * ===================================
 * Defines the page routes for the application:
 *   /                → HomePage (search form + map)
 *   /recommendations → RecommendationsPage (ranked journey cards)
 *   /journey/:index  → JourneyDetailsPage (full journey with map)
 *   *                → NotFoundPage (404)
 *
 * We use React Router v7 for client-side navigation.
 * This means page transitions are instant — no full page reloads.
 */

import { BrowserRouter, Routes, Route } from "react-router-dom";
import Navbar from "./components/Navbar.jsx";
import HomePage from "./pages/HomePage.jsx";
import RecommendationsPage from "./pages/RecommendationsPage.jsx";
import JourneyDetailsPage from "./pages/JourneyDetailsPage.jsx";
import NotFoundPage from "./pages/NotFoundPage.jsx";

function App() {
  return (
    <BrowserRouter>
      {/* Navbar appears on every page */}
      <Navbar />

      {/* Page routes */}
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/recommendations" element={<RecommendationsPage />} />
        <Route path="/journey/:index" element={<JourneyDetailsPage />} />
        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
