import React, { useState, useEffect } from 'react';
import { Building2, Search, RefreshCw, ChevronRight, ArrowLeft, ShoppingBag, FileText, CheckCircle2, ShieldCheck, Mail, Phone, MapPin, LayoutGrid, List, Eye } from 'lucide-react';

export default function VendorsView({ onSelectVendor, onSelectPo, onSelectInvoice }) {
  const [vendors, setVendors] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [viewMode, setViewMode] = useState('cards'); // 'cards' or 'table'
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
            <div style={{ background: 'rgba(255,255,255,0.03)', padding: '14px', borderRadius: '10px', border: '1px solid rgba(255,255,255,0.06)' }}>
              <span style={{ fontSize: '0.75rem', color: '#94a3b8', display: 'block' }}>Email Address</span>
              <span style={{ fontWeight: 600, color: '#38bdf8', display: 'flex', alignItems: 'center', gap: '6px', marginTop: '2px' }}>
                <Mail size={14} /> {vendorDetail.email || 'N/A'}
              </span>
            </div>

            <div style={{ background: 'rgba(255,255,255,0.03)', padding: '14px', borderRadius: '10px', border: '1px solid rgba(255,255,255,0.06)' }}>
              <span style={{ fontSize: '0.75rem', color: '#94a3b8', display: 'block' }}>Phone Number</span>
              <span style={{ fontWeight: 600, color: '#e2e8f0', display: 'flex', alignItems: 'center', gap: '6px', marginTop: '2px' }}>
                <Phone size={14} /> {vendorDetail.phone || 'N/A'}
              </span>
            </div>

            <div style={{ background: 'rgba(255,255,255,0.03)', padding: '14px', borderRadius: '10px', border: '1px solid rgba(255,255,255,0.06)' }}>
              <span style={{ fontSize: '0.75rem', color: '#94a3b8', display: 'block' }}>Tax Identification (TIN)</span>
              <span style={{ fontWeight: 700, color: '#34d399', marginTop: '2px', display: 'block' }}>
                {vendorDetail.tax_id || 'N/A'}
              </span>
            </div>

            <div style={{ background: 'rgba(255,255,255,0.03)', padding: '14px', borderRadius: '10px', border: '1px solid rgba(255,255,255,0.06)' }}>
              <span style={{ fontSize: '0.75rem', color: '#94a3b8', display: 'block' }}>Registration Number</span>
              <span style={{ fontWeight: 600, color: '#e2e8f0', marginTop: '2px', display: 'block' }}>
                {vendorDetail.registration_number || 'N/A'}
              </span>
            </div>
          </div>
        </div>

        {/* Related Purchase Orders */}
        <div className="glass-panel" style={{ padding: '24px' }}>
          <h3 style={{ fontSize: '1rem', fontWeight: 700, marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <ShoppingBag size={18} color="#34d399" /> Associated Enterprise Purchase Orders ({vendorDetail.purchase_orders?.length || 0})
          </h3>

          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.1)', textAlign: 'left', color: '#94a3b8' }}>
                  <th style={{ padding: '10px 12px' }}>PO NUMBER</th>
                  <th style={{ padding: '10px 12px' }}>AUTHORIZED TOTAL</th>
                  <th style={{ padding: '10px 12px' }}>REMAINING BALANCE</th>
                  <th style={{ padding: '10px 12px', textAlign: 'center' }}>STATUS</th>
                  <th style={{ padding: '10px 12px', textAlign: 'right' }}>ACTION</th>
                </tr>
              </thead>
              <tbody>
                {(!vendorDetail.purchase_orders || vendorDetail.purchase_orders.length === 0) ? (
                  <tr>
                    <td colSpan="5" style={{ padding: '24px', textAlign: 'center', color: '#64748b' }}>
                      No purchase orders associated with this vendor.
                    </td>
                  </tr>
                ) : (
                  vendorDetail.purchase_orders.map(po => (
                    <tr key={po.id} style={{ borderBottom: '1px solid rgba(255,255,255,0.04)' }} className="table-row-hover">
                      <td style={{ padding: '12px', fontWeight: 700, color: '#38bdf8' }}>{po.po_number}</td>
                      <td style={{ padding: '12px', fontWeight: 700 }}>${po.authorized_total?.toFixed(2)}</td>
                      <td style={{ padding: '12px', fontWeight: 700, color: '#34d399' }}>${po.remaining_balance?.toFixed(2)}</td>
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
                          Inspect PO
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Related Invoices Billed */}
        <div className="glass-panel" style={{ padding: '24px' }}>
          <h3 style={{ fontSize: '1rem', fontWeight: 700, marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <FileText size={18} color="#38bdf8" /> Billed Invoices History ({vendorDetail.invoices?.length || 0})
          </h3>

          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.1)', textAlign: 'left', color: '#94a3b8' }}>
                  <th style={{ padding: '10px 12px' }}>INVOICE #</th>
                  <th style={{ padding: '10px 12px' }}>DATE</th>
                  <th style={{ padding: '10px 12px' }}>PO REF</th>
                  <th style={{ padding: '10px 12px', textAlign: 'right' }}>TOTAL</th>
                  <th style={{ padding: '10px 12px', textAlign: 'center' }}>STATUS</th>
                  <th style={{ padding: '10px 12px', textAlign: 'right' }}>ACTION</th>
                </tr>
              </thead>
              <tbody>
                {(!vendorDetail.invoices || vendorDetail.invoices.length === 0) ? (
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
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      
      {/* Header Panel */}
      <div className="glass-panel" style={{ padding: '24px 32px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
          <div style={{ width: '42px', height: '42px', borderRadius: '12px', background: 'rgba(99, 102, 241, 0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Building2 size={24} color="#818cf8" />
          </div>
          <div>
            <h2 style={{ fontSize: '1.3rem', fontWeight: 800, margin: 0, color: '#f8fafc' }}>
              Master Vendors Registry
            </h2>
            <p style={{ fontSize: '0.8rem', color: '#94a3b8', marginTop: '2px' }}>
              SQL-backed billers and verified enterprise suppliers
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

          <button className="btn-secondary" style={{ padding: '8px 14px', fontSize: '0.8rem', display: 'flex', alignItems: 'center', gap: '6px' }} onClick={fetchVendors}>
            <RefreshCw size={14} className={loading ? 'animate-spin' : ''} /> Refresh
          </button>
        </div>
      </div>

      {/* Search Bar */}
      <div className="glass-panel" style={{ padding: '16px 24px' }}>
        <div style={{ position: 'relative' }}>
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
      </div>

      {/* Loading State */}
      {loading && vendors.length === 0 && (
        <div className="glass-panel" style={{ padding: '48px', textAlign: 'center' }}>
          <div className="animate-spin" style={{ width: '32px', height: '32px', border: '3px solid rgba(99,102,241,0.2)', borderTopColor: '#6366f1', borderRadius: '50%', margin: '0 auto 12px' }} />
          <p style={{ color: '#94a3b8' }}>Loading vendor registry records...</p>
        </div>
      )}

      {/* Empty State */}
      {vendors.length === 0 && !loading && (
        <div className="glass-panel" style={{ padding: '48px', textAlign: 'center' }}>
          <Building2 size={36} color="#64748b" style={{ marginBottom: '12px' }} />
          <p style={{ color: '#94a3b8', fontSize: '0.95rem' }}>No master vendors found matching your query.</p>
        </div>
      )}

      {/* VIEW MODE 1: EXECUTIVE CARD GRID */}
      {viewMode === 'cards' && vendors.length > 0 && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(340px, 1fr))', gap: '20px' }}>
          {vendors.map((vendor) => (
            <div
              key={vendor.id}
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
              onClick={() => handleVendorClick(vendor.id)}
            >
              <div>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <div style={{ width: '34px', height: '34px', borderRadius: '10px', background: 'rgba(99, 102, 241, 0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                      <Building2 size={18} color="#818cf8" />
                    </div>
                    <h3 style={{ fontSize: '1rem', fontWeight: 800, color: '#f8fafc', margin: 0 }}>
                      {vendor.name}
                    </h3>
                  </div>

                  <span className="badge badge-success" style={{ fontSize: '0.7rem' }}>
                    ✓ APPROVED
                  </span>
                </div>

                {/* Tax ID */}
                <div style={{ fontSize: '0.82rem', color: '#94a3b8', marginBottom: '12px' }}>
                  Tax Identification (TIN): <strong style={{ color: vendor.tax_id ? '#38bdf8' : '#64748b' }} className="font-mono">{vendor.tax_id || 'N/A'}</strong>
                </div>

                {/* Metrics Badges */}
                <div style={{ display: 'flex', gap: '12px' }}>
                  <div style={{ background: 'rgba(255,255,255,0.03)', padding: '8px 12px', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.05)', flex: 1 }}>
                    <span style={{ fontSize: '0.7rem', color: '#94a3b8', display: 'block' }}>PURCHASE ORDERS</span>
                    <strong style={{ fontSize: '0.95rem', color: '#e2e8f0' }}>{vendor.po_count} POs</strong>
                  </div>

                  <div style={{ background: 'rgba(255,255,255,0.03)', padding: '8px 12px', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.05)', flex: 1 }}>
                    <span style={{ fontSize: '0.7rem', color: '#94a3b8', display: 'block' }}>INVOICES BILLED</span>
                    <strong style={{ fontSize: '0.95rem', color: '#818cf8' }}>{vendor.invoice_count} Invoices</strong>
                  </div>
                </div>
              </div>

              {/* Action Button */}
              <div style={{ paddingTop: '14px', borderTop: '1px solid rgba(255, 255, 255, 0.06)', display: 'flex', justifyContent: 'flex-end' }}>
                <button
                  className="btn-secondary"
                  style={{ padding: '8px 14px', fontSize: '0.8rem', background: 'rgba(99, 102, 241, 0.15)', borderColor: 'rgba(99, 102, 241, 0.3)', color: '#818cf8' }}
                  onClick={(e) => {
                    e.stopPropagation();
                    handleVendorClick(vendor.id);
                  }}
                >
                  View Vendor Profile <ChevronRight size={14} />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* VIEW MODE 2: CLASSIC TABLE VIEW */}
      {viewMode === 'table' && vendors.length > 0 && (
        <div className="glass-panel" style={{ padding: '24px', overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.88rem' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.1)', color: '#94a3b8', fontSize: '0.75rem' }} className="font-mono">
                <th style={{ padding: '12px 16px' }}>VENDOR NAME</th>
                <th style={{ padding: '12px 16px' }}>TAX ID (TIN)</th>
                <th style={{ padding: '12px 16px' }}>STATUS</th>
                <th style={{ padding: '12px 16px' }}>PURCHASE ORDERS</th>
                <th style={{ padding: '12px 16px' }}>INVOICES BILLED</th>
                <th style={{ padding: '12px 16px', textAlign: 'right' }}>ACTION</th>
              </tr>
            </thead>
            <tbody>
              {vendors.map((vendor) => (
                <tr
                  key={vendor.id}
                  style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.04)', cursor: 'pointer' }}
                  className="table-row-hover"
                  onClick={() => handleVendorClick(vendor.id)}
                >
                  <td style={{ padding: '14px 16px', fontWeight: 700, color: '#f8fafc' }}>{vendor.name}</td>
                  <td style={{ padding: '14px 16px', color: '#38bdf8' }} className="font-mono">{vendor.tax_id || 'N/A'}</td>
                  <td style={{ padding: '14px 16px' }}>
                    <span className="badge badge-success" style={{ fontSize: '0.7rem' }}>✓ APPROVED</span>
                  </td>
                  <td style={{ padding: '14px 16px', fontWeight: 600 }}>{vendor.po_count} POs</td>
                  <td style={{ padding: '14px 16px', fontWeight: 600, color: '#818cf8' }}>{vendor.invoice_count} Invoices</td>
                  <td style={{ padding: '14px 16px', textAlign: 'right' }}>
                    <button
                      className="btn-secondary"
                      style={{ padding: '6px 12px', fontSize: '0.75rem' }}
                      onClick={(e) => {
                        e.stopPropagation();
                        handleVendorClick(vendor.id);
                      }}
                    >
                      View Profile <ChevronRight size={12} />
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
