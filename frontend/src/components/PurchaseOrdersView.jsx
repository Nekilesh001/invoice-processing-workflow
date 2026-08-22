import React, { useState, useEffect } from 'react';
import { ShoppingBag, Search, RefreshCw, ChevronRight, ArrowLeft, Building2, FileText, CheckCircle2, AlertTriangle, Layers, DollarSign, LayoutGrid, List, Eye } from 'lucide-react';

export default function PurchaseOrdersView({ onSelectPo, onSelectVendor, onSelectInvoice }) {
  const [pos, setPos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [viewMode, setViewMode] = useState('cards'); // 'cards' or 'table'
  const [selectedPoId, setSelectedPoId] = useState(null);
  const [poDetail, setPoDetail] = useState(null);
  const [detailLoading, setDetailLoading] = useState(false);

  const fetchPurchaseOrders = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (searchTerm.trim()) params.append('search', searchTerm.trim());
      if (statusFilter !== 'ALL') params.append('status', statusFilter);

      const res = await fetch(`/api/v1/purchase-orders?${params.toString()}`);
      if (res.ok) {
        const data = await res.json();
        setPos(data);
      }
    } catch (e) {
      console.error('Failed to fetch purchase orders', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPurchaseOrders();
  }, [searchTerm, statusFilter]);

  const fetchPoDetail = async (id) => {
    setDetailLoading(true);
    try {
      const res = await fetch(`/api/v1/purchase-orders/${id}`);
      if (res.ok) {
        const data = await res.json();
        setPoDetail(data);
      }
    } catch (e) {
      console.error('Failed to fetch PO detail', e);
    } finally {
      setDetailLoading(false);
    }
  };

  const handlePoClick = (id) => {
    setSelectedPoId(id);
    fetchPoDetail(id);
    if (onSelectPo) onSelectPo(id);
  };

  // PO Detail Screen
  if (selectedPoId) {
    if (detailLoading || !poDetail) {
      return (
        <div className="glass-panel" style={{ padding: '48px', textAlign: 'center' }}>
          <div className="animate-spin" style={{ width: '36px', height: '36px', border: '3px solid rgba(52,211,153,0.2)', borderTopColor: '#34d399', borderRadius: '50%', margin: '0 auto 16px' }} />
          <p style={{ color: '#94a3b8' }}>Loading Purchase Order records...</p>
        </div>
      );
    }

    const usedAmount = (poDetail.authorized_total || 0) - (poDetail.remaining_balance || 0);

    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
        {/* Header Navigation */}
        <div className="glass-panel" style={{ padding: '24px 32px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
            <button
              className="btn-secondary"
              style={{ padding: '8px 14px', fontSize: '0.85rem', display: 'flex', alignItems: 'center', gap: '6px' }}
              onClick={() => { setSelectedPoId(null); setPoDetail(null); }}
            >
              <ArrowLeft size={16} /> Back to PO List
            </button>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <h1 style={{ fontSize: '1.4rem', fontWeight: 800, color: '#f8fafc', margin: 0 }}>
                  {poDetail.po_number}
                </h1>
                <span className={poDetail.status === 'APPROVED' ? 'badge badge-success' : 'badge badge-warning'} style={{ padding: '4px 12px', fontSize: '0.75rem' }}>
                  {poDetail.status}
                </span>
              </div>
              <p style={{ fontSize: '0.85rem', color: '#94a3b8', marginTop: '4px' }}>
                Vendor: <strong style={{ color: '#e2e8f0', cursor: 'pointer' }} onClick={() => poDetail.vendor?.id && onSelectVendor && onSelectVendor(poDetail.vendor.id)}>
                  {poDetail.vendor?.name || 'Unknown Vendor'}
                </strong> • PO Date: {poDetail.po_date || 'N/A'}
              </p>
            </div>
          </div>
        </div>

        {/* PO Financial Balance Header Grid */}
        <div className="glass-panel" style={{ padding: '24px' }}>
          <h3 style={{ fontSize: '1rem', fontWeight: 700, marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <DollarSign size={18} color="#34d399" /> Authorized Financial Limit vs Available Balance
          </h3>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px' }}>
            <div style={{ background: 'rgba(255,255,255,0.03)', padding: '16px', borderRadius: '12px', border: '1px solid rgba(255,255,255,0.06)' }}>
              <span style={{ fontSize: '0.75rem', color: '#94a3b8', display: 'block' }}>Authorized Limit Total</span>
              <span style={{ fontSize: '1.4rem', fontWeight: 800, color: '#f8fafc' }}>
                ${poDetail.authorized_total?.toLocaleString(undefined, { minimumFractionDigits: 2 })}
              </span>
            </div>

            <div style={{ background: 'rgba(52,211,153,0.08)', padding: '16px', borderRadius: '12px', border: '1px solid rgba(52,211,153,0.2)' }}>
              <span style={{ fontSize: '0.75rem', color: '#94a3b8', display: 'block' }}>Remaining Available Balance</span>
              <span style={{ fontSize: '1.4rem', fontWeight: 800, color: '#34d399' }}>
                ${poDetail.remaining_balance?.toLocaleString(undefined, { minimumFractionDigits: 2 })}
              </span>
            </div>

            <div style={{ background: 'rgba(99,102,241,0.08)', padding: '16px', borderRadius: '12px', border: '1px solid rgba(99,102,241,0.2)' }}>
              <span style={{ fontSize: '0.75rem', color: '#94a3b8', display: 'block' }}>Total Billed Against PO</span>
              <span style={{ fontSize: '1.4rem', fontWeight: 800, color: '#818cf8' }}>
                ${usedAmount.toLocaleString(undefined, { minimumFractionDigits: 2 })}
              </span>
            </div>
          </div>
        </div>

        {/* PO Line Items Table */}
        <div className="glass-panel" style={{ padding: '24px' }}>
          <h3 style={{ fontSize: '1rem', fontWeight: 700, marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Layers size={18} color="#818cf8" /> Authorized Line Items ({poDetail.line_items?.length || 0})
          </h3>

          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.1)', textAlign: 'left', color: '#94a3b8' }}>
                  <th style={{ padding: '10px 12px' }}>LINE DESCRIPTION</th>
                  <th style={{ padding: '10px 12px' }}>PRODUCT CODE</th>
                  <th style={{ padding: '10px 12px', textAlign: 'center' }}>QTY</th>
                  <th style={{ padding: '10px 12px', textAlign: 'right' }}>UNIT PRICE</th>
                  <th style={{ padding: '10px 12px', textAlign: 'right' }}>LINE TOTAL</th>
                </tr>
              </thead>
              <tbody>
                {(!poDetail.line_items || poDetail.line_items.length === 0) ? (
                  <tr>
                    <td colSpan="5" style={{ padding: '24px', textAlign: 'center', color: '#64748b' }}>
                      No line items recorded for this purchase order.
                    </td>
                  </tr>
                ) : (
                  poDetail.line_items.map(li => (
                    <tr key={li.id} style={{ borderBottom: '1px solid rgba(255,255,255,0.04)' }}>
                      <td style={{ padding: '12px', fontWeight: 600, color: '#f8fafc' }}>{li.description}</td>
                      <td style={{ padding: '12px', color: '#94a3b8' }} className="font-mono">{li.product_code || 'N/A'}</td>
                      <td style={{ padding: '12px', textAlign: 'center', fontWeight: 700 }}>{li.quantity}</td>
                      <td style={{ padding: '12px', textAlign: 'right' }}>${li.unit_price?.toFixed(2)}</td>
                      <td style={{ padding: '12px', textAlign: 'right', fontWeight: 700, color: '#34d399' }}>${li.line_total?.toFixed(2)}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Associated Billed Invoices */}
        <div className="glass-panel" style={{ padding: '24px' }}>
          <h3 style={{ fontSize: '1rem', fontWeight: 700, marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <FileText size={18} color="#38bdf8" /> Billed Invoices Billed Against This PO ({poDetail.invoices?.length || 0})
          </h3>

          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.1)', textAlign: 'left', color: '#94a3b8' }}>
                  <th style={{ padding: '10px 12px' }}>INVOICE #</th>
                  <th style={{ padding: '10px 12px' }}>DATE</th>
                  <th style={{ padding: '10px 12px', textAlign: 'right' }}>TOTAL</th>
                  <th style={{ padding: '10px 12px', textAlign: 'center' }}>STATUS</th>
                  <th style={{ padding: '10px 12px', textAlign: 'right' }}>ACTION</th>
                </tr>
              </thead>
              <tbody>
                {(!poDetail.invoices || poDetail.invoices.length === 0) ? (
                  <tr>
                    <td colSpan="5" style={{ padding: '24px', textAlign: 'center', color: '#64748b' }}>
                      No invoices billed against this purchase order yet.
                    </td>
                  </tr>
                ) : (
                  poDetail.invoices.map(inv => (
                    <tr key={inv.id} style={{ borderBottom: '1px solid rgba(255,255,255,0.04)' }} className="table-row-hover">
                      <td style={{ padding: '12px', fontWeight: 700, color: '#38bdf8' }}>{inv.invoice_number}</td>
                      <td style={{ padding: '12px' }}>{inv.invoice_date || 'N/A'}</td>
                      <td style={{ padding: '12px', textAlign: 'right', fontWeight: 700, color: '#4ade80' }}>${inv.total_amount?.toFixed(2)}</td>
                      <td style={{ padding: '12px', textAlign: 'center' }}>
                        <span className={inv.status === 'APPROVED' ? 'badge badge-success' : inv.status === 'NEEDS_REVIEW' ? 'badge badge-warning' : 'badge badge-danger'}>
                          {inv.status}
                        </span>
                      </td>
                      <td style={{ padding: '12px', textAlign: 'right' }}>
                        <button
                          className="btn-secondary"
                          style={{ padding: '4px 10px', fontSize: '0.75rem' }}
                          onClick={() => onSelectInvoice && onSelectInvoice(inv.id)}
                        >
                          View Invoice
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    );
  }

  // PO List Screen
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      
      {/* Header Panel */}
      <div className="glass-panel" style={{ padding: '24px 32px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
          <div style={{ width: '42px', height: '42px', borderRadius: '12px', background: 'rgba(52, 211, 153, 0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <ShoppingBag size={24} color="#34d399" />
          </div>
          <div>
            <h2 style={{ fontSize: '1.3rem', fontWeight: 800, margin: 0, color: '#f8fafc' }}>
              Enterprise Purchase Orders
            </h2>
            <p style={{ fontSize: '0.8rem', color: '#94a3b8', marginTop: '2px' }}>
              SQL-backed master authorization records
            </p>
          </div>
        </div>

        {/* Action Controls & View Mode Toggle */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
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

          <button className="btn-secondary" style={{ padding: '8px 14px', fontSize: '0.8rem', display: 'flex', alignItems: 'center', gap: '6px' }} onClick={fetchPurchaseOrders}>
            <RefreshCw size={14} className={loading ? 'animate-spin' : ''} /> Refresh
          </button>
        </div>
      </div>

      {/* Search & Filter Controls */}
      <div className="glass-panel" style={{ padding: '16px 24px', display: 'flex', gap: '16px', flexWrap: 'wrap' }}>
        <div style={{ flex: 1, position: 'relative', minWidth: '280px' }}>
          <Search size={18} color="#64748b" style={{ position: 'absolute', left: '14px', top: '50%', transform: 'translateY(-50%)' }} />
          <input
            type="text"
            placeholder="Search by PO number or vendor name..."
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
          <option value="EXHAUSTED" style={{ background: '#0f172a' }}>Exhausted</option>
          <option value="CANCELLED" style={{ background: '#0f172a' }}>Cancelled</option>
        </select>
      </div>

      {/* Loading State */}
      {loading && pos.length === 0 && (
        <div className="glass-panel" style={{ padding: '48px', textAlign: 'center' }}>
          <div className="animate-spin" style={{ width: '32px', height: '32px', border: '3px solid rgba(52,211,153,0.2)', borderTopColor: '#34d399', borderRadius: '50%', margin: '0 auto 12px' }} />
          <p style={{ color: '#94a3b8' }}>Loading Purchase Orders database...</p>
        </div>
      )}

      {/* Empty State */}
      {pos.length === 0 && !loading && (
        <div className="glass-panel" style={{ padding: '48px', textAlign: 'center' }}>
          <ShoppingBag size={36} color="#64748b" style={{ marginBottom: '12px' }} />
          <p style={{ color: '#94a3b8', fontSize: '0.95rem' }}>No purchase orders match your filter criteria.</p>
        </div>
      )}

      {/* VIEW MODE 1: EXECUTIVE CARD GRID */}
      {viewMode === 'cards' && pos.length > 0 && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(340px, 1fr))', gap: '20px' }}>
          {pos.map((po) => {
            const usedPct = po.authorized_total > 0 ? Math.min(100, Math.round(((po.authorized_total - po.remaining_balance) / po.authorized_total) * 100)) : 0;
            return (
              <div
                key={po.id}
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
                onClick={() => handlePoClick(po.id)}
              >
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
                    <span style={{ fontSize: '1rem', fontWeight: 800, color: '#34d399' }} className="font-mono">
                      {po.po_number}
                    </span>
                    <span className={po.status === 'APPROVED' ? 'badge badge-success' : 'badge badge-warning'}>
                      {po.status}
                    </span>
                  </div>

                  {/* Vendor Name */}
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#e2e8f0', fontSize: '0.88rem', fontWeight: 600, marginBottom: '12px' }}>
                    <Building2 size={16} color="#94a3b8" />
                    <span>{po.vendor_name || 'Unknown Vendor'}</span>
                  </div>

                  {/* Balance Metrics Grid */}
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '12px' }}>
                    <div style={{ background: 'rgba(255,255,255,0.03)', padding: '8px 12px', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.05)' }}>
                      <span style={{ fontSize: '0.7rem', color: '#94a3b8', display: 'block' }}>AUTHORIZED LIMIT</span>
                      <strong style={{ fontSize: '0.95rem', color: '#f8fafc' }}>${po.authorized_total?.toFixed(2)}</strong>
                    </div>

                    <div style={{ background: 'rgba(52,211,153,0.08)', padding: '8px 12px', borderRadius: '8px', border: '1px solid rgba(52,211,153,0.2)' }}>
                      <span style={{ fontSize: '0.7rem', color: '#94a3b8', display: 'block' }}>REMAINING BALANCE</span>
                      <strong style={{ fontSize: '0.95rem', color: '#34d399' }}>${po.remaining_balance?.toFixed(2)}</strong>
                    </div>
                  </div>

                  {/* Utilization Progress Bar */}
                  <div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.72rem', color: '#94a3b8', marginBottom: '4px' }}>
                      <span>Billed Utilization</span>
                      <span>{usedPct}% Utilized</span>
                    </div>
                    <div style={{ height: '6px', borderRadius: '3px', background: 'rgba(255,255,255,0.05)', overflow: 'hidden' }}>
                      <div style={{ width: `${usedPct}%`, background: usedPct >= 90 ? '#f43f5e' : '#34d399', height: '100%', transition: 'width 0.3s ease' }} />
                    </div>
                  </div>
                </div>

                {/* Action Button */}
                <div style={{ paddingTop: '14px', borderTop: '1px solid rgba(255, 255, 255, 0.06)', display: 'flex', justifyContent: 'flex-end' }}>
                  <button
                    className="btn-secondary"
                    style={{ padding: '8px 14px', fontSize: '0.8rem', background: 'rgba(52, 211, 153, 0.15)', borderColor: 'rgba(52, 211, 153, 0.3)', color: '#34d399' }}
                    onClick={(e) => {
                      e.stopPropagation();
                      handlePoClick(po.id);
                    }}
                  >
                    Inspect PO <ChevronRight size={14} />
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* VIEW MODE 2: CLASSIC TABLE VIEW */}
      {viewMode === 'table' && pos.length > 0 && (
        <div className="glass-panel" style={{ padding: '24px', overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.88rem' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.1)', color: '#94a3b8', fontSize: '0.75rem' }} className="font-mono">
                <th style={{ padding: '12px 16px' }}>PO NUMBER</th>
                <th style={{ padding: '12px 16px' }}>VENDOR</th>
                <th style={{ padding: '12px 16px' }}>PO DATE</th>
                <th style={{ padding: '12px 16px' }}>AUTHORIZED TOTAL</th>
                <th style={{ padding: '12px 16px' }}>REMAINING BALANCE</th>
                <th style={{ padding: '12px 16px', textAlign: 'center' }}>STATUS</th>
                <th style={{ padding: '12px 16px', textAlign: 'right' }}>ACTION</th>
              </tr>
            </thead>
            <tbody>
              {pos.map((po) => (
                <tr
                  key={po.id}
                  style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.04)', cursor: 'pointer' }}
                  className="table-row-hover"
                  onClick={() => handlePoClick(po.id)}
                >
                  <td style={{ padding: '14px 16px', fontWeight: 700, color: '#34d399' }} className="font-mono">{po.po_number}</td>
                  <td style={{ padding: '14px 16px', color: '#e2e8f0' }}>{po.vendor_name || 'Unknown Vendor'}</td>
                  <td style={{ padding: '14px 16px', color: '#94a3b8' }}>{po.po_date || 'N/A'}</td>
                  <td style={{ padding: '14px 16px', fontWeight: 700 }}>${po.authorized_total?.toFixed(2)}</td>
                  <td style={{ padding: '14px 16px', fontWeight: 700, color: '#34d399' }}>${po.remaining_balance?.toFixed(2)}</td>
                  <td style={{ padding: '14px 16px', textAlign: 'center' }}>
                    <span className={po.status === 'APPROVED' ? 'badge badge-success' : 'badge badge-warning'}>
                      {po.status}
                    </span>
                  </td>
                  <td style={{ padding: '14px 16px', textAlign: 'right' }}>
                    <button
                      className="btn-secondary"
                      style={{ padding: '6px 12px', fontSize: '0.75rem' }}
                      onClick={(e) => {
                        e.stopPropagation();
                        handlePoClick(po.id);
                      }}
                    >
                      Inspect PO <ChevronRight size={12} />
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
