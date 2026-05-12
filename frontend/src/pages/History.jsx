import { useState, useEffect, useMemo } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { getScanHistory, getScanDetail } from '../api/scans';

// ── Helpers ──────────────────────────────────────────────────────────────────

function formatDate(iso) {
  return new Date(iso).toLocaleDateString('en-US', {
    month: 'short',
    day:   'numeric',
    year:  'numeric',
  });
}

function statusFor(isSick) {
  if (isSick === true)  return { label: 'Sick',    color: 'var(--error)' };
  if (isSick === false) return { label: 'Healthy', color: 'var(--accent)' };
  return                       { label: 'Pending', color: 'var(--text-dim)' };
}

function computeStats(scans) {
  const total   = scans.length;
  const sick    = scans.filter(s => s.is_sick === true).length;
  const healthy = scans.filter(s => s.is_sick === false).length;

  const freq = {};
  scans.forEach(s => {
    if (s.diagnosis) freq[s.diagnosis] = (freq[s.diagnosis] ?? 0) + 1;
  });
  const mostCommon = Object.entries(freq).sort((a, b) => b[1] - a[1])[0]?.[0] ?? '—';

  return { total, sick, healthy, mostCommon };
}

const DAY_MS = 86_400_000;

// ── Sub-components ───────────────────────────────────────────────────────────

function SkeletonRow() {
  return (
    <div className="history-row" style={{ pointerEvents: 'none' }}>
      <div className="h-num">—</div>
      <div style={{ display:'flex', alignItems:'center' }}>
        <span className="skeleton" style={{ height:11, width:'65%', display:'block' }} />
      </div>
      <div>
        <span className="skeleton" style={{ height:11, width:'55%', display:'block' }} />
      </div>
      <div>
        <span className="skeleton" style={{ height:11, width:'72%', display:'block' }} />
      </div>
      <div>
        <span className="skeleton" style={{ height:11, width:'40%', display:'block' }} />
      </div>
      <div />
    </div>
  );
}

function EmptyState({ hasScans }) {
  return (
    <div style={{ padding:'44px 16px', textAlign:'center' }}>
      <div style={{ fontSize:36, marginBottom:12 }}>{hasScans ? '🔍' : '🌿'}</div>
      <div style={{ fontSize:13, color:'var(--text-muted)', lineHeight:1.7, marginBottom: hasScans ? 0 : 20 }}>
        {hasScans
          ? 'No scans match your search or filters.'
          : <>No scans yet.<br />Upload your first plant photo to get started.</>}
      </div>
      {!hasScans && (
        <Link to="/scan" className="btn btn-primary">🔬 Scan a Plant</Link>
      )}
    </div>
  );
}

function FilterOption({ active, dot, onClick, children }) {
  return (
    <div
      className="filter-option"
      onClick={onClick}
      style={{
        background: active ? 'var(--glass-hover)' : '',
        color: active ? 'var(--text)' : '',
        borderRadius: 8,
      }}
    >
      {dot && <div className="filter-dot" style={{ background: dot }} />}
      {children}
    </div>
  );
}

// ── Main component ───────────────────────────────────────────────────────────

