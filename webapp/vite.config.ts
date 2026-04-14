import path from "node:path";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    port: 10893,
    strictPort: true,
    host: true,
    proxy: {
      "/api": {
        target: "http://localhost:10892",
        changeOrigin: true,
        timeout: 60000,
        proxyTimeout: 60000,
      },
      "/stream": {
        target: "http://localhost:10892",
        changeOrigin: true,
        timeout: 0,
        proxyTimeout: 0,
      },
    },
  },
});
