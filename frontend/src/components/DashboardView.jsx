import React, { useState, useEffect } from 'react';
import {
  LayoutDashboard, FileText, CheckCircle2, ShieldAlert, XCircle, RefreshCw,
  DollarSign, TrendingUp, AlertTriangle, ArrowRight, Upload, Clock, UserCheck, Layers, ChevronRight
} from 'lucide-react';

export default function DashboardView({ onSelectInvoice, onNavigateUpload }) {
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchDashboardSummary = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch('/api/v1/dashboard/summary');
      if (!res.ok) {
        throw new Error('Failed to load dashboard metrics');
      }
      const data = await res.json();
      setSummary(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardSummary();
  }, []);

  if (loading) {
    return (
      <div className="glass-panel" style={{ padding: '48px', textAlign: 'center' }}>
        <div className="animate-spin" style={{ width: '36px', height: '36px', border: '3px solid rgba(99,102,241,0.2)', borderTopColor: '#6366f1', borderRadius: '50%', margin: '0 auto 16px' }} />
        <p style={{ color: '#94a3b8' }}>Loading accounts payable operations dashboard...</p>
      </div>
    );
  }

  if (error || !summary) {
    return (
      <div className="glass-panel" style={{ padding: '32px', textAlign: 'center' }}>
        <div style={{ padding: '24px', background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.3)', borderRadius: '12px', color: '#f87171', maxWidth: '500px', margin: '0 auto' }}>
          <AlertTriangle size={32} style={{ marginBottom: '12px' }} />
          <h3 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '6px' }}>Unable to Load Dashboard Data</h3>
          <p style={{ fontSize: '0.85rem', color: '#fca5a5', marginBottom: '16px' }}>{error || 'Database metric aggregation error.'}</p>
          <button className="btn-primary" onClick={fetchDashboardSummary} style={{ padding: '8px 16px', fontSize: '0.85rem' }}>
            <RefreshCw size={14} /> Retry Loading
          </button>
        </div>
      </div>
    );
  }

  const { invoice_counts, financial_totals, review_metrics, verification_issues, recent_invoices, recent_reviews } = summary;
  const isDbEmpty = invoice_counts.total === 0;

  // Calculate status bar percentage distribution
  const totalInvs = invoice_counts.total || 1;
  const pctApproved = Math.round((invoice_counts.approved / totalInvs) * 100);
  const pctReview = Math.round((invoice_counts.human_review / totalInvs) * 100);
  const pctRejected = Math.round((invoice_counts.rejected / totalInvs) * 100);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Top Header */}
      <div className="glass-panel" style={{ padding: '24px 32px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
          <div style={{ width: '42px', height: '42px', borderRadius: '12px', background: 'rgba(99, 102, 241, 0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <LayoutDashboard size={24} color="#818cf8" />
          </div>
          <div>
            <h1 style={{ fontSize: '1.35rem', fontWeight: 800, color: '#f8fafc', margin: 0 }}>
              Invoice Operations Dashboard
            </h1>
            <p style={{ fontSize: '0.8rem', color: '#94a3b8', marginTop: '2px' }}>
              Real-time accounts payable metrics backed by enterprise SQL queries
            </p>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <button className="btn-secondary" style={{ padding: '8px 14px', fontSize: '0.8rem', display: 'flex', alignItems: 'center', gap: '6px' }} onClick={fetchDashboardSummary}>
            <RefreshCw size={14} className={loading ? 'animate-spin' : ''} /> Refresh Metrics
          </button>
          <button className="btn-primary" style={{ padding: '8px 16px', fontSize: '0.85rem' }} onClick={onNavigateUpload}>
            <Upload size={16} /> Process New Invoice
          </button>
        </div>
      </div>

      {/* Empty State Banner */}
      {isDbEmpty ? (
        <div className="glass-panel" style={{ padding: '48px 32px', textAlign: 'center' }}>
          <div style={{ width: '64px', height: '64px', borderRadius: '50%', background: 'rgba(99, 102, 241, 0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 16px' }}>
            <FileText size={32} color="#818cf8" />
          </div>
          <h2 style={{ fontSize: '1.2rem', fontWeight: 700, marginBottom: '6px' }}>No Invoices Processed Yet</h2>
          <p style={{ fontSize: '0.88rem', color: '#94a3b8', maxWidth: '480px', margin: '0 auto 20px' }}>
            Upload invoice documents (PDF/images) to trigger extraction, deterministic validation, and agentic AI PO verification.
          </p>
          <button className="btn-primary" style={{ padding: '10px 24px', fontSize: '0.9rem' }} onClick={onNavigateUpload}>
            <Upload size={18} /> Upload Your First Invoice
          </button>
        </div>
      ) : (
        <>
          {/* SECTION 1: Operational Status KPI Summary Grid */}
          <div>
            <h3 style={{ fontSize: '0.9rem', fontWeight: 700, color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '12px' }}>
              Operational Status Summary
            </h3>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px' }}>
              {/* Total Invoices */}
              <div className="glass-panel" style={{ padding: '20px', borderLeft: '4px solid #6366f1' }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
                  <span style={{ fontSize: '0.75rem', fontWeight: 600, color: '#94a3b8' }}>TOTAL INVOICES</span>
                  <FileText size={18} color="#818cf8" />
                </div>
                <span style={{ fontSize: '1.8rem', fontWeight: 800, color: '#f8fafc' }}>{invoice_counts.total}</span>
                <span style={{ fontSize: '0.75rem', color: '#64748b', display: 'block', marginTop: '4px' }}>Processed lifetime</span>
              </div>

              {/* Approved */}
              <div className="glass-panel" style={{ padding: '20px', borderLeft: '4px solid #22c55e' }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
                  <span style={{ fontSize: '0.75rem', fontWeight: 600, color: '#94a3b8' }}>APPROVED</span>
                  <CheckCircle2 size={18} color="#4ade80" />
                </div>
                <span style={{ fontSize: '1.8rem', fontWeight: 800, color: '#4ade80' }}>{invoice_counts.approved}</span>
                <span style={{ fontSize: '0.75rem', color: '#4ade80', display: 'block', marginTop: '4px' }}>{pctApproved}% of total</span>
              </div>

              {/* Human Review */}
              <div className="glass-panel" style={{ padding: '20px', borderLeft: '4px solid #f59e0b' }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
                  <span style={{ fontSize: '0.75rem', fontWeight: 600, color: '#94a3b8' }}>HUMAN REVIEW</span>
                  <ShieldAlert size={18} color="#fbbf24" />
                </div>
                <span style={{ fontSize: '1.8rem', fontWeight: 800, color: '#fbbf24' }}>{invoice_counts.human_review}</span>
                <span style={{ fontSize: '0.75rem', color: '#fbbf24', display: 'block', marginTop: '4px' }}>{pctReview}% flagged</span>
              </div>

              {/* Rejected */}
              <div className="glass-panel" style={{ padding: '20px', borderLeft: '4px solid #ef4444' }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
                  <span style={{ fontSize: '0.75rem', fontWeight: 600, color: '#94a3b8' }}>REJECTED</span>
                  <XCircle size={18} color="#f87171" />
                </div>
                <span style={{ fontSize: '1.8rem', fontWeight: 800, color: '#f87171' }}>{invoice_counts.rejected}</span>
                <span style={{ fontSize: '0.75rem', color: '#f87171', display: 'block', marginTop: '4px' }}>{pctRejected}% rejected</span>
              </div>

              {/* Processing */}
              <div className="glass-panel" style={{ padding: '20px', borderLeft: '4px solid #38bdf8' }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
                  <span style={{ fontSize: '0.75rem', fontWeight: 600, color: '#94a3b8' }}>PROCESSING</span>
                  <Clock size={18} color="#38bdf8" />
                </div>
                <span style={{ fontSize: '1.8rem', fontWeight: 800, color: '#38bdf8' }}>{invoice_counts.processing}</span>
                <span style={{ fontSize: '0.75rem', color: '#64748b', display: 'block', marginTop: '4px' }}>In flight runs</span>
              </div>
            </div>
          </div>

          {/* SECTION 2: Financial Overview & Status Distribution Grid */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(420px, 1fr))', gap: '24px' }}>
            
            {/* Financial Overview Card */}
            <div className="glass-panel" style={{ padding: '24px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '16px' }}>
                <TrendingUp size={20} color="#34d399" />
                <h3 style={{ fontSize: '1rem', fontWeight: 700, margin: 0 }}>Financial Monetary Overview</h3>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                <div style={{ background: 'rgba(255,255,255,0.03)', padding: '16px', borderRadius: '12px', border: '1px solid rgba(255,255,255,0.06)' }}>
                  <span style={{ fontSize: '0.75rem', color: '#94a3b8', display: 'block' }}>Total Invoice Billed Value</span>
                  <span style={{ fontSize: '1.4rem', fontWeight: 800, color: '#f8fafc' }}>${financial_totals.total_invoice_value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span>
                </div>

                <div style={{ background: 'rgba(34,197,94,0.08)', padding: '16px', borderRadius: '12px', border: '1px solid rgba(34,197,94,0.2)' }}>
                  <span style={{ fontSize: '0.75rem', color: '#94a3b8', display: 'block' }}>Approved Value</span>
                  <span style={{ fontSize: '1.4rem', fontWeight: 800, color: '#4ade80' }}>${financial_totals.approved_value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span>
                </div>

                <div style={{ background: 'rgba(245,158,11,0.08)', padding: '16px', borderRadius: '12px', border: '1px solid rgba(245,158,11,0.2)' }}>
                  <span style={{ fontSize: '0.75rem', color: '#94a3b8', display: 'block' }}>Review Queue Value</span>
                  <span style={{ fontSize: '1.4rem', fontWeight: 800, color: '#fbbf24' }}>${financial_totals.review_value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span>
                </div>

                <div style={{ background: 'rgba(239,68,68,0.08)', padding: '16px', borderRadius: '12px', border: '1px solid rgba(239,68,68,0.2)' }}>
                  <span style={{ fontSize: '0.75rem', color: '#94a3b8', display: 'block' }}>Rejected Value</span>
                  <span style={{ fontSize: '1.4rem', fontWeight: 800, color: '#f87171' }}>${financial_totals.rejected_value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span>
                </div>
              </div>
            </div>

            {/* Status Distribution Bar & Review Queue Metrics Card */}
            <div className="glass-panel" style={{ padding: '24px', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '16px' }}>
                  <Layers size={20} color="#818cf8" />
                  <h3 style={{ fontSize: '1rem', fontWeight: 700, margin: 0 }}>Invoice Workflow Distribution</h3>
                </div>

                {/* Progress Distribution Bar */}
                <div style={{ height: '14px', borderRadius: '7px', background: 'rgba(255,255,255,0.05)', overflow: 'hidden', display: 'flex', marginBottom: '16px' }}>
                  <div style={{ width: `${pctApproved}%`, background: '#22c55e', transition: 'width 0.5s ease' }} title={`Approved: ${pctApproved}%`} />
                  <div style={{ width: `${pctReview}%`, background: '#f59e0b', transition: 'width 0.5s ease' }} title={`Review Required: ${pctReview}%`} />
                  <div style={{ width: `${pctRejected}%`, background: '#ef4444', transition: 'width 0.5s ease' }} title={`Rejected: ${pctRejected}%`} />
                </div>

                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', color: '#94a3b8' }}>
                  <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}><span style={{ width: '10px', height: '10px', borderRadius: '50%', background: '#22c55e' }} /> Approved ({pctApproved}%)</span>
                  <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}><span style={{ width: '10px', height: '10px', borderRadius: '50%', background: '#f59e0b' }} /> Review ({pctReview}%)</span>
                  <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}><span style={{ width: '10px', height: '10px', borderRadius: '50%', background: '#ef4444' }} /> Rejected ({pctRejected}%)</span>
                </div>
              </div>

              <div style={{ background: 'rgba(244, 63, 94, 0.08)', border: '1px solid rgba(244, 63, 94, 0.2)', padding: '16px', borderRadius: '12px', marginTop: '20px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <div>
                  <span style={{ fontSize: '0.75rem', fontWeight: 600, color: '#f87171' }}>HUMAN REVIEW ACTION REQUIRED</span>
                  <p style={{ fontSize: '0.85rem', color: '#e2e8f0', margin: '2px 0 0' }}>
                    <strong style={{ color: '#f87171' }}>{review_metrics.pending_count} pending review tasks</strong> in queue
                  </p>
                </div>
                <span className="badge badge-warning" style={{ padding: '6px 12px', fontSize: '0.75rem' }}>ACTION NEEDED</span>
              </div>
            </div>
          </div>

          {/* SECTION 3: Verification Issue Summary Breakdown */}
          <div className="glass-panel" style={{ padding: '24px' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <ShieldAlert size={20} color="#fbbf24" />
                <h3 style={{ fontSize: '1rem', fontWeight: 700, margin: 0 }}>Verification Exceptions & Flag Reasons Breakdown</h3>
              </div>
              <span style={{ fontSize: '0.75rem', color: '#64748b' }}>SQL Aggregated Categories</span>
            </div>

            {verification_issues.length === 0 ? (
              <p style={{ color: '#64748b', fontSize: '0.85rem', textAlign: 'center', padding: '16px 0', margin: 0 }}>
                No verification exceptions or flags recorded.
              </p>
            ) : (
              <div style={{ overflowX: 'auto' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
                  <thead>
                    <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.1)', textAlign: 'left', color: '#94a3b8' }}>
                      <th style={{ padding: '10px 14px' }}>FLAG REASON CATEGORY</th>
                      <th style={{ padding: '10px 14px', textAlign: 'center' }}>AFFECTED INVOICES COUNT</th>
                      <th style={{ padding: '10px 14px' }}>IMPACT ASSESSMENT</th>
                    </tr>
                  </thead>
                  <tbody>
                    {verification_issues.map((issue, idx) => (
                      <tr key={idx} style={{ borderBottom: '1px solid rgba(255,255,255,0.04)' }}>
                        <td style={{ padding: '12px 14px', fontWeight: 700, color: '#f87171' }} className="font-mono">
                          {issue.reason}
                        </td>
                        <td style={{ padding: '12px 14px', textAlign: 'center', fontWeight: 700, color: '#fbbf24' }}>
                          {issue.count}
                        </td>
                        <td style={{ padding: '12px 14px', color: '#94a3b8', fontSize: '0.8rem' }}>
                          {issue.reason.includes('QUANTITY') ? 'Invoice quantity exceeds approved Purchase Order limit' :
                           issue.reason.includes('PRICE') ? 'Invoice unit price differs from PO authorization' :
                           issue.reason.includes('VENDOR') ? 'Vendor TIN or registration details not verified in master database' :
                           issue.reason.includes('DUPLICATE') ? 'Identical invoice number previously billed by vendor' :
                           'Requires manual Accounts Payable review'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          {/* SECTION 4 & 5: Recent Invoices Table (Left) vs Recent Review Activity (Right) */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(480px, 1fr))', gap: '24px' }}>
            
            {/* Recent Invoices Table */}
            <div className="glass-panel" style={{ padding: '24px' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <FileText size={20} color="#38bdf8" />
                  <h3 style={{ fontSize: '1rem', fontWeight: 700, margin: 0 }}>Recent Invoices Billed</h3>
                </div>
                <span style={{ fontSize: '0.75rem', color: '#64748b' }}>Latest 10 Invoices</span>
              </div>

              <div style={{ overflowX: 'auto' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
                  <thead>
                    <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.1)', textAlign: 'left', color: '#94a3b8' }}>
                      <th style={{ padding: '10px' }}>Invoice #</th>
                      <th style={{ padding: '10px' }}>Vendor</th>
                      <th style={{ padding: '10px', textAlign: 'right' }}>Total</th>
                      <th style={{ padding: '10px', textAlign: 'center' }}>Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {recent_invoices.length === 0 ? (
                      <tr><td colSpan="4" style={{ textAlign: 'center', padding: '20px', color: '#64748b' }}>No recent invoices</td></tr>
                    ) : (
                      recent_invoices.map((inv) => (
                        <tr
                          key={inv.id}
                          style={{ borderBottom: '1px solid rgba(255,255,255,0.04)', cursor: 'pointer' }}
                          className="table-row-hover"
                          onClick={() => onSelectInvoice && onSelectInvoice(inv.id)}
                        >
                          <td style={{ padding: '10px', fontWeight: 700, color: '#38bdf8' }}>{inv.invoice_number || `Invoice #${inv.id}`}</td>
                          <td style={{ padding: '10px', color: '#e2e8f0' }}>{inv.vendor_name}</td>
                          <td style={{ padding: '10px', textAlign: 'right', fontWeight: 700 }}>${inv.total_amount?.toFixed(2)}</td>
                          <td style={{ padding: '10px', textAlign: 'center' }}>
                            <span className={inv.status === 'APPROVED' ? 'badge badge-success' : inv.status === 'NEEDS_REVIEW' ? 'badge badge-warning' : 'badge badge-danger'} style={{ fontSize: '0.7rem' }}>
                              {inv.status}
                            </span>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Recent Human Review Decision Activity */}
            <div className="glass-panel" style={{ padding: '24px' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <UserCheck size={20} color="#818cf8" />
                  <h3 style={{ fontSize: '1rem', fontWeight: 700, margin: 0 }}>Recent Review Activity</h3>
                </div>
                <span style={{ fontSize: '0.75rem', color: '#64748b' }}>Audit Log</span>
              </div>

              {recent_reviews.length === 0 ? (
                <p style={{ color: '#64748b', fontSize: '0.85rem', textAlign: 'center', padding: '24px 0', margin: 0 }}>
                  No recent human review decisions logged.
                </p>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                  {recent_reviews.map((act) => (
                    <div
                      key={act.id}
                      style={{
                        padding: '12px 16px',
                        borderRadius: '10px',
                        background: 'rgba(255, 255, 255, 0.02)',
                        border: '1px solid rgba(255, 255, 255, 0.06)',
                        cursor: 'pointer'
                      }}
                      className="table-row-hover"
                      onClick={() => onSelectInvoice && onSelectInvoice(act.invoice_id)}
                    >
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '4px' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                          <span className={act.action === 'APPROVED' ? 'badge badge-success' : 'badge badge-danger'} style={{ fontSize: '0.7rem' }}>
                            {act.action}
                          </span>
                          <strong style={{ fontSize: '0.85rem', color: '#38bdf8' }}>{act.invoice_number}</strong>
                        </div>
                        <span style={{ fontSize: '0.75rem', color: '#64748b' }}>
                          {new Date(act.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                        </span>
                      </div>
                      <p style={{ fontSize: '0.8rem', color: '#94a3b8', margin: 0, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                        By <strong>{act.reviewer}</strong>: {act.comment || 'No comment'}
                      </p>
                    </div>
                  ))}
                </div>
              )}
            </div>

          </div>
        </>
      )}
    </div>
  );
}
