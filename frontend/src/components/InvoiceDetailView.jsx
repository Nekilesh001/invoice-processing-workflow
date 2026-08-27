import React, { useState, useEffect } from 'react';
import {
  ArrowLeft, FileText, CheckCircle, AlertTriangle, XCircle, ShieldCheck,
  Building2, Calendar, CreditCard, DollarSign, Layers, Check, X, ChevronDown, ChevronUp, AlertCircle, ExternalLink, Lock
} from 'lucide-react';
import { apiFetch } from '../api';

export default function InvoiceDetailView({ invoiceId, user, onBack, onStatusUpdated }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [actionLoading, setActionLoading] = useState(false);
  const [reviewerName, setReviewerName] = useState(user?.full_name || user?.username || 'Finance Reviewer');
  const [reviewerComment, setReviewerComment] = useState('');
  const [showConfirmModal, setShowConfirmModal] = useState(null); // 'approve' | 'reject' | null
  const [commentError, setCommentError] = useState(null);
  const [showAuditTrail, setShowAuditTrail] = useState(false);

  useEffect(() => {
    if (user?.full_name || user?.username) {
      setReviewerName(user.full_name || user.username);
    }
  }, [user]);

  const fetchInvoiceDetail = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await apiFetch(`/api/v1/invoices/${invoiceId}`);
      if (!res.ok) {
        throw new Error(`Failed to load invoice #${invoiceId}`);
      }
      const json = await res.json();
      setData(json);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (invoiceId) {
      fetchInvoiceDetail();
    }
  }, [invoiceId]);

  const handleReviewAction = async (actionType) => {
    if (!data || !data.review_task) return;

    if (actionType === 'reject' && (!reviewerComment || !reviewerComment.trim())) {
      setCommentError('Reviewer comment is required when rejecting an invoice.');
      return;
    }
    setCommentError(null);
    setActionLoading(true);

    try {
      const endpoint = actionType === 'approve'
        ? `/api/v1/reviews/${data.review_task.id}/approve`
        : `/api/v1/reviews/${data.review_task.id}/reject`;

      const res = await apiFetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          reviewer: reviewerName.trim() || 'Finance Reviewer',
          comment: reviewerComment.trim()
        })
      });

      if (!res.ok) {
        const errJson = await res.json().catch(() => ({}));
        throw new Error(errJson.detail || `Failed to ${actionType} invoice`);
      }

      setShowConfirmModal(null);
      setReviewerComment('');
      await fetchInvoiceDetail();
      if (onStatusUpdated) onStatusUpdated();
    } catch (err) {
      setCommentError(err.message);
    } finally {
      setActionLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="glass-panel" style={{ padding: '48px', textAlign: 'center' }}>
        <div className="animate-spin" style={{ width: '36px', height: '36px', border: '3px solid rgba(6,182,212,0.2)', borderTopColor: '#22d3ee', borderRadius: '50%', margin: '0 auto 16px' }} />
        <p style={{ color: '#94a3b8' }}>Loading verification data for invoice #{invoiceId}...</p>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="glass-panel" style={{ padding: '32px' }}>
        <button className="btn-secondary" style={{ marginBottom: '20px', display: 'flex', alignItems: 'center', gap: '8px' }} onClick={onBack}>
          <ArrowLeft size={16} /> Back to Invoices
        </button>
        <div style={{ padding: '24px', background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.3)', borderRadius: '12px', color: '#f87171' }}>
          <AlertCircle size={24} style={{ marginBottom: '8px' }} />
          <h3 style={{ fontWeight: 600 }}>Error Loading Invoice</h3>
          <p>{error || 'Invoice record not found.'}</p>
        </div>
      </div>
    );
  }

  const isApproved = data.status === 'APPROVED';
  const isNeedsReview = data.status === 'NEEDS_REVIEW' || data.status === 'PENDING';
  const isRejected = data.status === 'REJECTED';

  const poMatch = data.po_match || {};
  const isPoMatch = poMatch.is_match === true;
  const lineResults = poMatch.line_results || [];

  // Real multi-agent assessment data returned by the backend (see BUG-1 / BUG-5 fix).
  // These may be null for older invoices processed before this data was persisted.
  const procurement = data.procurement_assessment || null;
  const risk = data.risk_assessment || null;

  const procurementStatus = procurement?.status || data.procurement_status || 'UNKNOWN';
  const procurementBadgeClass = procurementStatus === 'PASS' ? 'badge-success'
    : procurementStatus === 'FAIL' ? 'badge-danger'
    : 'badge-warning';
  const vendorVerified = procurement ? !!procurement.vendor_verified : !!data.vendor?.name;
  const totalsMatch = procurement ? !procurement.issues?.some(i => /TOTAL|CALC/i.test(i)) : true;
  const duplicateFlagged = risk ? (risk.flags || []).some(f => /DUPLICATE/i.test(f)) : false;

  const riskLevel = risk?.risk_level || 'UNKNOWN';
  const riskBadgeClass = riskLevel === 'LOW' ? 'badge-success' : riskLevel === 'HIGH' ? 'badge-danger' : 'badge-warning';
  const riskHeadline = risk
    ? ((risk.flags && risk.flags.length > 0) ? risk.flags[0].replace(/_/g, ' ') : 'No Anomalies Flagged')
    : 'Risk Data Unavailable';
  const riskSubtext = risk
    ? (risk.flags && risk.flags.length > 0
        ? `${risk.flags.length} flag${risk.flags.length > 1 ? 's' : ''} raised`
        : 'Zero duplicate or amount risk')
    : 'Not assessed for this invoice';

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Top Header & Navigation */}
      <div className="glass-panel" style={{ padding: '24px 32px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <button className="btn-secondary" style={{ padding: '8px 14px', fontSize: '0.85rem', display: 'flex', alignItems: 'center', gap: '6px' }} onClick={onBack}>
            <ArrowLeft size={16} /> Back
          </button>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <h1 style={{ fontSize: '1.4rem', fontWeight: 800, color: '#f8fafc', margin: 0 }}>
                {data.invoice_number || `Invoice #${data.id}`}
              </h1>
              <span style={{
                padding: '4px 12px',
                borderRadius: '9999px',
                fontSize: '0.75rem',
                fontWeight: 700,
                letterSpacing: '0.05em',
                background: isApproved ? 'rgba(34,197,94,0.15)' : isNeedsReview ? 'rgba(245,158,11,0.15)' : 'rgba(239,68,68,0.15)',
                color: isApproved ? '#4ade80' : isNeedsReview ? '#fbbf24' : '#f87171',
                border: `1px solid ${isApproved ? 'rgba(34,197,94,0.3)' : isNeedsReview ? 'rgba(245,158,11,0.3)' : 'rgba(239,68,68,0.3)'}`
              }}>
                {isApproved ? 'APPROVED' : isNeedsReview ? 'HUMAN REVIEW REQUIRED' : isRejected ? 'REJECTED' : data.status}
              </span>
            </div>
            <p style={{ fontSize: '0.85rem', color: '#94a3b8', marginTop: '4px' }}>
              Vendor: <strong style={{ color: '#e2e8f0' }}>{data.vendor?.name || 'Unknown Vendor'}</strong> • Uploaded: {new Date(data.created_at).toLocaleDateString()}
            </p>
          </div>
        </div>

        {/* Human Review Decision Banner Action Buttons */}
        {isNeedsReview && data.review_task && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <button
              className="btn-success"
              disabled={actionLoading}
              onClick={() => { setCommentError(null); setShowConfirmModal('approve'); }}
              style={{ padding: '10px 20px', fontSize: '0.88rem', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '8px', background: '#16a34a', color: '#ffffff', border: 'none', borderRadius: '10px', cursor: 'pointer' }}
            >
              <Check size={18} /> Approve Invoice
            </button>
            <button
              className="btn-danger"
              disabled={actionLoading}
              onClick={() => { setCommentError(null); setShowConfirmModal('reject'); }}
              style={{ padding: '10px 20px', fontSize: '0.88rem', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '8px', background: '#dc2626', color: '#ffffff', border: 'none', borderRadius: '10px', cursor: 'pointer' }}
            >
              <X size={18} /> Reject Invoice
            </button>
          </div>
        )}
      </div>

      {/* Confirmation Modal */}
      {showConfirmModal && (
        <div style={{
          position: 'fixed',
          inset: 0,
          zIndex: 1000,
          background: 'rgba(0, 0, 0, 0.75)',
          backdropFilter: 'blur(6px)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          padding: '24px'
        }}>
          <div className="glass-panel" style={{
            maxWidth: '520px',
            width: '100%',
            padding: '28px',
            background: '#0f172a',
            border: `1px solid ${showConfirmModal === 'approve' ? 'rgba(34, 197, 94, 0.4)' : 'rgba(239, 68, 68, 0.4)'}`,
            borderRadius: '16px',
            boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.5)'
          }}>
            <h3 style={{ fontSize: '1.15rem', fontWeight: 800, marginBottom: '8px', color: showConfirmModal === 'approve' ? '#4ade80' : '#f87171', display: 'flex', alignItems: 'center', gap: '8px' }}>
              {showConfirmModal === 'approve' ? <CheckCircle size={22} /> : <AlertTriangle size={22} />}
              {showConfirmModal === 'approve' ? 'Confirm Invoice Approval' : 'Confirm Invoice Rejection'}
            </h3>
            <p style={{ fontSize: '0.85rem', color: '#94a3b8', marginBottom: '20px' }}>
              {showConfirmModal === 'approve'
                ? 'Approve this invoice and transition database status to APPROVED.'
                : 'Reject this invoice and transition database status to REJECTED. A comment is required.'}
            </p>

            {commentError && (
              <div style={{ padding: '10px 14px', background: 'rgba(239,68,68,0.15)', border: '1px solid rgba(239,68,68,0.3)', borderRadius: '8px', color: '#f87171', fontSize: '0.82rem', marginBottom: '16px' }}>
                {commentError}
              </div>
            )}

            <div style={{ marginBottom: '16px' }}>
              <label style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.75rem', fontWeight: 600, color: '#64748b', marginBottom: '6px' }}>
                <Lock size={12} color="#818cf8" /> REVIEWER IDENTITY (VERIFIED USER)
              </label>
              <div style={{ position: 'relative' }}>
                <input
                  type="text"
                  value={reviewerName}
                  readOnly
                  style={{
                    width: '100%',
                    background: 'rgba(255, 255, 255, 0.03)',
                    border: '1px solid rgba(255, 255, 255, 0.08)',
                    borderRadius: '8px',
                    padding: '8px 12px 8px 34px',
                    color: '#94a3b8',
                    fontSize: '0.85rem',
                    outline: 'none',
                    cursor: 'not-allowed'
                  }}
                />
                <Lock size={14} color="#818cf8" style={{ position: 'absolute', left: '10px', top: '50%', transform: 'translateY(-50%)' }} />
              </div>
            </div>

            <div style={{ marginBottom: '24px' }}>
              <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, color: '#64748b', marginBottom: '6px' }}>
                REVIEWER COMMENT {showConfirmModal === 'reject' && <span style={{ color: '#f87171' }}>* (Required)</span>}
              </label>
              <textarea
                rows="3"
                placeholder={showConfirmModal === 'approve' ? 'Optional notes (e.g. Confirmed discrepancy with procurement)' : 'Enter rejection reason (e.g. Quantity mismatch confirmed with buyer)'}
                value={reviewerComment}
                onChange={e => setReviewerComment(e.target.value)}
                style={{
                  width: '100%',
                  background: 'rgba(255,255,255,0.05)',
                  border: '1px solid rgba(255,255,255,0.1)',
                  borderRadius: '8px',
                  padding: '10px 12px',
                  color: '#ffffff',
                  fontSize: '0.85rem',
                  outline: 'none',
                  resize: 'vertical'
                }}
              />
            </div>

            <div style={{ display: 'flex', gap: '12px', justifyContent: 'flex-end' }}>
              <button
                className="btn-secondary"
                disabled={actionLoading}
                onClick={() => { setShowConfirmModal(null); setCommentError(null); }}
                style={{ padding: '8px 16px', fontSize: '0.85rem' }}
              >
                Cancel
              </button>

              <button
                className={showConfirmModal === 'approve' ? 'btn-success' : 'btn-danger'}
                disabled={actionLoading}
                onClick={() => handleReviewAction(showConfirmModal)}
                style={{
                  padding: '8px 18px',
                  fontSize: '0.85rem',
                  fontWeight: 600,
                  background: showConfirmModal === 'approve' ? '#16a34a' : '#dc2626',
                  color: '#ffffff',
                  border: 'none',
                  borderRadius: '8px',
                  cursor: 'pointer'
                }}
              >
                {actionLoading ? 'Processing...' : showConfirmModal === 'approve' ? 'Confirm Approval' : 'Confirm Rejection'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Main Grid: PDF Preview (Left) vs Business Verification & Details (Right) */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(480px, 1fr))', gap: '24px' }}>
        
        {/* Document Previewer Pane (Image or PDF) */}
        <div className="glass-panel" style={{ padding: '24px', display: 'flex', flexDirection: 'column', height: '100%', minHeight: '650px' }}>
          {(() => {
            const isImg = data.source_filename && (
              data.source_filename.toLowerCase().endsWith('.png') ||
              data.source_filename.toLowerCase().endsWith('.jpg') ||
              data.source_filename.toLowerCase().endsWith('.jpeg') ||
              data.source_filename.toLowerCase().endsWith('.tiff') ||
              data.source_filename.toLowerCase().endsWith('.webp')
            );
            const docUrl = `/api/v1/invoices/${data.id}/document`;

            return (
              <>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px', flexWrap: 'wrap', gap: '8px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <FileText size={20} color="#38bdf8" />
                    <h3 style={{ fontSize: '1rem', fontWeight: 700, margin: 0 }}>
                      Invoice Document {isImg ? 'Image' : 'PDF'}
                    </h3>
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <span style={{ fontSize: '0.75rem', color: '#64748b' }}>{data.source_filename || 'Document Preview'}</span>
                    <a
                      href={docUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="btn-secondary"
                      style={{ padding: '4px 10px', fontSize: '0.75rem', textDecoration: 'none', display: 'inline-flex', alignItems: 'center', gap: '4px', color: '#38bdf8', borderColor: 'rgba(56,189,248,0.3)' }}
                    >
                      <ExternalLink size={12} /> {isImg ? 'Open Image' : 'Open PDF'}
                    </a>
                  </div>
                </div>

                <div style={{ flex: 1, borderRadius: '12px', overflow: 'hidden', background: '#0f172a', border: '1px solid rgba(255,255,255,0.08)', position: 'relative', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  {isImg ? (
                    <div style={{ width: '100%', height: '100%', minHeight: '600px', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '16px', background: '#090d16' }}>
                      <img
                        src={docUrl}
                        alt={data.source_filename || "Invoice Document Image"}
                        style={{ maxWidth: '100%', maxHeight: '600px', objectFit: 'contain', borderRadius: '8px', boxShadow: '0 8px 30px rgba(0,0,0,0.6)' }}
                      />
                    </div>
                  ) : (
                    <object
                      data={`${docUrl}#toolbar=0`}
                      type="application/pdf"
                      style={{ width: '100%', height: '100%', minHeight: '600px' }}
                    >
                      <iframe
                        src={`${docUrl}#toolbar=0`}
                        title="Invoice PDF Preview"
                        style={{ width: '100%', height: '100%', minHeight: '600px', border: 'none' }}
                      >
                        <div style={{ padding: '32px', textAlign: 'center', color: '#94a3b8' }}>
                          <FileText size={40} color="#38bdf8" style={{ marginBottom: '12px' }} />
                          <p>Your browser is unable to display PDF inline.</p>
                          <a
                            href={docUrl}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="btn-primary"
                            style={{ marginTop: '12px', display: 'inline-flex' }}
                          >
                            Download / View Document PDF
                          </a>
                        </div>
                      </iframe>
                    </object>
                  )}
                </div>
              </>
            );
          })()}
        </div>

        {/* Verification Summary & Extracted Financials Pane */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          
          {/* Multi-Agent Business Verification Summary */}
          <div className="glass-panel" style={{ padding: '24px' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '20px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <ShieldCheck size={22} color="#4ade80" />
                <h3 style={{ fontSize: '1.1rem', fontWeight: 700, margin: 0 }}>Multi-Agent Verification Summary</h3>
              </div>
              <span className="badge badge-info" style={{ fontSize: '0.7rem' }}>
                Procurement + Risk + Policy Engine
              </span>
            </div>

            {/* Specialist Agent Cards */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '12px', marginBottom: '16px' }}>
              {/* Procurement Agent Card */}
              <div style={{ padding: '12px 14px', borderRadius: '10px', background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.08)' }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '6px' }}>
                  <span style={{ fontSize: '0.72rem', fontWeight: 700, color: '#94a3b8' }}>PROCUREMENT AGENT</span>
                  <span className={`badge ${procurementBadgeClass}`} style={{ fontSize: '0.65rem' }}>
                    {procurementStatus}
                  </span>
                </div>
                <span style={{ fontSize: '0.82rem', fontWeight: 600, color: '#f8fafc', display: 'block' }}>
                  {vendorVerified ? 'Vendor Verified' : 'Unknown Vendor'}
                </span>
                <span style={{ fontSize: '0.73rem', color: '#64748b' }}>
                  {data.po_number ? (isPoMatch ? 'PO Lines Matched' : 'PO Line Mismatch') : 'No PO Reference'}
                </span>
              </div>

              {/* Financial Risk Agent Card */}
              <div style={{ padding: '12px 14px', borderRadius: '10px', background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.08)' }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '6px' }}>
                  <span style={{ fontSize: '0.72rem', fontWeight: 700, color: '#94a3b8' }}>FINANCIAL RISK AGENT</span>
                  <span className={`badge ${riskBadgeClass}`} style={{ fontSize: '0.65rem' }}>
                    {riskLevel} RISK
                  </span>
                </div>
                <span style={{ fontSize: '0.82rem', fontWeight: 600, color: riskLevel === 'LOW' ? '#4ade80' : '#f8fafc', display: 'block', textTransform: 'capitalize' }}>
                  {riskHeadline.toLowerCase()}
                </span>
                <span style={{ fontSize: '0.73rem', color: '#64748b' }}>
                  {riskSubtext}
                </span>
              </div>

              {/* Final Policy Card */}
              <div style={{ padding: '12px 14px', borderRadius: '10px', background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.08)' }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '6px' }}>
                  <span style={{ fontSize: '0.72rem', fontWeight: 700, color: '#94a3b8' }}>APPROVAL POLICY</span>
                  <span className={`badge ${data.status === 'APPROVED' ? 'badge-success' : 'badge-warning'}`} style={{ fontSize: '0.65rem' }}>
                    {data.status === 'APPROVED' ? 'AUTO_PROCESS' : 'HUMAN_REVIEW'}
                  </span>
                </div>
                <span style={{ fontSize: '0.82rem', fontWeight: 600, color: '#f8fafc', display: 'block' }}>
                  {data.status === 'APPROVED' ? 'Approved by Policy' : 'Routed to Review'}
                </span>
                <span style={{ fontSize: '0.73rem', color: '#64748b' }}>
                  Deterministic Safety Engine
                </span>
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '12px' }}>
              <VerificationItem
                label="Vendor Verified"
                passed={vendorVerified}
                detail={vendorVerified ? `Master Registry: ${data.vendor?.name || ''}` : 'Unknown Vendor'}
              />
              <VerificationItem
                label="Duplicate Check"
                passed={!duplicateFlagged}
                detail={duplicateFlagged ? 'Possible duplicate invoice detected' : 'No identical invoice found'}
              />
              <VerificationItem
                label="Calculations Valid"
                passed={totalsMatch}
                detail={totalsMatch ? 'Subtotal + Tax = Total' : (procurement?.issues?.find(i => /TOTAL|CALC/i.test(i)) || 'Totals mismatch detected')}
              />
              <VerificationItem
                label="Purchase Order"
                passed={!!data.po_number && poMatch.overall_status !== 'PO_NOT_FOUND'}
                detail={data.po_number ? `Verified ${data.po_number}` : 'No PO Reference'}
              />
              <VerificationItem
                label="Line Items Match"
                passed={isPoMatch}
                detail={isPoMatch ? 'All lines match PO' : poMatch.reasons?.[0] || 'Line mismatch detected'}
              />
            </div>
          </div>

          {/* Invoice Summary Card */}
          <div className="glass-panel" style={{ padding: '24px' }}>
            <h3 style={{ fontSize: '1rem', fontWeight: 700, marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Building2 size={18} color="#94a3b8" /> Financial & Header Summary
            </h3>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '16px', fontSize: '0.88rem' }}>
              <div>
                <span style={{ color: '#64748b', fontSize: '0.75rem', display: 'block' }}>Vendor Name</span>
                <strong>{data.vendor?.name || 'N/A'}</strong>
              </div>
              <div>
                <span style={{ color: '#64748b', fontSize: '0.75rem', display: 'block' }}>Tax ID</span>
                <strong>{data.vendor?.tax_id || 'N/A'}</strong>
              </div>
              <div>
                <span style={{ color: '#64748b', fontSize: '0.75rem', display: 'block' }}>Invoice Date</span>
                <strong>{data.invoice_date || 'N/A'}</strong>
              </div>
              <div>
                <span style={{ color: '#64748b', fontSize: '0.75rem', display: 'block' }}>Due Date</span>
                <strong>{data.due_date || 'N/A'}</strong>
              </div>
              <div>
                <span style={{ color: '#64748b', fontSize: '0.75rem', display: 'block' }}>PO Reference</span>
                <strong>{data.po_number || 'None'}</strong>
              </div>
              <div>
                <span style={{ color: '#64748b', fontSize: '0.75rem', display: 'block' }}>Currency</span>
                <strong>{data.currency || 'USD'}</strong>
              </div>
            </div>

            <div style={{ marginTop: '20px', paddingTop: '16px', borderTop: '1px solid rgba(255,255,255,0.08)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <span style={{ color: '#94a3b8', fontSize: '0.8rem' }}>Subtotal: ${data.subtotal?.toFixed(2) || '0.00'}</span>
                <span style={{ color: '#94a3b8', fontSize: '0.8rem', marginLeft: '16px' }}>Tax: ${data.tax_amount?.toFixed(2) || '0.00'}</span>
              </div>
              <div style={{ textAlign: 'right' }}>
                <span style={{ color: '#64748b', fontSize: '0.75rem', display: 'block' }}>Total Claimed</span>
                <span style={{ fontSize: '1.4rem', fontWeight: 800, color: '#38bdf8' }}>${data.total_amount?.toFixed(2) || '0.00'}</span>
              </div>
            </div>
          </div>

          {/* Mismatch Evidence Banner (if review required) */}
          {(!isPoMatch || isNeedsReview) && (
            <div style={{ padding: '20px', background: 'rgba(245,158,11,0.1)', border: '1px solid rgba(245,158,11,0.3)', borderRadius: '16px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '8px', color: '#fbbf24' }}>
                <AlertTriangle size={20} />
                <h4 style={{ fontWeight: 700, margin: 0 }}>Human Review Attention Required</h4>
              </div>
              <p style={{ fontSize: '0.88rem', color: '#fcd34d', margin: 0 }}>
                {data.review_task?.reason || poMatch.reasons?.[0] || 'Verification discrepancy identified during automated invoice checks.'}
              </p>
            </div>
          )}

        </div>
      </div>

      {/* Line-Item Comparison Section */}
      <div className="glass-panel" style={{ padding: '28px' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <Layers size={22} color="#38bdf8" />
            <div>
              <h3 style={{ fontSize: '1.1rem', fontWeight: 700, margin: 0 }}>Invoice vs Purchase Order Line-Item Matching</h3>
              <p style={{ fontSize: '0.8rem', color: '#94a3b8', margin: 0 }}>Deterministic line arithmetic comparison</p>
            </div>
          </div>

          <span style={{
            padding: '6px 14px',
            borderRadius: '9999px',
            fontSize: '0.8rem',
            fontWeight: 700,
            background: isPoMatch ? 'rgba(34,197,94,0.15)' : 'rgba(239,68,68,0.15)',
            color: isPoMatch ? '#4ade80' : '#f87171'
          }}>
            {isPoMatch ? '✓ ALL LINES MATCH' : '⚠ LINE MISMATCH DETECTED'}
          </span>
        </div>

        {/* Comparison Table */}
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.1)', textAlign: 'left', color: '#94a3b8' }}>
                <th style={{ padding: '12px' }}>Invoice Description</th>
                <th style={{ padding: '12px', textAlign: 'right' }}>Inv Qty</th>
                <th style={{ padding: '12px', textAlign: 'right' }}>Inv Price</th>
                <th style={{ padding: '12px' }}>PO Item Reference</th>
                <th style={{ padding: '12px', textAlign: 'right' }}>PO Qty</th>
                <th style={{ padding: '12px', textAlign: 'right' }}>PO Price</th>
                <th style={{ padding: '12px', textAlign: 'center' }}>Match Status</th>
              </tr>
            </thead>
            <tbody>
              {lineResults.length > 0 ? (
                lineResults.map((line, idx) => (
                  <tr key={idx} style={{ borderBottom: '1px solid rgba(255,255,255,0.05)', background: line.status !== 'MATCH' ? 'rgba(239,68,68,0.05)' : 'transparent' }}>
                    <td style={{ padding: '12px', fontWeight: 600 }}>{line.invoice_description || 'N/A'}</td>
                    <td style={{ padding: '12px', textAlign: 'right' }}>{line.invoice_quantity}</td>
                    <td style={{ padding: '12px', textAlign: 'right' }}>${line.invoice_unit_price?.toFixed(2)}</td>
                    <td style={{ padding: '12px', color: '#94a3b8' }}>{line.po_description || 'N/A'}</td>
                    <td style={{ padding: '12px', textAlign: 'right', color: line.quantity_difference > 0 ? '#f87171' : 'inherit' }}>{line.po_quantity}</td>
                    <td style={{ padding: '12px', textAlign: 'right', color: line.unit_price_difference > 0 ? '#f87171' : 'inherit' }}>${line.po_unit_price?.toFixed(2)}</td>
                    <td style={{ padding: '12px', textAlign: 'center' }}>
                      <LineStatusBadge status={line.status} />
                    </td>
                  </tr>
                ))
              ) : (
                (data.line_items || []).map((item, idx) => (
                  <tr key={idx} style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                    <td style={{ padding: '12px', fontWeight: 600 }}>{item.description}</td>
                    <td style={{ padding: '12px', textAlign: 'right' }}>{item.quantity}</td>
                    <td style={{ padding: '12px', textAlign: 'right' }}>${item.unit_price?.toFixed(2)}</td>
                    <td style={{ padding: '12px', color: '#64748b' }}>No PO Linked</td>
                    <td style={{ padding: '12px', textAlign: 'right', color: '#64748b' }}>-</td>
                    <td style={{ padding: '12px', textAlign: 'right', color: '#64748b' }}>-</td>
                    <td style={{ padding: '12px', textAlign: 'center' }}>
                      <span style={{ fontSize: '0.75rem', color: '#94a3b8' }}>N/A</span>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Review Decision History Timeline Panel */}
      <div className="glass-panel" style={{ padding: '24px' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <ShieldCheck size={20} color="#818cf8" />
            <h3 style={{ fontSize: '1rem', fontWeight: 700, margin: 0 }}>Human Review Decision History & Audit Trail</h3>
          </div>
          <span style={{ fontSize: '0.75rem', color: '#64748b' }}>
            {(data.review_history || []).length} Decision Record(s)
          </span>
        </div>

        {(data.review_history || []).length === 0 ? (
          <p style={{ color: '#64748b', fontSize: '0.85rem', textAlign: 'center', padding: '16px 0', margin: 0 }}>
            No human review actions have been taken on this invoice yet.
          </p>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            {data.review_history.map((item) => (
              <div key={item.id} style={{
                padding: '16px 20px',
                borderRadius: '12px',
                background: item.action === 'APPROVED' ? 'rgba(34, 197, 94, 0.06)' : 'rgba(239, 68, 68, 0.06)',
                border: `1px solid ${item.action === 'APPROVED' ? 'rgba(34, 197, 94, 0.2)' : 'rgba(239, 68, 68, 0.2)'}`
              }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px', flexWrap: 'wrap', gap: '8px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <span style={{
                      padding: '3px 10px',
                      borderRadius: '6px',
                      fontSize: '0.75rem',
                      fontWeight: 700,
                      background: item.action === 'APPROVED' ? '#16a34a' : '#dc2626',
                      color: '#ffffff'
                    }}>
                      {item.action}
                    </span>
                    <strong style={{ fontSize: '0.88rem', color: '#f8fafc' }}>{item.reviewer}</strong>
                    <span style={{ fontSize: '0.75rem', color: '#64748b' }}>
                      ({item.previous_status} → {item.new_status})
                    </span>
                  </div>

                  <span style={{ fontSize: '0.78rem', color: '#94a3b8' }}>
                    {new Date(item.created_at).toLocaleString()}
                  </span>
                </div>

                {item.comment ? (
                  <p style={{ fontSize: '0.85rem', color: '#e2e8f0', margin: '6px 0 0', fontStyle: 'italic', background: 'rgba(0, 0, 0, 0.2)', padding: '10px 14px', borderRadius: '8px' }}>
                    "{item.comment}"
                  </p>
                ) : (
                  <p style={{ fontSize: '0.8rem', color: '#64748b', margin: '4px 0 0', fontStyle: 'italic' }}>
                    No notes provided for approval.
                  </p>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Collapsible Technical Audit Trail */}
      <div className="glass-panel" style={{ padding: '20px 28px' }}>
        <button
          onClick={() => setShowAuditTrail(!showAuditTrail)}
          style={{ width: '100%', background: 'none', border: 'none', color: '#94a3b8', display: 'flex', alignItems: 'center', justifyContent: 'space-between', cursor: 'pointer', fontSize: '0.9rem', fontWeight: 600 }}
        >
          <span>Processing Audit Details & Technical Verification Log</span>
          {showAuditTrail ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
        </button>

        {showAuditTrail && (
          <div style={{ marginTop: '16px', paddingTop: '16px', borderTop: '1px solid rgba(255,255,255,0.08)', fontSize: '0.85rem' }}>
            <p style={{ color: '#64748b', fontSize: '0.8rem', marginBottom: '12px' }}>
              Observable system verification trace (Tool executions & deterministic checks)
            </p>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              <AuditLogStep title="Document Extracted" detail={`File: ${data.source_filename}`} status="DONE" />
              <AuditLogStep
                title="Deterministic Math Validation"
                detail={totalsMatch ? 'Subtotal + Tax = Total Verified' : (procurement?.issues?.find(i => /TOTAL|CALC/i.test(i)) || 'Totals mismatch detected')}
                status={totalsMatch ? 'PASSED' : 'FAILED'}
              />
              <AuditLogStep
                title="Tool: lookup_vendor"
                detail={`Vendor: ${data.vendor?.name || 'N/A'}${procurement ? (vendorVerified ? ' (verified)' : ' (not found in registry)') : ''}`}
                status={procurement ? 'EXECUTED' : 'NOT RECORDED'}
              />
              {data.po_number && <AuditLogStep title="Tool: lookup_purchase_order" detail={`PO: ${data.po_number}`} status={procurement ? 'EXECUTED' : 'NOT RECORDED'} />}
              {data.po_number && <AuditLogStep title="Tool: compare_invoice_to_purchase_order" detail={`Line match status: ${poMatch.overall_status || 'N/A'}`} status={poMatch.overall_status ? 'EXECUTED' : 'NOT RECORDED'} />}
              {risk && <AuditLogStep title="Tool: financial risk checks" detail={risk.flags?.length ? `Flags: ${risk.flags.join(', ')}` : 'No risk flags raised'} status="EXECUTED" />}
              <p style={{ color: '#64748b', fontSize: '0.72rem', marginTop: '4px', fontStyle: 'italic' }}>
                Full per-tool argument/output trace is available on the Agent Trace tab immediately after upload (not yet persisted for historical invoices).
              </p>
            </div>
          </div>
        )}
      </div>

    </div>
  );
}

function VerificationItem({ label, passed, detail }) {
  return (
    <div style={{
      padding: '14px',
      borderRadius: '12px',
      background: passed ? 'rgba(34,197,94,0.05)' : 'rgba(239,68,68,0.05)',
      border: `1px solid ${passed ? 'rgba(34,197,94,0.2)' : 'rgba(239,68,68,0.2)'}`
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
        {passed ? <CheckCircle size={16} color="#4ade80" /> : <XCircle size={16} color="#f87171" />}
        <span style={{ fontWeight: 600, fontSize: '0.85rem', color: passed ? '#4ade80' : '#f87171' }}>{label}</span>
      </div>
      <span style={{ fontSize: '0.75rem', color: '#94a3b8', display: 'block' }}>{detail}</span>
    </div>
  );
}

function LineStatusBadge({ status }) {
  const isMatch = status === 'MATCH';
  return (
    <span style={{
      padding: '3px 8px',
      borderRadius: '6px',
      fontSize: '0.7rem',
      fontWeight: 700,
      background: isMatch ? 'rgba(34,197,94,0.15)' : 'rgba(239,68,68,0.15)',
      color: isMatch ? '#4ade80' : '#f87171'
    }}>
      {status}
    </span>
  );
}

function AuditLogStep({ title, detail, status }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '8px 12px', background: 'rgba(255,255,255,0.02)', borderRadius: '8px' }}>
      <span style={{ fontWeight: 500, color: '#e2e8f0' }}>{title}</span>
      <span style={{ color: '#94a3b8', fontSize: '0.8rem' }}>{detail}</span>
    </div>
  );
}
