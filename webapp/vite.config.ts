import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig({
    plugins: [react()],
    resolve: {
        alias: {
            '@': path.resolve(__dirname, './src'),
        },
    },
    server: {
        port: 10893,
        strictPort: true,
        host: true,
        proxy: {
            '/api': { 
                target: 'http://localhost:10892', 
                changeOrigin: true,
                timeout: 60000, // 60s timeout for hardware operations
                proxyTimeout: 60000
            },
            // MJPEG is a long-lived HTTP response — avoid short proxy timeouts / buffering issues
            '/stream': { 
                target: 'http://localhost:10892', 
                changeOrigin: true,
                timeout: 0,
                proxyTimeout: 0,
            },
        },
    },
})