export default function History() {
  const navigate = useNavigate();

  const [scans,        setScans]        = useState([]);
  const [loading,      setLoading]      = useState(true);
  const [opening,      setOpening]      = useState(null); // scan id being opened
  const [error,        setError]        = useState('');
  const [query,        setQuery]        = useState('');
  const [statusFilter, setStatusFilter] = useState('all');  // 'all' | 'sick' | 'healthy'
  const [dateFilter,   setDateFilter]   = useState('all');  // 'all' | '7d' | '30d'

  useEffect(() => {
    getScanHistory()
      .then(data => setScans(data))
      .catch(() => setError('Failed to load scan history. Please try again.'))
      .finally(() => setLoading(false));
  }, []);

  const filtered = useMemo(() => {
    const q   = query.trim().toLowerCase();
    const now = Date.now();

    return scans.filter(s => {
      if (q) {
        const inDiagnosis = s.diagnosis?.toLowerCase().includes(q);
        const inCity      = s.city?.toLowerCase().includes(q);
        if (!inDiagnosis && !inCity) return false;
      }
      if (statusFilter === 'sick'    && s.is_sick !== true)  return false;
      if (statusFilter === 'healthy' && s.is_sick !== false) return false;
      if (dateFilter === '7d'  && now - new Date(s.created_at).getTime() > 7  * DAY_MS) return false;
      if (dateFilter === '30d' && now - new Date(s.created_at).getTime() > 30 * DAY_MS) return false;
      return true;
    });
  }, [scans, query, statusFilter, dateFilter]);

  const stats = useMemo(() => computeStats(scans), [scans]);

  return (
    <div>
      <div className="page-header">
        <div className="page-title">Scan <span>History</span></div>
        <div className="page-sub">Review previous analyses and export past reports</div>
      </div>

      <div className="history-layout">

        {/* ── Table column ── */}
        <div>

          {/* Search bar */}
          <div className="search-bar glass-card">
            <span style={{ fontSize:14, color:'var(--text-dim)' }}>🔍</span>
            <input
              type="text"
              placeholder="Search by diagnosis or city…"
              value={query}
              onChange={e => setQuery(e.target.value)}
            />
            {query && (
              <span
                title="Clear search"
                style={{ fontSize:12, color:'var(--text-dim)', cursor:'pointer', userSelect:'none' }}
                onClick={() => setQuery('')}
              >
                ✕
              </span>
            )}
            <span style={{
              fontSize:11, color:'var(--text-dim)',
              background:'var(--glass)', padding:'3px 8px',
              borderRadius:5, border:'1px solid var(--glass-border)',
              flexShrink:0,
            }}>
              ⌘K
            </span>
          </div>

          {/* Table */}
          <div className="history-table glass-card">
            <div className="history-head">
              <div>#</div>
              <div>Diagnosis</div>
              <div>City</div>
              <div>Date</div>
              <div>Status</div>
              <div>Action</div>
            </div>

            {/* Loading skeleton */}
            {loading && Array.from({ length: 6 }, (_, i) => <SkeletonRow key={i} />)}

            {/* Error */}
            {!loading && error && (
              <div style={{ padding:'28px 16px', textAlign:'center', fontSize:13, color:'var(--error)' }}>
                {error}
              </div>
            )}

            {/* Empty state */}
            {!loading && !error && filtered.length === 0 && (
              <EmptyState hasScans={scans.length > 0} />
            )}

            {/* Rows */}
            {!loading && !error && filtered.map((scan, i) => {
              const status = statusFor(scan.is_sick);
              const isOpening = opening === scan.id;
              return (
                <div
                  key={scan.id}
                  className="history-row"
                  onClick={async () => {
                    if (opening) return;
                    setOpening(scan.id);
                    try {
                      const full = await getScanDetail(scan.id);
                      navigate('/results', { state: { result: full } });
                    } catch {
                      navigate('/results', { state: { result: scan } });
                    } finally {
                      setOpening(null);
                    }
                  }}
                  style={{ opacity: isOpening ? 0.6 : 1 }}
                >
                  <div className="h-num">{i + 1}</div>
                  <div className="h-plant">{scan.diagnosis ?? '—'}</div>
                  <div className="h-disease">{scan.city || '—'}</div>
                  <div className="h-date">{formatDate(scan.created_at)}</div>
                  <div className="h-conf" style={{ color: status.color }}>{status.label}</div>
                  <div className="h-action">
                    <div className="icon-btn" title="View results">
                      {isOpening ? '⏳' : '👁'}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* ── Sidebar ── */}
        <div>

          {/* Filters */}
          <div className="glass-card" style={{ marginBottom:14 }}>
            <div className="filter-section">
              <div className="filter-title">Filter by Status</div>
              <FilterOption active={statusFilter==='all'}     dot="var(--text-dim)" onClick={() => setStatusFilter('all')}>All</FilterOption>
              <FilterOption active={statusFilter==='sick'}    dot="#ff7070"         onClick={() => setStatusFilter('sick')}>Sick</FilterOption>
              <FilterOption active={statusFilter==='healthy'} dot="var(--accent)"   onClick={() => setStatusFilter('healthy')}>Healthy</FilterOption>

              <div style={{ height:10 }} />

              <div className="filter-title">Filter by Date</div>
              <FilterOption active={dateFilter==='7d'}  onClick={() => setDateFilter('7d')}>📅 Last 7 days</FilterOption>
              <FilterOption active={dateFilter==='30d'} onClick={() => setDateFilter('30d')}>📅 Last 30 days</FilterOption>
              <FilterOption active={dateFilter==='all'} onClick={() => setDateFilter('all')}>📅 All time</FilterOption>
            </div>
          </div>

          {/* Summary — always derived from the full unfiltered dataset */}
          <div className="glass-card">
            <div className="summary-card">
              <div className="filter-title" style={{ marginBottom:12 }}>History Summary</div>
              <div className="summary-stat">
                <span>Total scans</span>
                <span className="summary-val">{loading ? '…' : stats.total}</span>
              </div>
              <div className="summary-stat">
                <span>Diseases found</span>
                <span className="summary-val">{loading ? '…' : stats.sick}</span>
              </div>
              <div className="summary-stat">
                <span>Healthy plants</span>
                <span className="summary-val">{loading ? '…' : stats.healthy}</span>
              </div>
              <div className="summary-stat">
                <span>Most common</span>
                <span className="summary-val" style={{ fontSize:11, textAlign:'right', maxWidth:110 }}>
                  {loading ? '…' : stats.mostCommon}
                </span>
              </div>
            </div>
          </div>

        </div>
      </div>
    </div>
  );
}
