import { NavLink } from 'react-router-dom';

const navItems = [
  { to: '/',        end: true,  icon: '⊞', label: 'Dashboard' },
  { to: '/scan',               icon: '⊙', label: 'Scan Plant' },
  { to: '/results',            icon: '◈', label: 'Results',  dot: true },
  { to: '/history',            icon: '◷', label: 'History' },
];

export default function Sidebar() {
  return (
    <aside className="sidebar">
      <div className="logo">
        <div className="logo-icon">🌿</div>
        <div>
          <div className="logo-text">GreenLens</div>
          <div className="logo-sub">AI · Plant Analysis</div>
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
          <div className="avatar">AG</div>
          <div>
            <div className="user-name">Agronomist</div>
            <div className="user-role">Field Expert</div>
          </div>
        </div>
      </div>
    </aside>
  );
}
