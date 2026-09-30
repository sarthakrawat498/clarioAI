import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { Shield, Lock, Mail, User, ArrowRight, Sparkles } from 'lucide-react';

export const Auth = () => {
  const { login, register } = useAuth();
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSubmitting(true);

    try {
      if (isLogin) {
        await login(email, password);
      } else {
        if (!fullName || fullName.trim().length < 2) {
          throw new Error('Full Name must be at least 2 characters long.');
        }
        if (!password || password.length < 6) {
          throw new Error('Password must be at least 6 characters long.');
        }
        await register(fullName, email, password);
      }
    } catch (err) {
      console.error('Auth error:', err);
      
      // Better error message detection
      let detail = 'Authentication failed. Please check credentials.';
      
      if (err.response?.data?.detail) {
        detail = err.response.data.detail;
      } else if (err.message === 'Network Error' || err.code === 'ERR_NETWORK') {
        detail = 'Network error: Cannot reach the server. Is the backend running at http://127.0.0.1:8001?';
      } else if (err.message) {
        detail = err.message;
      }
      
      setError(detail);
    } finally {
      setSubmitting(false);
    }
  };

  const fillDemoUser = async () => {
    setEmail('demo@clario.ai');
    setPassword('demo123456');
    setError('');
  };

  return (
    <div className="auth-wrapper">
      <div className="auth-card">
        <div style={{ textAlign: 'center', marginBottom: '24px' }}>
          <div className="brand-icon" style={{ margin: '0 auto 16px', width: '56px', height: '56px', fontSize: '28px' }}>
            🛡️
          </div>
          <h2 style={{ fontSize: '1.5rem', fontWeight: 800 }}>Clario AI</h2>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.88rem', marginTop: '4px' }}>
            Production-Grade Multi-Agent AI Health Insurance Platform
          </p>
        </div>

        <div className="tab-group">
          <button
            className={`tab-btn ${isLogin ? 'active' : ''}`}
            onClick={() => { setIsLogin(true); setError(''); }}
            type="button"
          >
            Sign In
          </button>
          <button
            className={`tab-btn ${!isLogin ? 'active' : ''}`}
            onClick={() => { setIsLogin(false); setError(''); }}
            type="button"
          >
            Register
          </button>
        </div>

        {error && (
          <div
            style={{
              padding: '10px 14px',
              borderRadius: 'var(--radius-md)',
              background: 'rgba(244, 63, 94, 0.15)',
              border: '1px solid rgba(244, 63, 94, 0.4)',
              color: '#fb7185',
              fontSize: '0.85rem',
              marginBottom: '16px',
            }}
          >
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          {!isLogin && (
            <div className="form-group">
              <label className="form-label">Full Name</label>
              <div style={{ position: 'relative' }}>
                <User size={18} style={{ position: 'absolute', left: '14px', top: '14px', color: 'var(--text-muted)' }} />
                <input
                  type="text"
                  className="form-input"
                  style={{ paddingLeft: '42px' }}
                  placeholder="John Doe"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  required={!isLogin}
                />
              </div>
            </div>
          )}

          <div className="form-group">
            <label className="form-label">Email Address</label>
            <div style={{ position: 'relative' }}>
              <Mail size={18} style={{ position: 'absolute', left: '14px', top: '14px', color: 'var(--text-muted)' }} />
              <input
                type="email"
                className="form-input"
                style={{ paddingLeft: '42px' }}
                placeholder="name@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>
          </div>

          <div className="form-group">
            <label className="form-label">Password</label>
            <div style={{ position: 'relative' }}>
              <Lock size={18} style={{ position: 'absolute', left: '14px', top: '14px', color: 'var(--text-muted)' }} />
              <input
                type="password"
                className="form-input"
                style={{ paddingLeft: '42px' }}
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                minLength={isLogin ? 1 : 6}
                required
              />
            </div>
            {!isLogin && (
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '4px' }}>
                Must be at least 6 characters long.
              </div>
            )}
          </div>

          <button
            type="submit"
            className="btn-primary"
            style={{ width: '100%', marginTop: '12px', padding: '12px' }}
            disabled={submitting}
          >
            {submitting ? 'Please wait...' : (isLogin ? 'Sign In' : 'Create Account')}
            <ArrowRight size={18} />
          </button>
        </form>

        <div style={{ marginTop: '20px', paddingTop: '16px', borderTop: '1px solid var(--border-color)', textAlign: 'center' }}>
          <button
            type="button"
            className="btn-secondary"
            onClick={fillDemoUser}
            style={{ width: '100%', fontSize: '0.82rem', padding: '8px 12px' }}
          >
            <Sparkles size={14} style={{ color: 'var(--cyan)' }} /> Fill Quick Demo Account
          </button>
        </div>
      </div>
    </div>
  );
};
