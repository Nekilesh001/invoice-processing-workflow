import React, { useState, useEffect } from 'react';
import { Database, Search, Eye, RefreshCw, FileText, CheckCircle, AlertTriangle } from 'lucide-react';

export default function InvoicesTable({ onSelectInvoice }) {
  const [invoices, setInvoices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [selectedInvoice, setSelectedInvoice] = useState(null);

  const fetchInvoices = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/v1/invoices');
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
      (inv.vendor_name || '').toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = statusFilter === 'ALL' || inv.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  return (
    <div className="glass-panel" style={{ padding: '32px' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '24px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{ width: '40px', height: '40px', borderRadius: '12px', background: 'rgba(6, 182, 212, 0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Database size={22} color="#22d3ee" />
          </div>
          <div>
            <h2 style={{ fontSize: '1.2rem', fontWeight: 700 }}>MySQL Processed Invoices</h2>
            <p style={{ fontSize: '0.8rem', color: '#94a3b8' }}>Live relational records stored in `invoice_db`</p>
          </div>
        </div>

        <button className="btn-secondary" style={{ padding: '8px 14px', fontSize: '0.8rem', display: 'flex', alignItems: 'center', gap: '6px' }} onClick={fetchInvoices}>
          <RefreshCw size={14} className={loading ? 'animate-spin' : ''} /> Refresh
        </button>
      </div>

      {/* Search & Filters */}
      <div style={{ display: 'flex', gap: '16px', marginBottom: '20px' }}>
        <div style={{ flex: 1, position: 'relative' }}>
          <Search size={18} color="#64748b" style={{ position: 'absolute', left: '14px', top: '50%', transform: 'translateY(-50%)' }} />
          <input
            type="text"
            placeholder="Search by invoice number or vendor..."
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

      {/* Table */}
      <div style={{ overflowX: 'auto' }}>
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
            {filteredInvoices.length === 0 && !loading && (
              <tr>
                <td colSpan="7" style={{ textAlign: 'center', padding: '40px', color: '#64748b' }}>
                  No processed invoices found in MySQL database.
                </td>
              </tr>
            )}
            {filteredInvoices.map((inv) => (
              <tr key={inv.id} style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.04)', transition: 'background 0.15s ease' }} className="table-row-hover">
                <td style={{ padding: '14px 16px' }} className="font-mono">{inv.id}</td>
                <td style={{ padding: '14px 16px', fontWeight: 600 }} className="font-mono">{inv.invoice_number}</td>
                <td style={{ padding: '14px 16px' }}>{inv.vendor_name || 'Unassigned'}</td>
                <td style={{ padding: '14px 16px', color: inv.po_number ? '#34d399' : '#64748b' }} className="font-mono">{inv.po_number || 'NONE'}</td>
                <td style={{ padding: '14px 16px', fontWeight: 700, color: '#818cf8' }}>${(inv.total_amount || 0).toFixed(2)}</td>
                <td style={{ padding: '14px 16px' }}>
                  <span className={inv.status === 'APPROVED' ? 'badge badge-success' : inv.status === 'NEEDS_REVIEW' ? 'badge badge-warning' : 'badge badge-danger'}>
                    {inv.status}
                  </span>
                </td>
                <td style={{ padding: '14px 16px', textAlign: 'right' }}>
                  <button
                    className="btn-secondary"
                    style={{ padding: '6px 12px', fontSize: '0.75rem', display: 'inline-flex', alignItems: 'center', gap: '4px' }}
                    onClick={() => onSelectInvoice ? onSelectInvoice(inv.id) : setSelectedInvoice(inv)}
                  >
                    <Eye size={14} /> Verification Detail
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Details Modal */}
      {selectedInvoice && (
        <div style={{
          position: 'fixed',
          inset: 0,
          background: 'rgba(0, 0, 0, 0.75)',
          backdropFilter: 'blur(8px)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 100,
          padding: '24px'
        }}>
          <div className="glass-panel" style={{ width: '100%', maxWidth: '600px', padding: '32px', border: '1px solid rgba(255, 255, 255, 0.15)' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '20px' }}>
              <h3 style={{ fontSize: '1.2rem', fontWeight: 700 }} className="font-mono">
                Invoice Details: {selectedInvoice.invoice_number}
              </h3>
              <button className="btn-secondary" style={{ padding: '4px 10px' }} onClick={() => setSelectedInvoice(null)}>✕</button>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '20px' }}>
              <div style={{ background: 'rgba(255, 255, 255, 0.03)', padding: '12px', borderRadius: '8px' }}>
                <div style={{ fontSize: '0.75rem', color: '#94a3b8' }}>VENDOR</div>
                <div style={{ fontWeight: 600, marginTop: '2px' }}>{selectedInvoice.vendor_name}</div>
              </div>
              <div style={{ background: 'rgba(255, 255, 255, 0.03)', padding: '12px', borderRadius: '8px' }}>
                <div style={{ fontSize: '0.75rem', color: '#94a3b8' }}>TOTAL AMOUNT</div>
                <div style={{ fontWeight: 700, color: '#818cf8', marginTop: '2px' }}>${(selectedInvoice.total_amount || 0).toFixed(2)}</div>
              </div>
            </div>

            <div style={{ fontSize: '0.8rem', color: '#94a3b8', marginBottom: '16px' }}>LINE ITEMS</div>
            <div style={{ background: 'rgba(0, 0, 0, 0.3)', padding: '14px', borderRadius: '8px', marginBottom: '20px' }}>
              {selectedInvoice.line_items?.map((item, idx) => (
                <div key={idx} style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.82rem', padding: '4px 0' }}>
                  <span>{item.description} (x{item.quantity})</span>
                  <span style={{ fontWeight: 600 }}>${item.line_total?.toFixed(2)}</span>
                </div>
              ))}
            </div>

            <button className="btn-primary" style={{ width: '100%', justifyContent: 'center' }} onClick={() => setSelectedInvoice(null)}>
              Close Detail View
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
