import { useEffect, useMemo, useState } from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { getMe, logout } from '../api/auth';

const navItems = [
  { to: '/',        end: true,  icon: '⊞', label: 'Контролна табла' },
  { to: '/scan',               icon: '⊙', label: 'Скенирај растение' },
  { to: '/results',            icon: '◈', label: 'Резултати',  dot: true },
  { to: '/history',            icon: '◷', label: 'Историја' },
];

export default function Sidebar() {
  const navigate = useNavigate();
  const [user, setUser] = useState(null);

  useEffect(() => {
    getMe().then(setUser).catch(() => {});
  }, []);

  const initials = useMemo(() => {
    const source = user?.first_name || user?.username || user?.email || 'U';
    return source.slice(0, 2).toUpperCase();
  }, [user]);

  function handleLogout() {
    logout();
    navigate('/login', { replace: true });
  }

  return (
    <aside className="sidebar">
      <div className="logo">
          <div className="logo-icon">🌿</div>
        <div>
          <div className="logo-text">GreenLens</div>
          <div className="logo-sub">ВИ · Анализа на растенија</div>
        </div>
      </div>

      <nav>
        {navItems.map(({ to, end, icon, label, dot }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            className={({ isActive }) => `nav-item${isActive ? ' active' : ''}`}
          >
            <span className="nav-icon">{icon}</span>
            <span className="nav-label">{label}</span>
            {dot && <span className="notif-dot" />}
          </NavLink>
        ))}
      </nav>

      <div className="sidebar-footer">
        <div className="user-pill">
          <div className="avatar">{initials}</div>
          <div>
            <div className="user-name">{user?.username || 'Најавен корисник'}</div>
            <div className="user-role">{user?.email || 'GreenLens корисник'}</div>
          </div>
        </div>
        <button className="logout-btn" type="button" onClick={handleLogout}>
          Одјави се
        </button>
      </div>
    </aside>
  );
}
