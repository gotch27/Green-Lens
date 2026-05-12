/**
 * App.jsx — Root component and route definitions.
 *
 * Route structure:
 *   /login     — Public login page
 *   /register  — Public registration page
 *   /*         — AppShell (requires authentication via ProtectedRoute)
 *                 /           → Dashboard
 *                 /scan       → ScanPlant (upload & analyze)
 *                 /results    → Results (diagnosis output)
 *                 /history    → History (past scans list)
 *
 * ProtectedRoute redirects unauthenticated users to /login.
 * The .bg div renders the flat background behind all routes.
 */

import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import ProtectedRoute from './components/ProtectedRoute';
import Login from './pages/Login';
import Register from './pages/Register';
import Dashboard from './pages/Dashboard';
import ScanPlant from './pages/ScanPlant';
import Results from './pages/Results';
import History from './pages/History';
import './index.css';

/** Authenticated app shell — renders sidebar + page content. */
function AppShell() {
  return (
    <ProtectedRoute>
      <div className="app">
        <Sidebar />
        <main className="main">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/scan" element={<ScanPlant />} />
            <Route path="/results" element={<Results />} />
            <Route path="/history" element={<History />} />
          </Routes>
        </main>
      </div>
    </ProtectedRoute>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      {/* Flat background layer — sits behind all content (z-index: 0) */}
      <div className="bg" />
      <Routes>
        {/* Public routes — no auth required */}
        <Route path="/login"    element={<Login />} />
        <Route path="/register" element={<Register />} />

        {/* Protected routes — redirect to /login if not authenticated */}
        <Route path="/*" element={<AppShell />} />
      </Routes>
    </BrowserRouter>
  );
}
