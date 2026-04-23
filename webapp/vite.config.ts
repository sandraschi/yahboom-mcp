import path from "node:path";
import react from "@vitejs/plugin-react";
import { createLogger, defineConfig } from "vite";

let lastConnRefusedProxyLogMs = 0;
const PROXY_CONN_REFUSED_THROTTLE_MS = 5000;

/**
 * Vite logs proxy failures in split lines: first `[vite] http proxy error: /api/...`,
 * then `Error: connect ECONNREFUSED 127.0.0.1:10892`. Throttle both.
 */
function isDevProxyBackendRefused(msg: unknown): boolean {
  const text = typeof msg === "string" ? msg : msg != null ? String(msg) : "";
  if (text.includes("[vite] http proxy error")) {
    return true;
  }
  return (
    text.includes("ECONNREFUSED") &&
    (text.includes("127.0.0.1:10892") || text.includes("localhost:10892"))
  );
}

function throttledViteLogger() {
  const logger = createLogger();
  const origInfo = logger.info.bind(logger);
  const origWarn = logger.warn.bind(logger);
  const origError = logger.error.bind(logger);

  const throttle = (
    msg: unknown,
    options: undefined | Parameters<typeof origWarn>[1],
    orig: typeof origWarn,
  ) => {
    if (isDevProxyBackendRefused(msg)) {
      const now = Date.now();
      if (now - lastConnRefusedProxyLogMs < PROXY_CONN_REFUSED_THROTTLE_MS) {
        return;
      }
      lastConnRefusedProxyLogMs = now;
      const text = typeof msg === "string" ? msg : msg != null ? String(msg) : "";
      const head = text.split("\n")[0] ?? text;
      orig(
        `${head} (similar dev-proxy → :10892 errors suppressed for ${PROXY_CONN_REFUSED_THROTTLE_MS / 1000}s)`,
        options,
      );
      return;
    }
    orig(msg, options);
  };

  logger.info = (msg, options) => throttle(msg, options, origInfo);
  logger.warn = (msg, options) => throttle(msg, options, origWarn);
  logger.error = (msg, options) => throttle(msg, options, origError);
  return logger;
}

// https://vitejs.dev/config/
export default defineConfig({
  customLogger: throttledViteLogger(),
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
        target: "http://127.0.0.1:10892",
        changeOrigin: true,
        timeout: 60000,
        proxyTimeout: 60000,
      },
      "/stream": {
        target: "http://127.0.0.1:10892",
        changeOrigin: true,
        timeout: 0,
        proxyTimeout: 0,
      },
    },
  },
});
