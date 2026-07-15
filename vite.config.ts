import { defineConfig } from "vite";
import { svelte } from "@sveltejs/vite-plugin-svelte";

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [svelte()],
  clearScreen: false,
  server: {
    port: 5173,
    strictPort: true,
    // Proxy for PWA development - bypasses CORS
    proxy: {
      '/rpc': {
        target: 'http://localhost:18457',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/rpc/, ''),
        configure: (proxy) => {
          // Add basic auth header if not present
          proxy.on('proxyReq', (proxyReq) => {
            if (!proxyReq.getHeader('authorization')) {
              // Default local-dev credentials (freebankd regtest; change as needed)
              const auth = Buffer.from('rpcuser:rpcpassword').toString('base64');
              proxyReq.setHeader('Authorization', `Basic ${auth}`);
            }
          });
        },
      },
    },
  },
  envPrefix: ["VITE_", "TAURI_"],
  build: {
    target: "esnext",
    minify: !process.env.TAURI_DEBUG ? "esbuild" : false,
    sourcemap: !!process.env.TAURI_DEBUG,
  },
});
