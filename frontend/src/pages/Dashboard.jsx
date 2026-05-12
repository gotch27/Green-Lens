import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { getMe } from '../api/auth';
import { getScanHistory } from '../api/scans';
import { getWeather } from '../api/weather';

const DEFAULT_CITY = 'Skopje';
const DEFAULT_CITY_LABEL = 'Скопје';

function getGreeting() {
  const h = new Date().getHours();
  if (h >= 5 && h < 12) return 'Добро утро';
  if (h < 17) return 'Добар ден';
  if (h < 21) return 'Добра вечер';
  return 'Добра вечер';
}

function formatDate(date) {
  return date.toLocaleDateString('mk-MK', {
    weekday: 'long',
    month: 'long',
    day: 'numeric',
    year: 'numeric',
  });
}

function tempTrend(t) {
  if (t > 30) return 'Жешко — ризик од топлотен стрес';
  if (t > 22) return 'Топло — поволни услови за раст';
  if (t > 12) return 'Свежо — намалена активност на болести';
  return 'Студено — можен ризик од мраз';
}

function humidityTrend(h) {
  if (h > 70) return 'Висока — следете ширење на габи';
  if (h > 50) return 'Умерена — внимавајте на габични заболувања';
  return 'Ниска — мал ризик од болести';
}

function formatRelative(iso) {
  const diffMs = Date.now() - new Date(iso).getTime();
  const hours = Math.max(1, Math.round(diffMs / 3_600_000));
  if (hours < 24) return `пред ${hours} ч.`;
  return `пред ${Math.round(hours / 24)} д.`;
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
        setErrorMsg('Не може да се вчитаат временските податоци');
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
  const cityVal  = loading ? '…' : status === 'error' ? DEFAULT_CITY_LABEL : (weather.city === DEFAULT_CITY ? DEFAULT_CITY_LABEL : weather.city);

  const tempNote  = loading ? 'Се вчитува времето…' : status === 'error' ? errorMsg : tempTrend(weather.temperature);
  const humNote   = loading ? 'Се вчитува времето…' : status === 'error' ? '' : humidityTrend(weather.humidity);
  const cityNote  = loading ? 'Се вчитува времето…' : status === 'error' ? 'Се користи стандардниот град' : weather.recommendation;

  return (
    <div>
      <div className="page-header">
        <div className="page-title">
          {getGreeting()}, <span>{user?.username || 'кориснику'}</span>
        </div>
        <div className="page-sub">
          Преглед на вашите насади за денес · {formatDate(new Date())}
        </div>
      </div>

      <div className="grid-main">
        {/* ── Left column ── */}
        <div>
          {/* Hero banner */}
          <div className="hero-banner glass-card">
            <div className="hero-title">
              Откривање <em>болести кај растенија</em> со ВИ
            </div>
            <div className="hero-desc">
              Прикачете фотографија од вашите култури и добијте брза дијагноза,
              препораки за третман и временски контекст.
            </div>
            <div className="hero-actions">
              <Link to="/scan" className="btn btn-primary">🌿 Скенирај растение</Link>
              <Link to="/history" className="btn btn-ghost">Види историја</Link>
            </div>
          </div>

          {/* Weather cards */}
          <div className="section-label">Временски услови</div>
          <div className="grid-3" style={{ marginBottom: 16 }}>
            <WeatherCard icon="🌡" value={tempVal} label="Температура" trend={tempNote} loading={loading} />
            <WeatherCard icon="💧" value={humVal}  label="Влажност"    trend={humNote}  loading={loading} />
            <WeatherCard icon="📍" value={cityVal} label="Локација" trend={cityNote} loading={loading} />
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
            <div className="scan-cta-title">Кликнете за скенирање растение</div>
            <div className="scan-cta-sub">
              Повлечете фотографија или кликнете за ВИ анализа
            </div>
          </div>
        </div>

        {/* ── Right column ── */}
        <div style={{ animation: 'fadeUp 0.5s 0.35s ease both', opacity: 0 }}>
          <div className="ad-box">
            <div className="ad-label">Спонзорирано</div>
            <div className="ad-content">Реклама</div>
          </div>

          <div className="glass-card" style={{ marginTop: 14 }}>
            <div style={{ padding: 16 }}>
              <div className="section-label" style={{ marginBottom: 10 }}>
                Последна активност
              </div>
              <div style={{ fontSize: 12, color: 'var(--text-muted)', lineHeight: 2 }}>
                {recentStatus === 'fetching' && <div>Се вчитуваат скенирања…</div>}
                {recentStatus === 'error' && <div>Не може да се вчитаат последните скенирања.</div>}
                {recentStatus === 'ready' && recentScans.length === 0 && <div>Сè уште нема скенирања.</div>}
                {recentStatus === 'ready' && recentScans.map(scan => (
                  <div key={scan.id}>
                    {scan.is_sick ? '🔴' : '🟢'} {scan.diagnosis || 'Скенирање'} · {formatRelative(scan.created_at)}
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
