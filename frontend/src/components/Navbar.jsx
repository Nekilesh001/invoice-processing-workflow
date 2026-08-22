import React from 'react';
import { Bot, FileText, CheckCircle2, ShieldAlert, Cpu, Database, Building2, ShoppingBag, LayoutDashboard, User, LogOut } from 'lucide-react';

export default function Navbar({ activeTab, setActiveTab, pendingReviewCount, apiOnline, user, onLogout }) {
  return (
    <header className="glass-panel" style={{ margin: '16px 24px', padding: '16px 28px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '16px' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
        <div style={{
          width: '42px',
          height: '42px',
          borderRadius: '12px',
          background: 'linear-gradient(135deg, #6366f1 0%, #06b6d4 100%)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          boxShadow: '0 0 15px rgba(99, 102, 241, 0.4)'
        }}>
          <Bot size={24} color="#ffffff" />
        </div>
        <div>
          <h1 style={{ fontSize: '1.25rem', fontWeight: 800, letterSpacing: '-0.02em', background: 'linear-gradient(90deg, #ffffff 0%, #cbd5e1 100%)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
            INVOICE MIND <span style={{ color: '#6366f1', WebkitTextFillColor: '#6366f1' }}>AI</span>
          </h1>
          <p style={{ fontSize: '0.75rem', color: '#94a3b8', display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span>DeepLearning.AI Agentic AI Architecture</span>
          </p>
        </div>
      </div>

      <nav style={{ display: 'flex', alignItems: 'center', gap: '6px', background: 'rgba(255, 255, 255, 0.03)', padding: '4px', borderRadius: '12px', border: '1px solid rgba(255, 255, 255, 0.05)' }}>
        <button
          className={activeTab === 'dashboard' ? 'btn-primary' : 'btn-secondary'}
          style={{ padding: '8px 14px', fontSize: '0.85rem', border: 'none' }}
          onClick={() => setActiveTab('dashboard')}
        >
          <LayoutDashboard size={16} /> Dashboard
        </button>
        <button
          className={activeTab === 'upload' ? 'btn-primary' : 'btn-secondary'}
          style={{ padding: '8px 14px', fontSize: '0.85rem', border: 'none' }}
          onClick={() => setActiveTab('upload')}
        >
          <FileText size={16} /> Process Upload
        </button>
        <button
          className={activeTab === 'invoices' ? 'btn-primary' : 'btn-secondary'}
          style={{ padding: '8px 14px', fontSize: '0.85rem', border: 'none' }}
          onClick={() => setActiveTab('invoices')}
        >
          <Database size={16} /> Invoices
        </button>
        <button
          className={activeTab === 'vendors' ? 'btn-primary' : 'btn-secondary'}
          style={{ padding: '8px 14px', fontSize: '0.85rem', border: 'none' }}
          onClick={() => setActiveTab('vendors')}
        >
          <Building2 size={16} /> Vendors
        </button>
        <button
          className={activeTab === 'purchase_orders' ? 'btn-primary' : 'btn-secondary'}
          style={{ padding: '8px 14px', fontSize: '0.85rem', border: 'none' }}
          onClick={() => setActiveTab('purchase_orders')}
        >
          <ShoppingBag size={16} /> Purchase Orders
        </button>
        <button
          className={activeTab === 'trace' ? 'btn-primary' : 'btn-secondary'}
          style={{ padding: '8px 14px', fontSize: '0.85rem', border: 'none' }}
          onClick={() => setActiveTab('trace')}
        >
          <Cpu size={16} /> Agent Trace
        </button>
        <button
          className={activeTab === 'reviews' ? 'btn-primary' : 'btn-secondary'}
          style={{ padding: '8px 14px', fontSize: '0.85rem', border: 'none', position: 'relative' }}
          onClick={() => setActiveTab('reviews')}
        >
          <ShieldAlert size={16} /> Review Queue
          {pendingReviewCount > 0 && (
            <span style={{
              position: 'absolute',
              top: '-4px',
              right: '-4px',
              background: '#f43f5e',
              color: '#ffffff',
              borderRadius: '9999px',
              padding: '2px 6px',
              fontSize: '0.65rem',
              fontWeight: 700
            }}>
              {pendingReviewCount}
            </span>
          )}
        </button>
      </nav>

      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
        {user && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', background: 'rgba(255, 255, 255, 0.05)', padding: '6px 12px', borderRadius: '10px', border: '1px solid rgba(255, 255, 255, 0.1)' }}>
            <User size={14} color="#818cf8" />
            <span style={{ fontSize: '0.8rem', fontWeight: 600, color: '#f8fafc' }}>
              {user.full_name || user.username}
            </span>
            <span className={user.role === 'ADMIN' ? 'badge badge-danger' : user.role === 'AP_MANAGER' ? 'badge badge-info' : user.role === 'REVIEWER' ? 'badge badge-warning' : 'badge badge-secondary'} style={{ fontSize: '0.65rem', padding: '2px 6px' }}>
              {user.role}
            </span>
          </div>
        )}
        <div className={apiOnline ? 'badge badge-success' : 'badge badge-danger'}>
          <CheckCircle2 size={12} /> {apiOnline ? 'Online' : 'Offline'}
        </div>
        {user && onLogout && (
          <button
            className="btn-secondary"
            title="Sign out of portal"
            style={{ padding: '6px 10px', fontSize: '0.8rem' }}
            onClick={onLogout}
          >
            <LogOut size={14} />
          </button>
        )}
      </div>
    </header>
  );
}
