import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';

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

function rainTrend(p) {
  if (p > 60) return 'Heavy rain likely today';
  if (p > 25) return 'Showers possible';
  return 'Dry conditions';
}

async function fetchWeather(lat, lon) {
  const params = new URLSearchParams({
    latitude: lat,
    longitude: lon,
    current: 'temperature_2m,relative_humidity_2m,precipitation_probability',
  });
  const res = await fetch(`https://api.open-meteo.com/v1/forecast?${params}`);
  if (!res.ok) throw new Error(`Weather API error ${res.status}`);
  return res.json();
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
  const [weather, setWeather] = useState(null);
  const [status, setStatus] = useState('locating'); // locating | fetching | ready | error
  const [errorMsg, setErrorMsg] = useState('');

  useEffect(() => {
    if (!navigator.geolocation) {
      setErrorMsg('Geolocation not supported by this browser');
      setStatus('error');
      return;
    }

    navigator.geolocation.getCurrentPosition(
      async ({ coords }) => {
        setStatus('fetching');
        try {
          const data = await fetchWeather(coords.latitude, coords.longitude);
          setWeather(data.current);
          setStatus('ready');
        } catch {
          setErrorMsg('Could not load weather data');
          setStatus('error');
        }
      },
      () => {
        setErrorMsg('Location access denied — enable it to see live weather');
        setStatus('error');
      },
    );
  }, []);

  const loading = status === 'locating' || status === 'fetching';

  const tempVal  = loading ? '…' : status === 'error' ? '—' : `${Math.round(weather.temperature_2m)}°C`;
  const humVal   = loading ? '…' : status === 'error' ? '—' : `${weather.relative_humidity_2m}%`;
  const rainVal  = loading ? '…' : status === 'error' ? '—' : `${weather.precipitation_probability}%`;

  const tempNote  = loading ? 'Fetching location…' : status === 'error' ? errorMsg : tempTrend(weather.temperature_2m);
  const humNote   = loading ? 'Fetching location…' : status === 'error' ? '' : humidityTrend(weather.relative_humidity_2m);
  const rainNote  = loading ? 'Fetching location…' : status === 'error' ? '' : rainTrend(weather.precipitation_probability);

  return (
    <div>
      <div className="page-header">
        <div className="page-title">
          {getGreeting()}, <span>Agronomist</span>
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
          <div className="section-label">Live Weather Conditions</div>
          <div className="grid-3" style={{ marginBottom: 16 }}>
            <WeatherCard icon="🌡" value={tempVal} label="Temperature" trend={tempNote} loading={loading} />
            <WeatherCard icon="💧" value={humVal}  label="Humidity"    trend={humNote}  loading={loading} />
            <WeatherCard icon="🌧" value={rainVal} label="Rain Chance" trend={rainNote} loading={loading} />
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
                <div>🟢 Tomato scanned · 2h ago</div>
                <div>🟡 Wheat analyzed · 1d ago</div>
                <div>🔴 Blight detected · 3d ago</div>
                <div>🟢 Corn healthy · 5d ago</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
