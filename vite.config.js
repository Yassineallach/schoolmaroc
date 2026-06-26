import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  build: {
    outDir: "dist",
    chunkSizeWarningLimit: 3000,
  },
  // Allow CDN dynamic imports (Firebase loaded from gstatic at runtime)
  optimizeDeps: {
    exclude: [],
  },
});
