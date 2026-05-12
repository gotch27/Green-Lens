/**
 * ProtectedRoute.jsx — Route guard for authenticated pages.
 *
 * Checks if a JWT access token exists in localStorage.
 * If not authenticated, redirects to /login (replace so the user
 * can't press Back to return to a protected page after logout).
 *
 * Note: This is a client-side check only. The backend independently
 * validates the token on every API request via JWTAuthentication.
 */

import { Navigate } from 'react-router-dom';
import { isAuthenticated } from '../api/auth';

export default function ProtectedRoute({ children }) {
  if (!isAuthenticated()) {
    return <Navigate to="/login" replace />;
  }
  return children;
}
