import React, { useState, useEffect } from 'react';
import { Building2, Search, RefreshCw, ChevronRight, ArrowLeft, ShoppingBag, FileText, CheckCircle2, ShieldCheck, Mail, Phone, MapPin } from 'lucide-react';

export default function VendorsView({ onSelectVendor, onSelectPo, onSelectInvoice }) {
  const [vendors, setVendors] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedVendorId, setSelectedVendorId] = useState(null);
  const [vendorDetail, setVendorDetail] = useState(null);
  const [detailLoading, setDetailLoading] = useState(false);

  const fetchVendors = async () => {
    setLoading(true);
    try {
      const url = searchTerm.trim()
        ? `/api/v1/vendors?search=${encodeURIComponent(searchTerm.trim())}`
        : '/api/v1/vendors';
      const res = await fetch(url);
      if (res.ok) {
        const data = await res.json();
        setVendors(data);
      }
    } catch (e) {
      console.error('Failed to fetch vendors', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchVendors();
  }, [searchTerm]);

  const fetchVendorDetail = async (id) => {
    setDetailLoading(true);
    try {
      const res = await fetch(`/api/v1/vendors/${id}`);
      if (res.ok) {
        const data = await res.json();
        setVendorDetail(data);
      }
    } catch (e) {
      console.error('Failed to fetch vendor detail', e);
    } finally {
      setDetailLoading(false);
    }
  };

  const handleVendorClick = (id) => {
    setSelectedVendorId(id);
    fetchVendorDetail(id);
    if (onSelectVendor) onSelectVendor(id);
  };

  // Vendor Detail Screen
  if (selectedVendorId) {
    if (detailLoading || !vendorDetail) {
      return (
        <div className="glass-panel" style={{ padding: '48px', textAlign: 'center' }}>
          <div className="animate-spin" style={{ width: '36px', height: '36px', border: '3px solid rgba(99,102,241,0.2)', borderTopColor: '#6366f1', borderRadius: '50%', margin: '0 auto 16px' }} />
          <p style={{ color: '#94a3b8' }}>Loading master vendor records...</p>
        </div>
      );
    }

    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
        {/* Header Navigation */}
        <div className="glass-panel" style={{ padding: '24px 32px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
            <button
              className="btn-secondary"
              style={{ padding: '8px 14px', fontSize: '0.85rem', display: 'flex', alignItems: 'center', gap: '6px' }}
              onClick={() => { setSelectedVendorId(null); setVendorDetail(null); }}
            >
              <ArrowLeft size={16} /> Back to Vendors List
            </button>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <h1 style={{ fontSize: '1.4rem', fontWeight: 800, color: '#f8fafc', margin: 0 }}>
                  {vendorDetail.name}
                </h1>
                <span className="badge badge-success" style={{ padding: '4px 12px', fontSize: '0.75rem' }}>
                  ✓ APPROVED VENDOR
                </span>
              </div>
              <p style={{ fontSize: '0.85rem', color: '#94a3b8', marginTop: '4px' }}>
                Tax ID: <strong style={{ color: '#e2e8f0' }}>{vendorDetail.tax_id || 'N/A'}</strong> • Reg #: {vendorDetail.registration_number || 'N/A'}
              </p>
            </div>
          </div>
        </div>

        {/* Vendor Contact & Registration Grid */}
        <div className="glass-panel" style={{ padding: '24px' }}>
          <h3 style={{ fontSize: '1rem', fontWeight: 700, marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Building2 size={18} color="#818cf8" /> Vendor Profile & Contact Information
          </h3>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '16px', fontSize: '0.88rem' }}>
            <div style={{ background: 'rgba(255, 255, 255, 0.03)', padding: '12px 16px', borderRadius: '10px' }}>
              <span style={{ color: '#64748b', fontSize: '0.75rem', display: 'block' }}>Tax Identification Number (TIN)</span>
              <strong style={{ color: '#38bdf8' }}>{vendorDetail.tax_id || 'N/A'}</strong>
            </div>
            <div style={{ background: 'rgba(255, 255, 255, 0.03)', padding: '12px 16px', borderRadius: '10px' }}>
              <span style={{ color: '#64748b', fontSize: '0.75rem', display: 'block' }}>Registration Number</span>
              <strong>{vendorDetail.registration_number || 'N/A'}</strong>
            </div>
            <div style={{ background: 'rgba(255, 255, 255, 0.03)', padding: '12px 16px', borderRadius: '10px' }}>
              <span style={{ color: '#64748b', fontSize: '0.75rem', display: 'block' }}>Official Email</span>
              <strong style={{ display: 'flex', alignItems: 'center', gap: '6px' }}><Mail size={14} color="#94a3b8" /> {vendorDetail.email || 'billing@domain.com'}</strong>
            </div>
            <div style={{ background: 'rgba(255, 255, 255, 0.03)', padding: '12px 16px', borderRadius: '10px' }}>
              <span style={{ color: '#64748b', fontSize: '0.75rem', display: 'block' }}>Phone Contact</span>
              <strong style={{ display: 'flex', alignItems: 'center', gap: '6px' }}><Phone size={14} color="#94a3b8" /> {vendorDetail.phone || '+1 (800) 555-0199'}</strong>
            </div>
          </div>
        </div>

        {/* Master Purchase Orders Table */}
        <div className="glass-panel" style={{ padding: '24px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <ShoppingBag size={20} color="#34d399" />
              <h3 style={{ fontSize: '1rem', fontWeight: 700, margin: 0 }}>Associated Purchase Orders ({vendorDetail.purchase_orders?.length || 0})</h3>
            </div>
          </div>

          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.1)', textAlign: 'left', color: '#94a3b8' }}>
                  <th style={{ padding: '12px' }}>PO Number</th>
                  <th style={{ padding: '12px' }}>PO Date</th>
                  <th style={{ padding: '12px', textAlign: 'right' }}>Authorized Total</th>
                  <th style={{ padding: '12px', textAlign: 'right' }}>Remaining Balance</th>
                  <th style={{ padding: '12px', textAlign: 'center' }}>Status</th>
                  <th style={{ padding: '12px', textAlign: 'right' }}>Action</th>
                </tr>
              </thead>
              <tbody>
                {(vendorDetail.purchase_orders || []).length === 0 ? (
                  <tr>
                    <td colSpan="6" style={{ padding: '24px', textAlign: 'center', color: '#64748b' }}>
                      No active purchase orders associated with this vendor.
                    </td>
                  </tr>
                ) : (
                  vendorDetail.purchase_orders.map(po => (
                    <tr key={po.id} style={{ borderBottom: '1px solid rgba(255,255,255,0.04)' }} className="table-row-hover">
                      <td style={{ padding: '12px', fontWeight: 700, color: '#38bdf8' }}>{po.po_number}</td>
                      <td style={{ padding: '12px' }}>{po.po_date || 'N/A'}</td>
                      <td style={{ padding: '12px', textAlign: 'right', fontWeight: 700 }}>${po.authorized_total?.toFixed(2)}</td>
                      <td style={{ padding: '12px', textAlign: 'right', fontWeight: 700, color: '#34d399' }}>${po.remaining_balance?.toFixed(2)}</td>
                      <td style={{ padding: '12px', textAlign: 'center' }}>
                        <span className={po.status === 'APPROVED' ? 'badge badge-success' : 'badge badge-warning'}>
                          {po.status}
                        </span>
                      </td>
                      <td style={{ padding: '12px', textAlign: 'right' }}>
                        <button
                          className="btn-secondary"
                          style={{ padding: '4px 10px', fontSize: '0.75rem' }}
                          onClick={() => onSelectPo && onSelectPo(po.id)}
                        >
                          View PO
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Master Invoices Table */}
        <div className="glass-panel" style={{ padding: '24px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <FileText size={20} color="#818cf8" />
              <h3 style={{ fontSize: '1rem', fontWeight: 700, margin: 0 }}>Vendor Invoice Billed History ({vendorDetail.invoices?.length || 0})</h3>
            </div>
          </div>

          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.1)', textAlign: 'left', color: '#94a3b8' }}>
                  <th style={{ padding: '12px' }}>Invoice Number</th>
                  <th style={{ padding: '12px' }}>Invoice Date</th>
                  <th style={{ padding: '12px' }}>PO Reference</th>
                  <th style={{ padding: '12px', textAlign: 'right' }}>Total Billed</th>
                  <th style={{ padding: '12px', textAlign: 'center' }}>Status</th>
                  <th style={{ padding: '12px', textAlign: 'right' }}>Action</th>
                </tr>
              </thead>
              <tbody>
                {(vendorDetail.invoices || []).length === 0 ? (
                  <tr>
                    <td colSpan="6" style={{ padding: '24px', textAlign: 'center', color: '#64748b' }}>
                      No invoices billed by this vendor yet.
                    </td>
                  </tr>
                ) : (
                  vendorDetail.invoices.map(inv => (
                    <tr key={inv.id} style={{ borderBottom: '1px solid rgba(255,255,255,0.04)' }} className="table-row-hover">
                      <td style={{ padding: '12px', fontWeight: 700 }}>{inv.invoice_number}</td>
                      <td style={{ padding: '12px' }}>{inv.invoice_date || 'N/A'}</td>
                      <td style={{ padding: '12px', color: '#38bdf8' }}>{inv.po_number || 'None'}</td>
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

  // Vendor List Screen
  return (
    <div className="glass-panel" style={{ padding: '32px' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '24px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{ width: '40px', height: '40px', borderRadius: '12px', background: 'rgba(99, 102, 241, 0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Building2 size={22} color="#818cf8" />
          </div>
          <div>
            <h2 style={{ fontSize: '1.2rem', fontWeight: 700 }}>Master Vendors Registry</h2>
            <p style={{ fontSize: '0.8rem', color: '#94a3b8' }}>SQL-backed billers and verified enterprise suppliers</p>
          </div>
        </div>

        <button className="btn-secondary" style={{ padding: '8px 14px', fontSize: '0.8rem', display: 'flex', alignItems: 'center', gap: '6px' }} onClick={fetchVendors}>
          <RefreshCw size={14} className={loading ? 'animate-spin' : ''} /> Refresh
        </button>
      </div>

      {/* Search Input */}
      <div style={{ position: 'relative', marginBottom: '20px' }}>
        <Search size={18} color="#64748b" style={{ position: 'absolute', left: '14px', top: '50%', transform: 'translateY(-50%)' }} />
        <input
          type="text"
          placeholder="Search by vendor name, TIN, or registration number..."
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

      {/* Vendors Table */}
      <div style={{ overflowX: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.88rem' }}>
          <thead>
            <tr style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.1)', color: '#94a3b8', fontSize: '0.75rem' }}>
              <th style={{ padding: '12px 16px' }}>VENDOR NAME</th>
              <th style={{ padding: '12px 16px' }}>TAX ID (TIN)</th>
              <th style={{ padding: '12px 16px' }}>STATUS</th>
              <th style={{ padding: '12px 16px', textAlign: 'center' }}>PURCHASE ORDERS</th>
              <th style={{ padding: '12px 16px', textAlign: 'center' }}>INVOICES BILLED</th>
              <th style={{ padding: '12px 16px', textAlign: 'right' }}>ACTION</th>
            </tr>
          </thead>
          <tbody>
            {vendors.length === 0 && !loading && (
              <tr>
                <td colSpan="6" style={{ textAlign: 'center', padding: '40px', color: '#64748b' }}>
                  No master vendors found matching search query.
                </td>
              </tr>
            )}
            {vendors.map((v) => (
              <tr key={v.id} style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.04)', cursor: 'pointer' }} className="table-row-hover" onClick={() => handleVendorClick(v.id)}>
                <td style={{ padding: '14px 16px', fontWeight: 700, color: '#f8fafc' }}>{v.name}</td>
                <td style={{ padding: '14px 16px', color: '#38bdf8' }} className="font-mono">{v.tax_id || 'N/A'}</td>
                <td style={{ padding: '14px 16px' }}>
                  <span className="badge badge-success">✓ APPROVED</span>
                </td>
                <td style={{ padding: '14px 16px', textAlign: 'center', fontWeight: 600 }}>{v.purchase_order_count} POs</td>
                <td style={{ padding: '14px 16px', textAlign: 'center', fontWeight: 600, color: '#818cf8' }}>{v.invoice_count} Invoices</td>
                <td style={{ padding: '14px 16px', textAlign: 'right' }}>
                  <button className="btn-secondary" style={{ padding: '6px 12px', fontSize: '0.75rem', display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
                    View Profile <ChevronRight size={14} />
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
