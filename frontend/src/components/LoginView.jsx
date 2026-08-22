import React, { useState } from 'react';
import { Bot, Shield, User, Key, AlertCircle, ArrowRight, ShieldCheck, CheckCircle2, UserCheck, Eye, Cpu } from 'lucide-react';

export default function LoginView({ onLoginSuccess }) {
  const [identifier, setIdentifier] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [selectedRole, setSelectedRole] = useState(null);
  const [error, setError] = useState('');

  const demoAccounts = [
    {
      role: 'ADMIN',
      title: 'System Administrator',
      username: 'admin',
      email: 'admin@invoicemind.ai',
      badgeClass: 'badge-danger',
      description: 'Full portal access, database seeding, audit controls, and RBAC management.',
      icon: ShieldCheck,
      color: '#f43f5e'
    },
    {
      role: 'AP_MANAGER',
      title: 'Accounts Payable Manager',
      username: 'ap_manager',
      email: 'manager@invoicemind.ai',
      badgeClass: 'badge-info',
      description: 'Process uploads, oversee verification pipeline, review tasks, manage vendors & POs.',
      icon: UserCheck,
      color: '#38bdf8'
    },
    {
      role: 'REVIEWER',
      title: 'Senior AP Reviewer',
      username: 'reviewer',
      email: 'reviewer@invoicemind.ai',
      badgeClass: 'badge-warning',
      description: 'Inspect PO mismatches, approve/reject review tasks with mandatory audit notes.',
      icon: Shield,
      color: '#fbbf24'
    },
    {
      role: 'VIEWER',
      title: 'Auditor Viewer',
      username: 'viewer',
      email: 'viewer@invoicemind.ai',
      badgeClass: 'badge-secondary',
      description: 'Read-only access to dashboard, invoices, vendors, and POs (no write permissions).',
      icon: Eye,
      color: '#94a3b8'
    }
  ];

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

  const handleQuickLogin = async (account) => {
    setSelectedRole(account.role);
    setIdentifier(account.username);
    setPassword('Admin@123');
    setLoading(true);
    setError('');

    try {
      const res = await fetch('/api/v1/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username_or_email: account.username, password: 'Admin@123' })
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || 'Demo authentication failed.');
      }

      onLoginSuccess(data.access_token, data.user);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
      setSelectedRole(null);
    }
  };

  return (
    <div style={{ maxWidth: '1100px', margin: '20px auto', padding: '0 16px' }}>
      
      {/* Header Banner */}
      <div style={{ textAlign: 'center', marginBottom: '36px' }}>
        <div style={{
          width: '64px',
          height: '64px',
          borderRadius: '20px',
          background: 'linear-gradient(135deg, #6366f1 0%, #06b6d4 100%)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          margin: '0 auto 16px',
          boxShadow: '0 0 25px rgba(99, 102, 241, 0.5)'
        }}>
          <Bot size={36} color="#ffffff" />
        </div>
        <h1 style={{ fontSize: '1.8rem', fontWeight: 800, margin: 0, color: '#f8fafc', letterSpacing: '-0.02em' }}>
          INVOICE MIND <span style={{ color: '#6366f1' }}>AI</span> PORTAL
        </h1>
        <p style={{ fontSize: '0.9rem', color: '#94a3b8', marginTop: '6px' }}>
          Enterprise Accounts Payable & Agentic Verification System
        </p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(420px, 1fr))', gap: '32px', alignItems: 'start' }}>
        
        {/* LEFT COLUMN: 1-Click Role Login Cards */}
        <div>
          <h2 style={{ fontSize: '1.05rem', fontWeight: 700, color: '#f8fafc', marginBottom: '6px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <ShieldCheck size={20} color="#818cf8" /> Select Portal Role for 1-Click Sign In
          </h2>
          <p style={{ fontSize: '0.8rem', color: '#94a3b8', marginBottom: '16px' }}>
            Choose a seeded role account to test permissions and verification workflows
          </p>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
            {demoAccounts.map((account) => {
              const IconComp = account.icon;
              const isSelected = selectedRole === account.role;
              return (
                <div
                  key={account.role}
                  className="glass-panel"
                  style={{
                    padding: '18px 20px',
                    borderRadius: '14px',
                    border: isSelected ? `2px solid ${account.color}` : '1px solid rgba(255, 255, 255, 0.08)',
                    background: isSelected ? 'rgba(99, 102, 241, 0.12)' : 'rgba(255, 255, 255, 0.02)',
                    transition: 'all 0.2s ease',
                    cursor: 'pointer'
                  }}
                  className="table-row-hover"
                  onClick={() => handleQuickLogin(account)}
                >
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                      <div style={{ width: '34px', height: '34px', borderRadius: '10px', background: `${account.color}20`, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                        <IconComp size={18} color={account.color} />
                      </div>
                      <div>
                        <h3 style={{ fontSize: '0.95rem', fontWeight: 700, color: '#f8fafc', margin: 0 }}>
                          {account.title}
                        </h3>
                        <span style={{ fontSize: '0.75rem', color: '#64748b' }}>{account.email}</span>
                      </div>
                    </div>

                    <span className={`badge ${account.badgeClass}`} style={{ fontSize: '0.7rem' }}>
                      {account.role}
                    </span>
                  </div>

                  <p style={{ fontSize: '0.8rem', color: '#94a3b8', margin: '0 0 12px 0', lineHeight: 1.4 }}>
                    {account.description}
                  </p>

                  <button
                    type="button"
                    className="btn-primary"
                    disabled={loading}
                    style={{
                      width: '100%',
                      padding: '8px',
                      fontSize: '0.8rem',
                      justifyContent: 'center',
                      background: account.color,
                      borderColor: account.color
                    }}
                    onClick={(e) => {
                      e.stopPropagation();
                      handleQuickLogin(account);
                    }}
                  >
                    {isSelected ? 'Signing in...' : `Sign In as ${account.role}`} <ArrowRight size={14} />
                  </button>
                </div>
              );
            })}
          </div>
        </div>

        {/* RIGHT COLUMN: Manual Form Sign In Card */}
        <div className="glass-panel" style={{ padding: '32px', borderRadius: '16px' }}>
          <h2 style={{ fontSize: '1.05rem', fontWeight: 700, color: '#f8fafc', marginBottom: '6px' }}>
            Manual Credentials Login
          </h2>
          <p style={{ fontSize: '0.8rem', color: '#94a3b8', marginBottom: '24px' }}>
            Sign in with explicit user account credentials
          </p>

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

          <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '18px' }}>
            <div>
              <label style={{ display: 'block', fontSize: '0.78rem', fontWeight: 600, color: '#94a3b8', marginBottom: '6px' }}>
                USERNAME OR EMAIL ADDRESS
              </label>
              <div style={{ position: 'relative' }}>
                <User size={18} color="#64748b" style={{ position: 'absolute', left: '14px', top: '50%', transform: 'translateY(-50%)' }} />
                <input
                  type="text"
                  className="input-field"
                  style={{ paddingLeft: '42px', width: '100%', fontSize: '0.9rem' }}
                  placeholder="e.g. admin or reviewer@invoicemind.ai"
                  value={identifier}
                  onChange={(e) => setIdentifier(e.target.value)}
                />
              </div>
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '0.78rem', fontWeight: 600, color: '#94a3b8', marginBottom: '6px' }}>
                ACCOUNT PASSWORD
              </label>
              <div style={{ position: 'relative' }}>
                <Key size={18} color="#64748b" style={{ position: 'absolute', left: '14px', top: '50%', transform: 'translateY(-50%)' }} />
                <input
                  type="password"
                  className="input-field"
                  style={{ paddingLeft: '42px', width: '100%', fontSize: '0.9rem' }}
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                />
              </div>
            </div>

            <div style={{ background: 'rgba(255,255,255,0.03)', padding: '12px 14px', borderRadius: '10px', fontSize: '0.78rem', color: '#64748b', border: '1px solid rgba(255,255,255,0.05)' }}>
              🔑 Default seed password for all roles: <strong style={{ color: '#818cf8' }}>Admin@123</strong>
            </div>

            <button
              type="submit"
              className="btn-primary"
              disabled={loading}
              style={{ width: '100%', padding: '12px', fontSize: '0.95rem', justifyContent: 'center', marginTop: '4px' }}
            >
              {loading ? 'Authenticating...' : (
                <>Sign In to Accounts Payable Portal <ArrowRight size={16} /></>
              )}
            </button>
          </form>
        </div>

      </div>
    </div>
  );
}
