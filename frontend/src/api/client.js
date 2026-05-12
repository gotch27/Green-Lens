/**
 * client.js — Axios instance with automatic JWT auth & silent token refresh.
 *
 * Why we read localStorage directly here instead of importing from auth.js:
 *   auth.js imports this file (client), and this file would import auth.js →
 *   circular ES module dependency that crashes at runtime. Reading localStorage
 *   directly with the same key constants breaks the cycle.
 *
 * Token storage keys must stay in sync with auth.js:
 *   gl_access  — short-lived JWT access token  (15 min)
 *   gl_refresh — long-lived JWT refresh token  (7 days)
 */

import axios from 'axios';

const ACCESS_KEY  = 'gl_access';
const REFRESH_KEY = 'gl_refresh';

// Shared axios instance — no baseURL so Vite's proxy handles /api routes.
const client = axios.create();

// ── Request interceptor ────────────────────────────────────────────────────
// Attach Bearer token to every outgoing request if one is stored.
client.interceptors.request.use(config => {
  const token = localStorage.getItem(ACCESS_KEY);
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// ── Response interceptor ───────────────────────────────────────────────────
// On 401 Unauthorized: attempt a one-time silent refresh, then retry the
// original request with the new access token.
// Uses a shared promise (refreshPromise) so parallel 401s don't fire
// multiple refresh requests at the same time.
let refreshPromise = null;

client.interceptors.response.use(
  res => res,
  async err => {
    const original = err.config;
    const hasAccess  = Boolean(localStorage.getItem(ACCESS_KEY));
    const hasRefresh = Boolean(localStorage.getItem(REFRESH_KEY));

    if (err.response?.status === 401 && !original._retry && hasAccess && hasRefresh) {
      original._retry = true; // Prevent infinite retry loops
      try {
        // Only start one refresh request even if multiple calls fail at once
        if (!refreshPromise) {
          refreshPromise = axios
            .post('/api/auth/refresh/', { refresh: localStorage.getItem(REFRESH_KEY) })
            .then(r => {
              localStorage.setItem(ACCESS_KEY, r.data.access);
              return r.data.access;
            })
            .finally(() => { refreshPromise = null; });
        }
        const newAccess = await refreshPromise;
        original.headers.Authorization = `Bearer ${newAccess}`;
        return client(original); // Retry original request with new token
      } catch {
        // Refresh token expired or invalid — wipe tokens so ProtectedRoute
        // redirects the user back to /login automatically.
        localStorage.removeItem(ACCESS_KEY);
        localStorage.removeItem(REFRESH_KEY);
      }
    }
    return Promise.reject(err);
  }
);

export default client;
