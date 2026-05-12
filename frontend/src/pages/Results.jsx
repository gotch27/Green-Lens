import { useEffect, useRef } from 'react';
import { useLocation, useNavigate, Link } from 'react-router-dom';

// Icons cycled across treatment steps (list[str], no titles from ML)
const STEP_ICONS = ['🧪', '✂️', '🌱', '💊', '🔬', '📋'];

function pct(confidence) {
  return Math.round((confidence ?? 0) * 100);
}

function severityTag(isSick, confidence) {
  if (!isSick) return { label: '✓ Healthy', cls: 'tag-green' };
  const p = pct(confidence);
  if (p >= 80) return { label: '🔴 High Severity', cls: 'tag-red' };
  if (p >= 50) return { label: '🟡 Medium Severity', cls: 'tag-amber' };
  return { label: '🟢 Low Severity', cls: 'tag-green' };
}

function spreadRisk(weather) {
  if (!weather || weather.humidity == null) return null;
  if (weather.humidity > 70 && (weather.temperature ?? 0) > 18) return 'High';
  if (weather.humidity > 50) return 'Moderate';
  return 'Low';
}

function resolveImageUrl(rawUrl) {
  if (!rawUrl) return null;
  // Relative paths (e.g. /media/scans/…) go through the Vite proxy — return as-is.
  // Absolute URLs (http/https) are returned unchanged.
  return rawUrl;
}

// ── Empty state ──────────────────────────────────────────────────────────────
function NoResult() {
  return (
    <div>
      <div className="page-header">
        <div className="page-title">Diagnosis <span>Results</span></div>
        <div className="page-sub">No scan data found</div>
      </div>
      <div className="glass-card" style={{ padding: 40, textAlign: 'center' }}>
        <div style={{ fontSize: 40, marginBottom: 14 }}>🌿</div>
        <div style={{ fontSize: 14, color: 'var(--text-muted)', marginBottom: 24, lineHeight: 1.6 }}>
          No diagnosis to display yet.<br />Upload a plant photo to get started.
        </div>
        <Link to="/scan" className="btn btn-primary">🔬 Scan a Plant</Link>
      </div>
    </div>
  );
}

