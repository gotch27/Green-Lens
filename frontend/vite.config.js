/**
 * vite.config.js — Vite dev server configuration.
 *
 * Proxy rules forward requests to the Django backend (port 8000),
 * avoiding CORS issues during local development:
 *
 *   /api/*    → http://localhost:8000/api/*    (Django REST API)
 *   /media/*  → http://localhost:8000/media/*  (uploaded images)
 *
 * IMPORTANT: Because of these proxies, the axios client must NOT set a
 * baseURL. Setting baseURL: 'http://localhost:8000' would bypass the proxy
 * and cause CORS errors in the browser.
 */

import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      // Forward API calls to Django backend
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      // Forward media (uploaded images) to Django — needed because
      // <img> tags cannot send Bearer tokens, so images must be served
      // without authentication via /media/ URLs.
      '/media': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
});
