/**
 * auth.js — Authentication helpers for JWT-based login/register/logout.
 *
 * Backend endpoints (djangorestframework-simplejwt):
 *   POST /api/auth/register/  { username, email, password }  → { access, refresh, user }
 *   POST /api/auth/login/     { username, password }         → { access, refresh, user }
 *   POST /api/auth/refresh/   { refresh }                   → { access }
 *   GET  /api/auth/me/        (Bearer token required)       → { user }
 *
 * Tokens are stored in localStorage:
 *   gl_access  — JWT access token,  expires in 15 minutes
 *   gl_refresh — JWT refresh token, expires in 7 days
 *
 * NOTE: Do NOT import client.js here at the top-level in a way that creates a
 * circular dependency. client.js already imports from localStorage directly.
 */

import client from './client';

const ACCESS_KEY  = 'gl_access';
const REFRESH_KEY = 'gl_refresh';

// ── Token helpers ──────────────────────────────────────────────────────────

/** Returns the raw access token string, or null if not logged in. */
export function getAccessToken()  { return localStorage.getItem(ACCESS_KEY);  }

/** Returns the raw refresh token string, or null if not stored. */
export function getRefreshToken() { return localStorage.getItem(REFRESH_KEY); }

/** Returns true if an access token exists (user is considered logged in). */
export function isAuthenticated() { return Boolean(localStorage.getItem(ACCESS_KEY)); }

/** Persists both tokens from a login/register response. */
function storeTokens({ access, refresh }) {
  localStorage.setItem(ACCESS_KEY, access);
  if (refresh) localStorage.setItem(REFRESH_KEY, refresh);
}

/** Removes both tokens — effectively logs the user out on the client side. */
export function logout() {
  localStorage.removeItem(ACCESS_KEY);
  localStorage.removeItem(REFRESH_KEY);
}

// ── API calls ──────────────────────────────────────────────────────────────

/**
 * Login with username + password.
 * Note: the backend accepts username, NOT email, for login.
 */
export async function login(username, password) {
  const { data } = await client.post('/api/auth/login/', { username, password });
  storeTokens(data);
  return data;
}

/**
 * Register a new account.
 * On success the backend returns tokens immediately — no separate login needed.
 */
export async function register(username, email, password) {
  const { data } = await client.post('/api/auth/register/', { username, email, password });
  storeTokens(data);
  return data;
}

/** Fetch the currently authenticated user's profile. */
export async function getMe() {
  const { data } = await client.get('/api/auth/me/');
  return data.user;
}
