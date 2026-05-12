import axios from 'axios';

const ACCESS_KEY  = 'gl_access';
const REFRESH_KEY = 'gl_refresh';

const client = axios.create();

// Attach Bearer token to every request (read directly from localStorage — no auth.js import)
client.interceptors.request.use(config => {
  const token = localStorage.getItem(ACCESS_KEY);
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// On 401, try refreshing once then retry
let refreshPromise = null;

client.interceptors.response.use(
  res => res,
  async err => {
    const original = err.config;
    const hasAccess  = Boolean(localStorage.getItem(ACCESS_KEY));
    const hasRefresh = Boolean(localStorage.getItem(REFRESH_KEY));

    if (err.response?.status === 401 && !original._retry && hasAccess && hasRefresh) {
      original._retry = true;
      try {
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
        return client(original);
      } catch {
        // Refresh failed — clear tokens so ProtectedRoute redirects to login
        localStorage.removeItem(ACCESS_KEY);
        localStorage.removeItem(REFRESH_KEY);
      }
    }
    return Promise.reject(err);
  }
);

export default client;
