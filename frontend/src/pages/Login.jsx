import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { login } from '../api/auth';
import { getApiErrorMessage } from '../utils/apiErrors';

const inputStyle = {
  display: 'flex',
  alignItems: 'center',
  gap: 10,
  background: 'var(--card)',
  border: '1px solid var(--card-border)',
  borderRadius: 'var(--radius-sm)',
  padding: '11px 14px',
  transition: 'border-color 0.15s',
};

const inputFieldStyle = {
  background: 'none',
  border: 'none',
  outline: 'none',
  color: 'var(--text)',
  fontSize: 14,
  flex: 1,
  fontFamily: 'inherit',
  width: '100%',
};

export default function Login() {
  const navigate = useNavigate();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading]   = useState(false);
  const [error, setError]       = useState('');

  async function handleSubmit(e) {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await login(username, password);
      navigate('/', { replace: true });
    } catch (err) {
      setError(getApiErrorMessage(err, 'Невалидни податоци за најава. Обидете се повторно.'));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={{
      position: 'relative',
      zIndex: 1,
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '24px 16px',
    }}>
      <div style={{ width: '100%', maxWidth: 400 }}>

        {/* Logo */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 11, justifyContent: 'center', marginBottom: 28 }}>
          <div className="logo-icon" style={{ width: 36, height: 36, fontSize: 18 }}>🌿</div>
          <div>
            <div className="logo-text" style={{ fontSize: 18 }}>GreenLens</div>
            <div className="logo-sub">ВИ · Анализа на растенија</div>
          </div>
        </div>

        {/* Card */}
        <div className="glass-card" style={{ padding: 32 }}>
          <div style={{ marginBottom: 24 }}>
            <div className="page-title" style={{ fontSize: 22, marginBottom: 4 }}>
              Добредојдовте <span>назад</span>
            </div>
            <div className="page-sub">Најавете се на вашата сметка</div>
          </div>

          <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>

            {/* Username */}
            <div style={inputStyle}>
              <span style={{ fontSize: 14, opacity: 0.45 }}>👤</span>
              <input
                style={inputFieldStyle}
                type="text"
                placeholder="Корисничко име"
                value={username}
                onChange={e => setUsername(e.target.value)}
                required
                autoComplete="username"
              />
            </div>

            {/* Password */}
            <div style={inputStyle}>
              <span style={{ fontSize: 14, opacity: 0.45 }}>🔒</span>
              <input
                style={inputFieldStyle}
                type="password"
                placeholder="Лозинка"
                value={password}
                onChange={e => setPassword(e.target.value)}
                required
                autoComplete="current-password"
              />
            </div>

            {/* Error */}
            {error && (
              <div style={{
                padding: '9px 13px',
                borderRadius: 'var(--radius-sm)',
                background: 'var(--error-dim)',
                border: '1px solid var(--error-border)',
                color: 'var(--error)',
                fontSize: 12,
                lineHeight: 1.5,
              }}>
                {error}
              </div>
            )}

            {/* Submit */}
            <button
              className="btn btn-primary"
              type="submit"
              disabled={loading}
              style={{ justifyContent: 'center', padding: '11px 18px', marginTop: 4, opacity: loading ? 0.7 : 1 }}
            >
              {loading ? '⏳ Се најавувате…' : '🌿 Најави се'}
            </button>
          </form>

          {/* Divider */}
          <div className="divider" style={{ margin: '22px 0' }} />

          {/* Register link */}
          <div style={{ textAlign: 'center', fontSize: 13, color: 'var(--text-muted)' }}>
            Немате сметка?{' '}
            <Link
              to="/register"
              style={{ color: 'var(--accent)', textDecoration: 'none', fontWeight: 600 }}
            >
              Креирајте сметка
            </Link>
          </div>
        </div>

        {/* Dev bypass — only rendered in Vite dev mode */}
        {import.meta.env.DEV && (
          <div style={{
            marginTop: 14,
            padding: '11px 14px',
            borderRadius: 'var(--radius-sm)',
            border: '1px dashed var(--glass-border)',
            background: 'var(--card)',
            textAlign: 'center',
          }}>
            <div style={{ fontSize: 11, color: 'var(--text-dim)', marginBottom: 8 }}>
              РАЗВОЕН РЕЖИМ — прво креирајте сметка, потоа најавете се
            </div>
            <Link
              to="/register"
              className="btn btn-ghost"
              style={{ width: '100%', justifyContent: 'center', fontSize: 12 }}
            >
              📝 Креирај тест сметка
            </Link>
          </div>
        )}

        {/* Footer note */}
        <div style={{ textAlign: 'center', marginTop: 18, fontSize: 11, color: 'var(--text-dim)' }}>
          GreenLens ВИ · Платформа за откривање болести кај растенија
        </div>
      </div>
    </div>
  );
}
