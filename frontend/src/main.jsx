/**
 * React Application Entry Point
 * ===============================
 * Mounts the React app into the DOM.
 * Imports global styles (Tailwind + custom CSS).
 */

import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App.jsx";
import "./index.css";

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
