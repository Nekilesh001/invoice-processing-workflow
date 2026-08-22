import React, { useState, useEffect } from 'react';
import { ShoppingBag, Search, RefreshCw, ChevronRight, ArrowLeft, Building2, FileText, CheckCircle2, AlertTriangle, Layers, DollarSign } from 'lucide-react';

export default function PurchaseOrdersView({ onSelectPo, onSelectVendor, onSelectInvoice }) {
  const [pos, setPos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('ALL');
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
            <ShoppingBag size={18} color="#34d399" /> Purchase Order Authorization & Balance Summary
          </h3>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '16px' }}>
            <div style={{ background: 'rgba(52, 211, 153, 0.08)', border: '1px solid rgba(52, 211, 153, 0.2)', padding: '16px', borderRadius: '12px' }}>
              <span style={{ color: '#64748b', fontSize: '0.75rem', display: 'block' }}>Authorized Limit Total</span>
              <span style={{ fontSize: '1.5rem', fontWeight: 800, color: '#34d399' }}>${poDetail.authorized_total?.toFixed(2)}</span>
            </div>

            <div style={{ background: 'rgba(56, 189, 248, 0.08)', border: '1px solid rgba(56, 189, 248, 0.2)', padding: '16px', borderRadius: '12px' }}>
              <span style={{ color: '#64748b', fontSize: '0.75rem', display: 'block' }}>Used Amount Billed</span>
              <span style={{ fontSize: '1.5rem', fontWeight: 800, color: '#38bdf8' }}>${usedAmount.toFixed(2)}</span>
            </div>

            <div style={{ background: 'rgba(129, 140, 248, 0.08)', border: '1px solid rgba(129, 140, 248, 0.2)', padding: '16px', borderRadius: '12px' }}>
              <span style={{ color: '#64748b', fontSize: '0.75rem', display: 'block' }}>Remaining Balance</span>
              <span style={{ fontSize: '1.5rem', fontWeight: 800, color: '#818cf8' }}>${poDetail.remaining_balance?.toFixed(2)}</span>
            </div>
          </div>
        </div>

        {/* PO Line Items Table */}
        <div className="glass-panel" style={{ padding: '24px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Layers size={20} color="#38bdf8" />
              <h3 style={{ fontSize: '1rem', fontWeight: 700, margin: 0 }}>Authorized Line Items ({poDetail.line_items?.length || 0})</h3>
            </div>
          </div>

          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.1)', textAlign: 'left', color: '#94a3b8' }}>
                  <th style={{ padding: '12px' }}>Description</th>
                  <th style={{ padding: '12px' }}>Product Code / SKU</th>
                  <th style={{ padding: '12px', textAlign: 'right' }}>Quantity</th>
                  <th style={{ padding: '12px' }}>Unit</th>
                  <th style={{ padding: '12px', textAlign: 'right' }}>Unit Price</th>
                  <th style={{ padding: '12px', textAlign: 'right' }}>Line Total</th>
                </tr>
              </thead>
              <tbody>
                {(poDetail.line_items || []).length === 0 ? (
                  <tr>
                    <td colSpan="6" style={{ padding: '24px', textAlign: 'center', color: '#64748b' }}>
                      No line items specified for this purchase order.
                    </td>
                  </tr>
                ) : (
                  poDetail.line_items.map((item, idx) => (
                    <tr key={idx} style={{ borderBottom: '1px solid rgba(255,255,255,0.04)' }}>
                      <td style={{ padding: '12px', fontWeight: 600 }}>{item.description}</td>
                      <td style={{ padding: '12px', color: '#38bdf8' }}>{item.product_code || 'N/A'}</td>
                      <td style={{ padding: '12px', textAlign: 'right' }}>{item.quantity}</td>
                      <td style={{ padding: '12px', color: '#94a3b8' }}>{item.unit || 'units'}</td>
                      <td style={{ padding: '12px', textAlign: 'right' }}>${item.unit_price?.toFixed(2)}</td>
                      <td style={{ padding: '12px', textAlign: 'right', fontWeight: 700, color: '#34d399' }}>${item.line_total?.toFixed(2)}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Associated Invoices Table */}
        <div className="glass-panel" style={{ padding: '24px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <FileText size={20} color="#818cf8" />
              <h3 style={{ fontSize: '1rem', fontWeight: 700, margin: 0 }}>Associated Billed Invoices ({poDetail.related_invoices?.length || 0})</h3>
            </div>
          </div>

          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.1)', textAlign: 'left', color: '#94a3b8' }}>
                  <th style={{ padding: '12px' }}>Invoice Number</th>
                  <th style={{ padding: '12px' }}>Invoice Date</th>
                  <th style={{ padding: '12px', textAlign: 'right' }}>Total Billed</th>
                  <th style={{ padding: '12px', textAlign: 'center' }}>Status</th>
                  <th style={{ padding: '12px', textAlign: 'right' }}>Action</th>
                </tr>
              </thead>
              <tbody>
                {(poDetail.related_invoices || []).length === 0 ? (
                  <tr>
                    <td colSpan="5" style={{ padding: '24px', textAlign: 'center', color: '#64748b' }}>
                      No invoices linked to this purchase order yet.
                    </td>
                  </tr>
                ) : (
                  poDetail.related_invoices.map(inv => (
                    <tr key={inv.id} style={{ borderBottom: '1px solid rgba(255,255,255,0.04)' }} className="table-row-hover">
                      <td style={{ padding: '12px', fontWeight: 700 }}>{inv.invoice_number}</td>
                      <td style={{ padding: '12px' }}>{inv.invoice_date || 'N/A'}</td>
                      <td style={{ padding: '12px', textAlign: 'right', fontWeight: 700, color: '#818cf8' }}>${inv.total_amount?.toFixed(2)}</td>
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
    <div className="glass-panel" style={{ padding: '32px' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '24px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{ width: '40px', height: '40px', borderRadius: '12px', background: 'rgba(52, 211, 153, 0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <ShoppingBag size={22} color="#34d399" />
          </div>
          <div>
            <h2 style={{ fontSize: '1.2rem', fontWeight: 700 }}>Enterprise Purchase Orders</h2>
            <p style={{ fontSize: '0.8rem', color: '#94a3b8' }}>SQL-backed master authorization records</p>
          </div>
        </div>

        <button className="btn-secondary" style={{ padding: '8px 14px', fontSize: '0.8rem', display: 'flex', alignItems: 'center', gap: '6px' }} onClick={fetchPurchaseOrders}>
          <RefreshCw size={14} className={loading ? 'animate-spin' : ''} /> Refresh
        </button>
      </div>

      {/* Search & Status Filter Controls */}
      <div style={{ display: 'flex', gap: '16px', marginBottom: '20px' }}>
        <div style={{ flex: 1, position: 'relative' }}>
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
          <option value="DRAFT" style={{ background: '#0f172a' }}>Draft</option>
        </select>
      </div>

      {/* PO Table */}
      <div style={{ overflowX: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.88rem' }}>
          <thead>
            <tr style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.1)', color: '#94a3b8', fontSize: '0.75rem' }}>
              <th style={{ padding: '12px 16px' }}>PO NUMBER</th>
              <th style={{ padding: '12px 16px' }}>VENDOR</th>
              <th style={{ padding: '12px 16px' }}>PO DATE</th>
              <th style={{ padding: '12px 16px', textAlign: 'right' }}>AUTHORIZED TOTAL</th>
              <th style={{ padding: '12px 16px', textAlign: 'right' }}>REMAINING BALANCE</th>
              <th style={{ padding: '12px 16px', textAlign: 'center' }}>STATUS</th>
              <th style={{ padding: '12px 16px', textAlign: 'right' }}>ACTION</th>
            </tr>
          </thead>
          <tbody>
            {pos.length === 0 && !loading && (
              <tr>
                <td colSpan="7" style={{ textAlign: 'center', padding: '40px', color: '#64748b' }}>
                  No purchase orders found matching query.
                </td>
              </tr>
            )}
            {pos.map((po) => (
              <tr key={po.id} style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.04)', cursor: 'pointer' }} className="table-row-hover" onClick={() => handlePoClick(po.id)}>
                <td style={{ padding: '14px 16px', fontWeight: 700, color: '#38bdf8' }}>{po.po_number}</td>
                <td style={{ padding: '14px 16px', color: '#e2e8f0' }}>{po.vendor_name}</td>
                <td style={{ padding: '14px 16px' }}>{po.po_date || 'N/A'}</td>
                <td style={{ padding: '14px 16px', textAlign: 'right', fontWeight: 700 }}>${po.authorized_total?.toFixed(2)}</td>
                <td style={{ padding: '14px 16px', textAlign: 'right', fontWeight: 700, color: '#34d399' }}>${po.remaining_balance?.toFixed(2)}</td>
                <td style={{ padding: '14px 16px', textAlign: 'center' }}>
                  <span className={po.status === 'APPROVED' ? 'badge badge-success' : 'badge badge-warning'}>
                    {po.status}
                  </span>
                </td>
                <td style={{ padding: '14px 16px', textAlign: 'right' }}>
                  <button className="btn-secondary" style={{ padding: '6px 12px', fontSize: '0.75rem', display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
                    Inspect PO <ChevronRight size={14} />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
