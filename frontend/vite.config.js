import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

// Vite configuration for Hyderabad Transit Planner
// - React plugin enables JSX transformation and Fast Refresh (hot reload)
// - Tailwind CSS plugin processes utility classes without needing PostCSS config
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 5173,
  },
});
