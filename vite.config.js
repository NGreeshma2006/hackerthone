import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  root: 'frontend',
  // Keep cookies first-party and route every API call through vercel.json.
  // Override stale VITE_API_URL values only on Vercel builds.
  define: process.env.VERCEL === '1' ? { 'import.meta.env.VITE_API_URL': JSON.stringify('/api') } : {},
  server: {
    host: '0.0.0.0',
    port: 5173,
    proxy: { '/api': { target: 'http://127.0.0.1:8000', changeOrigin: true, rewrite: path => path.replace(/^\/api/, '') } },
  },
  preview: {
    host: '0.0.0.0',
    port: 4173,
    proxy: { '/api': { target: 'http://127.0.0.1:8000', changeOrigin: true, rewrite: path => path.replace(/^\/api/, '') } },
  }
});
