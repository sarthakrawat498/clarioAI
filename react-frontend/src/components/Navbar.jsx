import React from 'react';
import { useAuth } from '../context/AuthContext';
import { LogOut, Activity, User, ShieldCheck } from 'lucide-react';

export const Navbar = ({ activeTabTitle }) => {
  const { user, logout } = useAuth();

  const getInitials = (name) => {
    if (!name) return 'U';
    return name.split(' ').map(n => n[0]).join('').toUpperCase().substring(0, 2);
  };

  return (
    <header className="navbar">
      <div className="navbar-brand">
        <div className="brand-icon">🛡️</div>
        <div>
          <div className="brand-title">Clario AI</div>
          <div className="brand-subtitle">Health Insurance Multi-Agent AI System</div>
        </div>
      </div>

      <div className="nav-actions">
        <div className="system-badge">
          <span className="pulse-dot"></span>
          <span>LangGraph Multi-Agent RAG Online</span>
        </div>

        {user && (
          <div className="user-pill">
            <div className="user-avatar">{getInitials(user.full_name)}</div>
            <span>{user.full_name || user.email}</span>
          </div>
        )}

        <button className="logout-btn" onClick={logout} title="Sign Out">
          <LogOut size={16} />
          <span>Exit</span>
        </button>
      </div>
    </header>
  );
};
