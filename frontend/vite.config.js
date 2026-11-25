import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'
import tailwindcss from '@tailwindcss/vite'

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), 'VITE_');

  return {
    plugins: [
      react(),
      tailwindcss(),
    ],
    resolve: {
      alias: {
        "@": path.resolve(__dirname, "./src"),
      },
    },
    server: {
      allowedHosts: [
        "smith-sight-newsletter-recorder.trycloudflare.com",
      ],
      proxy: {
        '/api/v1': {
          target: env.VITE_API_PROXY_TARGET || 'http://127.0.0.1:8000',
          changeOrigin: true,
          configure(proxy) {
            proxy.on('proxyReq', (proxyRequest) => proxyRequest.removeHeader('origin'));
          },
        },
      },
    },
    build: {
      rollupOptions: {
        output: {
          manualChunks(id) {
            if (!id.includes('node_modules')) return undefined;
            if (/node_modules\/(react|react-dom|scheduler)\//.test(id)) return 'react-vendor';
            if (id.includes('node_modules/@supabase/')) return 'supabase-vendor';
            if (/node_modules\/(framer-motion|motion-dom|motion-utils)\//.test(id)) return 'motion-vendor';
            if (id.includes('node_modules/lucide-react/')) return 'icons-vendor';
            return undefined;
          },
        },
      },
    },
  };
});
