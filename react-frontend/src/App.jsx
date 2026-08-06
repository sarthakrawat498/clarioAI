import React from 'react';
import { AuthProvider, useAuth } from './context/AuthContext';
import { Auth } from './components/Auth';
import { SinglePageChatbot } from './components/SinglePageChatbot';

const MainApp = () => {
  const { isAuthenticated, loading } = useAuth();

  if (loading) {
    return (
      <div className="auth-wrapper">
        <div className="auth-card" style={{ textAlign: 'center' }}>
          <div className="brand-icon" style={{ margin: '0 auto 16px', width: '56px', height: '56px' }}>🛡️</div>
          <h3 style={{ fontSize: '1.2rem', fontWeight: 800 }}>Initializing AI Health Assistant...</h3>
          <p style={{ color: 'var(--text-muted)', marginTop: '8px', fontSize: '0.85rem' }}>Authenticating user session & vector database context</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Auth />;
  }

  return <SinglePageChatbot />;
};

export default function App() {
  return (
    <AuthProvider>
      <MainApp />
    </AuthProvider>
  );
}