// ── Main component ───────────────────────────────────────────────────────────
export default function Results() {
  const { state }  = useLocation();
  const navigate   = useNavigate();
  const barRef     = useRef(null);
  const result     = state?.result;

  // Animate confidence bar on mount
  useEffect(() => {
    if (!result || !barRef.current) return;
    const id = setTimeout(() => {
      if (barRef.current) barRef.current.style.width = `${pct(result.confidence)}%`;
    }, 120);
    return () => clearTimeout(id);
  }, [result]);

  if (!result) return <NoResult />;

  const confidencePct = pct(result.confidence);
  const imageUrl      = resolveImageUrl(result.image_url);
  const severity      = severityTag(result.is_sick, result.confidence);
  const weather       = result.weather ?? null;
  const risk          = spreadRisk(weather);

  return (
    <div>
      <div className="page-header">
        <div className="page-title">Diagnosis <span>Results</span></div>
        <div className="page-sub">AI prediction, treatment guidance, and weather context</div>
      </div>

      <div className="results-grid">

        {/* ── Left column ── */}
        <div>

          {/* Analysed image */}
          <div
            className="analyzed-img glass-card"
            style={{ height: 260, flexDirection: 'column', gap: 8 }}
          >
            <div className="confidence-badge">{confidencePct}% Confidence</div>
            {imageUrl ? (
              <img
                src={imageUrl}
                alt="Analysed plant"
                style={{ width: '100%', height: '100%', objectFit: 'cover', display: 'block' }}
              />
            ) : (
              <>
                <span style={{ fontSize: 32 }}>🍃</span>
                <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>Analysed image appears here</div>
              </>
            )}
          </div>

          {/* Action row */}
          <div className="export-row">
            <button
              className="btn btn-ghost"
              style={{ flex: 1, justifyContent: 'center' }}
              onClick={() => window.print()}
            >
              📄 Export PDF
            </button>
            <button
              className="btn btn-ghost"
              style={{ flex: 1, justifyContent: 'center' }}
              onClick={() => navigate('/history')}
            >
              💾 View History
            </button>
          </div>

          {/* Agrometeorological context */}
          {weather && (
            <div className="glass-card" style={{ marginTop: 14 }}>
              <div className="weather-context">
                <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text)', marginBottom: 4 }}>
                  🌦 Agrometeorological Context
                </div>
                <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 8 }}>
                  {weather.recommendation || 'Weather data recorded for this scan'}
                </div>
                <div className="wc-grid">
                  <div className="wc-item">
                    <div className="wc-val">{risk ?? '—'}</div>
                    <div className="wc-key">Spread risk</div>
                  </div>
                  <div className="wc-item">
                    <div className="wc-val">
                      {weather.temperature != null ? `${weather.temperature}°C` : '—'}
                    </div>
                    <div className="wc-key">Temperature</div>
                  </div>
                  <div className="wc-item">
                    <div className="wc-val">
                      {weather.humidity != null ? `${weather.humidity}%` : '—'}
                    </div>
                    <div className="wc-key">Humidity</div>
                  </div>
                  <div className="wc-item">
                    <div className="wc-val">{weather.city || '—'}</div>
                    <div className="wc-key">Location</div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Summary */}
          {result.description && (
            <div className="glass-card" style={{ marginTop: 12 }}>
              <div style={{ padding: 16, fontSize: 12, color: 'var(--text-muted)', lineHeight: 1.7 }}>
                <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text)', marginBottom: 8 }}>
                  📋 Summary for Agronomist
                </div>
                {result.description}
              </div>
            </div>
          )}
        </div>

        {/* ── Right column ── */}
        <div>

          {/* Disease card */}
          <div className="glass-card disease-card">
            <div className="disease-name">
              {result.is_sick
                ? `${result.diagnosis ?? 'Disease'} Detected`
                : (result.diagnosis ?? 'Plant Healthy')}
            </div>

            {result.characteristics?.length > 0 && (
              <div className="disease-sci">{result.characteristics[0]}</div>
            )}

            {/* Confidence bar */}
            <div className="confidence-bar-wrap">
              <div className="confidence-label">
                <span>Detection confidence</span>
                <span style={{ color: 'var(--accent)', fontWeight: 600 }}>{confidencePct}%</span>
              </div>
              <div className="confidence-bar">
                <div ref={barRef} className="confidence-fill" style={{ width: 0 }} />
              </div>
            </div>

            {/* Tags */}
            <div className="tag-row">
              <span className={`tag ${severity.cls}`}>{severity.label}</span>
              {risk === 'High'   && <span className="tag tag-amber">⚠ Spreading</span>}
              {result.is_sick    && <span className="tag tag-green">✓ Treatable</span>}
            </div>
          </div>

          {/* Treatment steps */}
          {result.treatment_steps?.length > 0 && (
            <>
              <div className="section-label">Treatment Recommendations</div>
              {result.treatment_steps.map((step, i) => (
                <div key={i} className="glass-card rec-card">
                  <div className="rec-header">
                    {STEP_ICONS[i % STEP_ICONS.length]} Step {i + 1}
                  </div>
                  <div className="rec-body">{step}</div>
                </div>
              ))}
            </>
          )}

          {/* Further reading */}
          {result.links?.length > 0 && (
            <div className="glass-card rec-card">
              <div className="rec-header">🔗 Further Reading</div>
              <div className="rec-body" style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                {result.links.map((url, i) => (
                  <a
                    key={i}
                    href={url}
                    target="_blank"
                    rel="noreferrer"
                    style={{ color: 'var(--accent)', wordBreak: 'break-all' }}
                  >
                    {url}
                  </a>
                ))}
              </div>
            </div>
          )}

        </div>
      </div>
    </div>
  );
}
