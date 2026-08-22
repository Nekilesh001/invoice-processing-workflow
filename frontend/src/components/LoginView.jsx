import React, { useState } from 'react';
import { Bot, Lock, User, Key, AlertCircle, ArrowRight, ShieldCheck } from 'lucide-react';

export default function LoginView({ onLoginSuccess }) {
  const [identifier, setIdentifier] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!identifier || !password) {
      setError('Please enter both username/email and password.');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const res = await fetch('/api/v1/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username_or_email: identifier, password: password })
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || 'Authentication failed.');
      }

      onLoginSuccess(data.access_token, data.user);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleDemoLogin = async (username, demoPassword = 'Admin@123') => {
    setIdentifier(username);
    setPassword(demoPassword);
    setLoading(true);
    setError('');

    try {
      const res = await fetch('/api/v1/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username_or_email: username, password: demoPassword })
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || 'Demo login failed.');
      }

      onLoginSuccess(data.access_token, data.user);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ minHeight: '80vh', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '24px' }}>
      <div className="glass-panel" style={{ width: '100%', maxWidth: '440px', padding: '36px 32px' }}>
        
        {/* Header Logo */}
        <div style={{ textAlign: 'center', marginBottom: '28px' }}>
          <div style={{
            width: '54px',
            height: '54px',
            borderRadius: '16px',
            background: 'linear-gradient(135deg, #6366f1 0%, #06b6d4 100%)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            margin: '0 auto 16px',
            boxShadow: '0 0 20px rgba(99, 102, 241, 0.4)'
          }}>
            <Bot size={32} color="#ffffff" />
          </div>
          <h2 style={{ fontSize: '1.4rem', fontWeight: 800, margin: 0, color: '#f8fafc' }}>
            INVOICE MIND <span style={{ color: '#6366f1' }}>AI</span>
          </h2>
          <p style={{ fontSize: '0.82rem', color: '#94a3b8', marginTop: '4px' }}>
            Enterprise Accounts Payable Portal Login
          </p>
        </div>

        {/* Error Alert */}
        {error && (
          <div style={{
            padding: '12px 16px',
            borderRadius: '10px',
            background: 'rgba(239, 68, 68, 0.1)',
            border: '1px solid rgba(239, 68, 68, 0.3)',
            color: '#f87171',
            fontSize: '0.85rem',
            marginBottom: '20px',
            display: 'flex',
            alignItems: 'center',
            gap: '8px'
          }}>
            <AlertCircle size={16} />
            <span>{error}</span>
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div>
            <label style={{ display: 'block', fontSize: '0.78rem', fontWeight: 600, color: '#94a3b8', marginBottom: '6px' }}>
              USERNAME OR EMAIL
            </label>
            <div style={{ position: 'relative' }}>
              <User size={18} color="#64748b" style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)' }} />
              <input
                type="text"
                className="input-field"
                style={{ paddingLeft: '40px', width: '100%', fontSize: '0.9rem' }}
                placeholder="e.g. admin or reviewer"
                value={identifier}
                onChange={(e) => setIdentifier(e.target.value)}
              />
            </div>
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '0.78rem', fontWeight: 600, color: '#94a3b8', marginBottom: '6px' }}>
              PASSWORD
            </label>
            <div style={{ position: 'relative' }}>
              <Key size={18} color="#64748b" style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)' }} />
              <input
                type="password"
                className="input-field"
                style={{ paddingLeft: '40px', width: '100%', fontSize: '0.9rem' }}
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            </div>
          </div>

          <button
            type="submit"
            className="btn-primary"
            disabled={loading}
            style={{ width: '100%', padding: '12px', fontSize: '0.95rem', justifyContent: 'center', marginTop: '8px' }}
          >
            {loading ? 'Authenticating...' : (
              <>Sign In to Portal <ArrowRight size={16} /></>
            )}
          </button>
        </form>

        {/* Quick Demo Login Preset Buttons */}
        <div style={{ marginTop: '28px', paddingTop: '20px', borderTop: '1px solid rgba(255, 255, 255, 0.08)' }}>
          <p style={{ fontSize: '0.75rem', fontWeight: 700, color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '10px', textAlign: 'center' }}>
            Quick Demo Login Accounts (Pass: Admin@123)
          </p>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
            <button
              type="button"
              className="btn-secondary"
              style={{ fontSize: '0.75rem', padding: '6px 8px', justifyContent: 'center' }}
              onClick={() => handleDemoLogin('admin')}
            >
              <ShieldCheck size={12} color="#6366f1" /> Admin
            </button>

            <button
              type="button"
              className="btn-secondary"
              style={{ fontSize: '0.75rem', padding: '6px 8px', justifyContent: 'center' }}
              onClick={() => handleDemoLogin('ap_manager')}
            >
              <ShieldCheck size={12} color="#06b6d4" /> AP Manager
            </button>

            <button
              type="button"
              className="btn-secondary"
              style={{ fontSize: '0.75rem', padding: '6px 8px', justifyContent: 'center' }}
              onClick={() => handleDemoLogin('reviewer')}
            >
              <ShieldCheck size={12} color="#fbbf24" /> Reviewer
            </button>

            <button
              type="button"
              className="btn-secondary"
              style={{ fontSize: '0.75rem', padding: '6px 8px', justifyContent: 'center' }}
              onClick={() => handleDemoLogin('viewer')}
            >
              <ShieldCheck size={12} color="#94a3b8" /> Viewer
            </button>
          </div>
        </div>

      </div>
    </div>
  );
}
