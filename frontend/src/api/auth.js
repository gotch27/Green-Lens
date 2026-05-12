// Auth endpoints (JWT via djangorestframework-simplejwt):
//   POST /api/auth/register/ { username, email, password }  → { access, refresh, user }
//   POST /api/auth/login/    { username, password }         → { access, refresh, user }
//   POST /api/auth/refresh/  { refresh }                    → { access }
//   GET  /api/auth/me/                                      → { user }

import client from './client';

const ACCESS_KEY  = 'gl_access';
const REFRESH_KEY = 'gl_refresh';

// ── Token helpers ──────────────────────────────────────────────────────────

export function getAccessToken()  { return localStorage.getItem(ACCESS_KEY);  }
export function getRefreshToken() { return localStorage.getItem(REFRESH_KEY); }
export function isAuthenticated() { return Boolean(localStorage.getItem(ACCESS_KEY)); }

function storeTokens({ access, refresh }) {
  localStorage.setItem(ACCESS_KEY, access);
  if (refresh) localStorage.setItem(REFRESH_KEY, refresh);
}

export function logout() {
  localStorage.removeItem(ACCESS_KEY);
  localStorage.removeItem(REFRESH_KEY);
}

// ── API calls ──────────────────────────────────────────────────────────────

export async function login(username, password) {
  const { data } = await client.post('/api/auth/login/', { username, password });
  storeTokens(data);
  return data;
}

export async function register(username, email, password) {
  const { data } = await client.post('/api/auth/register/', { username, email, password });
  storeTokens(data);
  return data;
}

export async function getMe() {
  const { data } = await client.get('/api/auth/me/');
  return data.user;
}
