import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { register } from '../api/auth';
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

export default function Register() {
  const navigate = useNavigate();
  const [username, setUsername] = useState('');
  const [email, setEmail]       = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading]   = useState(false);
  const [error, setError]       = useState('');

  async function handleSubmit(e) {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await register(username, email, password);
      navigate('/', { replace: true });
    } catch (err) {
      setError(getApiErrorMessage(err, 'Регистрацијата не успеа. Обидете се повторно.', ['username', 'email', 'password']));
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
              Креирајте <span>сметка</span>
            </div>
            <div className="page-sub">Приклучете се на GreenLens како агроном</div>
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

            {/* Email */}
            <div style={inputStyle}>
              <span style={{ fontSize: 14, opacity: 0.45 }}>✉</span>
              <input
                style={inputFieldStyle}
                type="email"
                placeholder="Е-пошта"
                value={email}
                onChange={e => setEmail(e.target.value)}
                required
                autoComplete="email"
              />
            </div>

            {/* Password */}
            <div style={inputStyle}>
              <span style={{ fontSize: 14, opacity: 0.45 }}>🔒</span>
              <input
                style={inputFieldStyle}
                type="password"
                placeholder="Лозинка (мин. 8 знаци)"
                value={password}
                onChange={e => setPassword(e.target.value)}
                required
                minLength={8}
                autoComplete="new-password"
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
              {loading ? '⏳ Се креира сметка…' : '🌿 Креирај сметка'}
            </button>
          </form>

          {/* Divider */}
          <div className="divider" style={{ margin: '22px 0' }} />

          <div style={{ textAlign: 'center', fontSize: 13, color: 'var(--text-muted)' }}>
            Веќе имате сметка?{' '}
            <Link
              to="/login"
              style={{ color: 'var(--accent)', textDecoration: 'none', fontWeight: 600 }}
            >
              Најавете се
            </Link>
          </div>
        </div>

        <div style={{ textAlign: 'center', marginTop: 18, fontSize: 11, color: 'var(--text-dim)' }}>
          GreenLens ВИ · Платформа за откривање болести кај растенија
        </div>
      </div>
    </div>
  );
}
