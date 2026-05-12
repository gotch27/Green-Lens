import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { getMe } from '../api/auth';
import { getScanHistory } from '../api/scans';
import { getWeather } from '../api/weather';

const DEFAULT_CITY = 'Skopje';

function getGreeting() {
  const h = new Date().getHours();
  if (h >= 5 && h < 12) return 'Good morning';
  if (h < 17) return 'Good afternoon';
  if (h < 21) return 'Good evening';
  return 'Good night';
}

function formatDate(date) {
  return date.toLocaleDateString('en-US', {
    weekday: 'long',
    month: 'long',
    day: 'numeric',
    year: 'numeric',
  });
}

function tempTrend(t) {
  if (t > 30) return 'Hot — heat stress risk for crops';
  if (t > 22) return 'Warm — favourable growing conditions';
  if (t > 12) return 'Cool — reduced disease activity';
  return 'Cold — frost risk possible';
}

function humidityTrend(h) {
  if (h > 70) return 'High — watch for fungal spread';
  if (h > 50) return 'Moderate — watch for fungal';
  return 'Low — low disease risk';
}

function formatRelative(iso) {
  const diffMs = Date.now() - new Date(iso).getTime();
  const hours = Math.max(1, Math.round(diffMs / 3_600_000));
  if (hours < 24) return `${hours}h ago`;
  return `${Math.round(hours / 24)}d ago`;
}

function WeatherCard({ icon, value, label, trend, loading }) {
  return (
    <div className="glass-card weather-card">
      <div className="weather-icon">{icon}</div>
      <div className="weather-val" style={{ opacity: loading ? 0.35 : 1 }}>
        {value}
      </div>
      <div className="weather-label">{label}</div>
      <div className="weather-trend">{trend}</div>
    </div>
  );
}

export default function Dashboard() {
  const navigate = useNavigate();
  const [user, setUser] = useState(null);
  const [weather, setWeather] = useState(null);
  const [recentScans, setRecentScans] = useState([]);
  const [status, setStatus] = useState('fetching'); // fetching | ready | error
  const [recentStatus, setRecentStatus] = useState('fetching');
  const [errorMsg, setErrorMsg] = useState('');

  useEffect(() => {
    getMe().then(setUser).catch(() => {});

    getWeather(DEFAULT_CITY)
      .then(data => {
        setWeather(data);
        setStatus('ready');
      })
      .catch(() => {
        setErrorMsg('Could not load backend weather data');
        setStatus('error');
      });

    getScanHistory()
      .then(data => {
        setRecentScans(data.slice(0, 4));
        setRecentStatus('ready');
      })
      .catch(() => setRecentStatus('error'));
  }, []);

  const loading = status === 'fetching';

  const tempVal  = loading ? '…' : status === 'error' || weather.temperature == null ? '—' : `${Math.round(weather.temperature)}°C`;
  const humVal   = loading ? '…' : status === 'error' || weather.humidity == null ? '—' : `${weather.humidity}%`;
  const cityVal  = loading ? '…' : status === 'error' ? DEFAULT_CITY : weather.city;

  const tempNote  = loading ? 'Fetching weather…' : status === 'error' ? errorMsg : tempTrend(weather.temperature);
  const humNote   = loading ? 'Fetching weather…' : status === 'error' ? '' : humidityTrend(weather.humidity);
  const cityNote  = loading ? 'Fetching weather…' : status === 'error' ? 'Using default dashboard city' : weather.recommendation;

  return (
    <div>
      <div className="page-header">
        <div className="page-title">
          {getGreeting()}, <span>{user?.username || 'there'}</span>
        </div>
        <div className="page-sub">
          Here's your field overview for today · {formatDate(new Date())}
        </div>
      </div>

      <div className="grid-main">
        {/* ── Left column ── */}
        <div>
          {/* Hero banner */}
          <div className="hero-banner glass-card">
            <div className="hero-title">
              AI-powered plant <em>disease detection</em>
            </div>
            <div className="hero-desc">
              Upload a photo of your crops and get instant diagnosis, treatment
              recommendations, and weather-aware insights — all in under 10 seconds.
            </div>
            <div className="hero-actions">
              <Link to="/scan" className="btn btn-primary">🌿 Scan a Plant</Link>
              <Link to="/history" className="btn btn-ghost">View History</Link>
            </div>
          </div>

          {/* Weather cards */}
          <div className="section-label">Backend Weather Conditions</div>
          <div className="grid-3" style={{ marginBottom: 16 }}>
            <WeatherCard icon="🌡" value={tempVal} label="Temperature" trend={tempNote} loading={loading} />
            <WeatherCard icon="💧" value={humVal}  label="Humidity"    trend={humNote}  loading={loading} />
            <WeatherCard icon="📍" value={cityVal} label="Location" trend={cityNote} loading={loading} />
          </div>

          {/* Scan CTA */}
          <div
            className="scan-cta glass-card"
            role="button"
            tabIndex={0}
            onClick={() => navigate('/scan')}
            onKeyDown={e => e.key === 'Enter' && navigate('/scan')}
          >
            <span className="scan-cta-icon">📸</span>
            <div className="scan-cta-title">Click to Scan Your Plant</div>
            <div className="scan-cta-sub">
              Drag &amp; drop or click to upload a photo for instant AI analysis
            </div>
          </div>
        </div>

        {/* ── Right column ── */}
        <div style={{ animation: 'fadeUp 0.5s 0.35s ease both', opacity: 0 }}>
          <div className="ad-box">
            <div className="ad-label">Sponsored</div>
            <div className="ad-content">Advertisement</div>
          </div>

          <div className="glass-card" style={{ marginTop: 14 }}>
            <div style={{ padding: 16 }}>
              <div className="section-label" style={{ marginBottom: 10 }}>
                Recent Activity
              </div>
              <div style={{ fontSize: 12, color: 'var(--text-muted)', lineHeight: 2 }}>
                {recentStatus === 'fetching' && <div>Loading scans…</div>}
                {recentStatus === 'error' && <div>Could not load recent scans.</div>}
                {recentStatus === 'ready' && recentScans.length === 0 && <div>No scans yet.</div>}
                {recentStatus === 'ready' && recentScans.map(scan => (
                  <div key={scan.id}>
                    {scan.is_sick ? '🔴' : '🟢'} {scan.diagnosis || 'Scan'} · {formatRelative(scan.created_at)}
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
