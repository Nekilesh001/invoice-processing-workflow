import React, { useState, useEffect } from 'react';
import { Database, Search, Eye, RefreshCw, FileText, CheckCircle2, ShieldAlert, XCircle, LayoutGrid, List, Building2, ShoppingBag, DollarSign, Calendar } from 'lucide-react';
import { apiFetch } from '../api';

export default function InvoicesTable({ onSelectInvoice }) {
  const [invoices, setInvoices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [viewMode, setViewMode] = useState('cards'); // 'cards' or 'table'

  const fetchInvoices = async () => {
    setLoading(true);
    try {
      const res = await apiFetch('/api/v1/invoices');
      if (res.ok) {
        const data = await res.json();
        setInvoices(data);
      }
    } catch (e) {
      console.error('Failed to fetch invoices', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchInvoices();
  }, []);

  const filteredInvoices = invoices.filter(inv => {
    const matchesSearch =
      (inv.invoice_number || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
      (inv.vendor_name || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
      (inv.po_number || '').toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = statusFilter === 'ALL' || inv.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      
      {/* Header Panel */}
      <div className="glass-panel" style={{ padding: '24px 32px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
          <div style={{ width: '42px', height: '42px', borderRadius: '12px', background: 'rgba(6, 182, 212, 0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Database size={24} color="#22d3ee" />
          </div>
          <div>
            <h2 style={{ fontSize: '1.3rem', fontWeight: 800, margin: 0, color: '#f8fafc' }}>
              MySQL Billed Invoices Repository
            </h2>
            <p style={{ fontSize: '0.8rem', color: '#94a3b8', marginTop: '2px' }}>
              Relational records stored in `invoice_db` database
            </p>
          </div>
        </div>

        {/* Action Controls & View Mode Toggle */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          {/* Card / Table View Toggle */}
          <div style={{ display: 'flex', background: 'rgba(255, 255, 255, 0.05)', padding: '3px', borderRadius: '10px', border: '1px solid rgba(255, 255, 255, 0.1)' }}>
            <button
              className={viewMode === 'cards' ? 'btn-primary' : 'btn-secondary'}
              style={{ padding: '6px 12px', fontSize: '0.78rem', border: 'none' }}
              onClick={() => setViewMode('cards')}
            >
              <LayoutGrid size={14} /> Cards
            </button>
            <button
              className={viewMode === 'table' ? 'btn-primary' : 'btn-secondary'}
              style={{ padding: '6px 12px', fontSize: '0.78rem', border: 'none' }}
              onClick={() => setViewMode('table')}
            >
              <List size={14} /> Table
            </button>
          </div>

          <button className="btn-secondary" style={{ padding: '8px 14px', fontSize: '0.8rem', display: 'flex', alignItems: 'center', gap: '6px' }} onClick={fetchInvoices}>
            <RefreshCw size={14} className={loading ? 'animate-spin' : ''} /> Refresh Data
          </button>
        </div>
      </div>

      {/* Search & Status Filter Bar */}
      <div className="glass-panel" style={{ padding: '16px 24px', display: 'flex', gap: '16px', flexWrap: 'wrap' }}>
        <div style={{ flex: 1, position: 'relative', minWidth: '280px' }}>
          <Search size={18} color="#64748b" style={{ position: 'absolute', left: '14px', top: '50%', transform: 'translateY(-50%)' }} />
          <input
            type="text"
            placeholder="Search by invoice number, vendor, or PO number..."
            value={searchTerm}
            onChange={e => setSearchTerm(e.target.value)}
            style={{
              width: '100%',
              background: 'rgba(255, 255, 255, 0.03)',
              border: '1px solid rgba(255, 255, 255, 0.1)',
              borderRadius: '10px',
              padding: '10px 14px 10px 42px',
              color: '#ffffff',
              fontSize: '0.88rem',
              outline: 'none'
            }}
          />
        </div>

        <select
          value={statusFilter}
          onChange={e => setStatusFilter(e.target.value)}
          style={{
            background: 'rgba(255, 255, 255, 0.05)',
            border: '1px solid rgba(255, 255, 255, 0.1)',
            borderRadius: '10px',
            padding: '10px 16px',
            color: '#ffffff',
            fontSize: '0.88rem',
            outline: 'none',
            cursor: 'pointer'
          }}
        >
          <option value="ALL" style={{ background: '#0f172a' }}>All Statuses</option>
          <option value="APPROVED" style={{ background: '#0f172a' }}>Approved</option>
          <option value="NEEDS_REVIEW" style={{ background: '#0f172a' }}>Needs Review</option>
          <option value="REJECTED" style={{ background: '#0f172a' }}>Rejected</option>
        </select>
      </div>

      {/* Loading State */}
      {loading && invoices.length === 0 && (
        <div className="glass-panel" style={{ padding: '48px', textAlign: 'center' }}>
          <div className="animate-spin" style={{ width: '32px', height: '32px', border: '3px solid rgba(99,102,241,0.2)', borderTopColor: '#6366f1', borderRadius: '50%', margin: '0 auto 12px' }} />
          <p style={{ color: '#94a3b8' }}>Loading invoice records from MySQL database...</p>
        </div>
      )}

      {/* Empty State */}
      {filteredInvoices.length === 0 && !loading && (
        <div className="glass-panel" style={{ padding: '48px', textAlign: 'center' }}>
          <FileText size={36} color="#64748b" style={{ marginBottom: '12px' }} />
          <p style={{ color: '#94a3b8', fontSize: '0.95rem' }}>No processed invoices match your filter criteria.</p>
        </div>
      )}

      {/* VIEW MODE 1: EXECUTIVE CARD GRID */}
      {viewMode === 'cards' && filteredInvoices.length > 0 && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(340px, 1fr))', gap: '20px' }}>
          {filteredInvoices.map((inv) => (
            <div
              key={inv.id}
              className="glass-panel table-row-hover"
              style={{
                padding: '22px',
                borderRadius: '16px',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'space-between',
                gap: '16px',
                cursor: 'pointer',
                border: '1px solid rgba(255, 255, 255, 0.08)'
              }}
              onClick={() => onSelectInvoice && onSelectInvoice(inv.id)}
            >
              {/* Card Header: Invoice # & Status Badge */}
              <div>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
                  <span style={{ fontSize: '1rem', fontWeight: 800, color: '#38bdf8' }} className="font-mono">
                    {inv.invoice_number || `Invoice #${inv.id}`}
                  </span>
                  <span className={inv.status === 'APPROVED' ? 'badge badge-success' : inv.status === 'NEEDS_REVIEW' ? 'badge badge-warning' : 'badge badge-danger'}>
                    {inv.status === 'APPROVED' ? <CheckCircle2 size={12} /> : inv.status === 'NEEDS_REVIEW' ? <ShieldAlert size={12} /> : <XCircle size={12} />}
                    {inv.status}
                  </span>
                </div>

                {/* Vendor Name */}
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#e2e8f0', fontSize: '0.88rem', fontWeight: 600, marginBottom: '6px' }}>
                  <Building2 size={16} color="#94a3b8" />
                  <span>{inv.vendor_name || 'Unassigned Vendor'}</span>
                </div>

                {/* Purchase Order Badge */}
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#94a3b8', fontSize: '0.8rem' }}>
                  <ShoppingBag size={14} color="#818cf8" />
                  <span>PO Reference: <strong style={{ color: inv.po_number ? '#818cf8' : '#64748b' }}>{inv.po_number || 'None'}</strong></span>
                </div>
              </div>

              {/* Card Footer: Financial Total & Inspect Detail Action Button */}
              <div style={{ paddingTop: '14px', borderTop: '1px solid rgba(255, 255, 255, 0.06)', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <div>
                  <span style={{ fontSize: '0.72rem', color: '#94a3b8', display: 'block' }}>TOTAL AMOUNT</span>
                  <span style={{ fontSize: '1.35rem', fontWeight: 800, color: '#4ade80' }}>
                    ${inv.total_amount ? Number(inv.total_amount).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : '0.00'}
                  </span>
                </div>

                <button
                  className="btn-secondary"
                  style={{ padding: '8px 14px', fontSize: '0.8rem', background: 'rgba(99, 102, 241, 0.15)', borderColor: 'rgba(99, 102, 241, 0.3)', color: '#818cf8' }}
                  onClick={(e) => {
                    e.stopPropagation();
                    onSelectInvoice && onSelectInvoice(inv.id);
                  }}
                >
                  <Eye size={14} /> Verification Detail
                </button>
              </div>

            </div>
          ))}
        </div>
      )}

      {/* VIEW MODE 2: CLASSIC TABLE VIEW */}
      {viewMode === 'table' && filteredInvoices.length > 0 && (
        <div className="glass-panel" style={{ padding: '24px', overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.88rem' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.1)', color: '#94a3b8', fontSize: '0.75rem' }} className="font-mono">
                <th style={{ padding: '12px 16px' }}>ID</th>
                <th style={{ padding: '12px 16px' }}>INVOICE #</th>
                <th style={{ padding: '12px 16px' }}>VENDOR</th>
                <th style={{ padding: '12px 16px' }}>PO NUMBER</th>
                <th style={{ padding: '12px 16px' }}>TOTAL</th>
                <th style={{ padding: '12px 16px' }}>STATUS</th>
                <th style={{ padding: '12px 16px', textAlign: 'right' }}>ACTIONS</th>
              </tr>
            </thead>
            <tbody>
              {filteredInvoices.map((inv) => (
                <tr
                  key={inv.id}
                  style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.04)', cursor: 'pointer' }}
                  className="table-row-hover"
                  onClick={() => onSelectInvoice && onSelectInvoice(inv.id)}
                >
                  <td style={{ padding: '14px 16px', color: '#64748b' }}>{inv.id}</td>
                  <td style={{ padding: '14px 16px', fontWeight: 700, color: '#38bdf8' }} className="font-mono">{inv.invoice_number || `Invoice #${inv.id}`}</td>
                  <td style={{ padding: '14px 16px', color: '#e2e8f0' }}>{inv.vendor_name || 'Unassigned Vendor'}</td>
                  <td style={{ padding: '14px 16px', color: '#94a3b8' }}>{inv.po_number || 'NONE'}</td>
                  <td style={{ padding: '14px 16px', fontWeight: 800, color: '#4ade80' }}>
                    ${inv.total_amount ? Number(inv.total_amount).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : '0.00'}
                  </td>
                  <td style={{ padding: '14px 16px' }}>
                    <span className={inv.status === 'APPROVED' ? 'badge badge-success' : inv.status === 'NEEDS_REVIEW' ? 'badge badge-warning' : 'badge badge-danger'}>
                      {inv.status}
                    </span>
                  </td>
                  <td style={{ padding: '14px 16px', textAlign: 'right' }}>
                    <button
                      className="btn-secondary"
                      style={{ padding: '6px 12px', fontSize: '0.75rem' }}
                      onClick={(e) => {
                        e.stopPropagation();
                        onSelectInvoice && onSelectInvoice(inv.id);
                      }}
                    >
                      <Eye size={12} /> Verification Detail
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

    </div>
  );
}
