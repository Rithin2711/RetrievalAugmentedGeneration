import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { resolve } from "path";

// OutDir is placed ready to be copied to ../static later as build step
export default defineConfig({
  plugins: [react()],
  build: {
    outDir: resolve(__dirname, "../static"),
    emptyOutDir: true
  },
  server: {
    port: 5173
  }
});
