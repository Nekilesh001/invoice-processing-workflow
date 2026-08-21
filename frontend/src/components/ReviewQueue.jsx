import React, { useState, useEffect } from 'react';
import { ShieldAlert, CheckCircle2, XCircle, AlertTriangle, RefreshCw, UserCheck, Code, LayoutGrid, DollarSign, Calendar, FileText, Building } from 'lucide-react';

export default function ReviewQueue({ onCountChange }) {
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(null);
  const [viewModes, setViewModes] = useState({}); // { [taskId]: 'data' | 'json' }

  const fetchTasks = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/v1/reviews?status=PENDING');
      if (res.ok) {
        const data = await res.json();
        setTasks(data);
        if (onCountChange) onCountChange(data.length);
      }
    } catch (e) {
      console.error('Failed to fetch review tasks', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTasks();
  }, []);

  const handleAction = async (taskId, action) => {
    setActionLoading(taskId);
    try {
      const endpoint = action === 'approve'
        ? `/api/v1/reviews/${taskId}/approve`
        : `/api/v1/reviews/${taskId}/reject`;

      const res = await fetch(endpoint, { method: 'POST' });
      if (res.ok) {
        await fetchTasks();
      }
    } catch (e) {
      console.error(`Failed to ${action} task`, e);
    } finally {
      setActionLoading(null);
    }
  };

  const toggleViewMode = (taskId, mode) => {
    setViewModes(prev => ({ ...prev, [taskId]: mode }));
  };

  return (
    <div className="glass-panel" style={{ padding: '32px' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '24px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{ width: '40px', height: '40px', borderRadius: '12px', background: 'rgba(244, 63, 94, 0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <ShieldAlert size={22} color="#f43f5e" />
          </div>
          <div>
            <h2 style={{ fontSize: '1.2rem', fontWeight: 700 }}>Human-in-the-Loop Review Queue</h2>
            <p style={{ fontSize: '0.8rem', color: '#94a3b8' }}>Flagged invoices requiring human verification before approval</p>
          </div>
        </div>

        <button className="btn-secondary" style={{ padding: '8px 14px', fontSize: '0.8rem', display: 'flex', alignItems: 'center', gap: '6px' }} onClick={fetchTasks}>
          <RefreshCw size={14} className={loading ? 'animate-spin' : ''} /> Refresh Queue
        </button>
      </div>

      {tasks.length === 0 && !loading && (
        <div style={{ height: '260px', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', color: '#34d399', textAlign: 'center' }}>
          <UserCheck size={52} style={{ opacity: 0.85, marginBottom: '16px' }} />
          <h3 style={{ fontSize: '1.1rem', fontWeight: 600, marginBottom: '4px' }}>Review Queue Empty</h3>
          <p style={{ fontSize: '0.85rem', color: '#94a3b8' }}>All processed invoices are verified and approved.</p>
        </div>
      )}

      <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
        {tasks.map((task) => {
          const currentMode = viewModes[task.id] || 'data';

          return (
            <div key={task.id} className="glass-panel" style={{
              border: '1px solid rgba(244, 63, 94, 0.3)',
              borderRadius: '16px',
              padding: '24px',
              background: 'rgba(15, 23, 42, 0.7)'
            }}>
              {/* Header Bar */}
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '18px', borderBottom: '1px solid rgba(255, 255, 255, 0.08)', paddingBottom: '14px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                  <span className="font-mono" style={{ background: 'rgba(244, 63, 94, 0.2)', color: '#f87171', padding: '4px 10px', borderRadius: '8px', fontSize: '0.85rem', fontWeight: 700 }}>
                    TASK #{task.id}
                  </span>
                  <span style={{ fontSize: '1rem', fontWeight: 700, color: '#ffffff' }}>
                    Invoice: <span className="font-mono" style={{ color: '#38bdf8' }}>{task.invoice_number}</span>
                  </span>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                  {/* View Mode Switcher */}
                  <div style={{ display: 'flex', background: 'rgba(255, 255, 255, 0.05)', padding: '3px', borderRadius: '8px', border: '1px solid rgba(255, 255, 255, 0.1)' }}>
                    <button
                      style={{
                        padding: '4px 10px',
                        fontSize: '0.75rem',
                        fontWeight: 600,
                        borderRadius: '6px',
                        border: 'none',
                        cursor: 'pointer',
                        background: currentMode === 'data' ? '#6366f1' : 'transparent',
                        color: currentMode === 'data' ? '#ffffff' : '#94a3b8',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '4px'
                      }}
                      onClick={() => toggleViewMode(task.id, 'data')}
                    >
                      <LayoutGrid size={12} /> Data Boxes
                    </button>
                    <button
                      style={{
                        padding: '4px 10px',
                        fontSize: '0.75rem',
                        fontWeight: 600,
                        borderRadius: '6px',
                        border: 'none',
                        cursor: 'pointer',
                        background: currentMode === 'json' ? '#6366f1' : 'transparent',
                        color: currentMode === 'json' ? '#ffffff' : '#94a3b8',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '4px'
                      }}
                      onClick={() => toggleViewMode(task.id, 'json')}
                    >
                      <Code size={12} /> Raw JSON
                    </button>
                  </div>

                  <span className="badge badge-warning" style={{ padding: '6px 12px', fontSize: '0.75rem' }}>
                    <AlertTriangle size={14} /> {task.status}
                  </span>
                </div>
              </div>

              {/* FLAGGED REASON WARNING CARD */}
              <div style={{
                background: 'rgba(245, 158, 11, 0.1)',
                border: '1px solid rgba(245, 158, 11, 0.3)',
                borderRadius: '12px',
                padding: '14px 18px',
                marginBottom: '20px',
                display: 'flex',
                alignItems: 'center',
                gap: '12px'
              }}>
                <AlertTriangle size={20} color="#fbbf24" style={{ flexShrink: 0 }} />
                <div>
                  <div style={{ fontSize: '0.8rem', fontWeight: 700, color: '#fbbf24', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                    FLAGGED FOR HUMAN REVIEW
                  </div>
                  <div style={{ fontSize: '0.9rem', color: '#fef08a', marginTop: '2px', fontWeight: 500 }}>
                    {task.reason}
                  </div>
                </div>
              </div>

              {/* MODE 1: STRUCTURED DATA BOXES VIEW */}
              {currentMode === 'data' && (
                <div>
                  {/* Extracted Header Fields Grid */}
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '14px', marginBottom: '20px' }}>
                    <div style={{ background: 'rgba(255, 255, 255, 0.03)', padding: '12px 14px', borderRadius: '10px', border: '1px solid rgba(255, 255, 255, 0.06)' }}>
                      <div style={{ fontSize: '0.7rem', color: '#94a3b8', display: 'flex', alignItems: 'center', gap: '4px' }}>
                        <Building size={12} /> VENDOR NAME
                      </div>
                      <div style={{ fontSize: '0.92rem', fontWeight: 600, marginTop: '4px', color: '#ffffff' }}>
                        {task.vendor_name}
                      </div>
                    </div>

                    <div style={{ background: 'rgba(255, 255, 255, 0.03)', padding: '12px 14px', borderRadius: '10px', border: '1px solid rgba(255, 255, 255, 0.06)' }}>
                      <div style={{ fontSize: '0.7rem', color: '#94a3b8', display: 'flex', alignItems: 'center', gap: '4px' }}>
                        <FileText size={12} /> PO NUMBER
                      </div>
                      <div style={{ fontSize: '0.92rem', fontWeight: 600, marginTop: '4px', color: task.po_number ? '#34d399' : '#94a3b8' }} className="font-mono">
                        {task.po_number || 'NONE'}
                      </div>
                    </div>

                    <div style={{ background: 'rgba(255, 255, 255, 0.03)', padding: '12px 14px', borderRadius: '10px', border: '1px solid rgba(255, 255, 255, 0.06)' }}>
                      <div style={{ fontSize: '0.7rem', color: '#94a3b8', display: 'flex', alignItems: 'center', gap: '4px' }}>
                        <DollarSign size={12} /> TOTAL AMOUNT
                      </div>
                      <div style={{ fontSize: '1.05rem', fontWeight: 700, marginTop: '4px', color: '#818cf8' }}>
                        ${task.total_amount?.toFixed(2)} ({task.currency})
                      </div>
                    </div>

                    <div style={{ background: 'rgba(255, 255, 255, 0.03)', padding: '12px 14px', borderRadius: '10px', border: '1px solid rgba(255, 255, 255, 0.06)' }}>
                      <div style={{ fontSize: '0.7rem', color: '#94a3b8', display: 'flex', alignItems: 'center', gap: '4px' }}>
                        <Calendar size={12} /> INVOICE DATE
                      </div>
                      <div style={{ fontSize: '0.92rem', fontWeight: 600, marginTop: '4px', color: '#ffffff' }} className="font-mono">
                        {task.invoice_date || 'Missing'}
                      </div>
                    </div>

                    <div style={{ background: 'rgba(255, 255, 255, 0.03)', padding: '12px 14px', borderRadius: '10px', border: '1px solid rgba(255, 255, 255, 0.06)' }}>
                      <div style={{ fontSize: '0.7rem', color: '#94a3b8', display: 'flex', alignItems: 'center', gap: '4px' }}>
                        <Calendar size={12} /> DUE DATE
                      </div>
                      <div style={{ fontSize: '0.92rem', fontWeight: 600, marginTop: '4px', color: task.due_date ? '#ffffff' : '#f87171' }} className="font-mono">
                        {task.due_date || '⚠️ MISSING DUE DATE'}
                      </div>
                    </div>
                  </div>

                  {/* Extracted Line Items Table */}
                  {task.line_items && task.line_items.length > 0 && (
                    <div style={{ marginBottom: '20px' }}>
                      <div style={{ fontSize: '0.75rem', fontWeight: 600, color: '#94a3b8', marginBottom: '8px' }}>
                        EXTRACTED LINE ITEMS ({task.line_items.length})
                      </div>
                      <div style={{ background: 'rgba(0, 0, 0, 0.3)', borderRadius: '10px', padding: '12px', border: '1px solid rgba(255, 255, 255, 0.06)' }}>
                        <table style={{ width: '100%', fontSize: '0.82rem', borderCollapse: 'collapse' }}>
                          <thead>
                            <tr style={{ color: '#64748b', textAlign: 'left', borderBottom: '1px solid rgba(255, 255, 255, 0.08)' }}>
                              <th style={{ padding: '6px 8px' }}>DESCRIPTION</th>
                              <th style={{ padding: '6px 8px' }}>QTY</th>
                              <th style={{ padding: '6px 8px' }}>UNIT PRICE</th>
                              <th style={{ padding: '6px 8px', textAlign: 'right' }}>LINE TOTAL</th>
                            </tr>
                          </thead>
                          <tbody>
                            {task.line_items.map((item, idx) => (
                              <tr key={idx} style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.04)' }}>
                                <td style={{ padding: '8px', color: '#e2e8f0' }}>{item.description}</td>
                                <td style={{ padding: '8px', color: '#94a3b8' }} className="font-mono">{item.quantity}</td>
                                <td style={{ padding: '8px', color: '#94a3b8' }} className="font-mono">${item.unit_price?.toFixed(2)}</td>
                                <td style={{ padding: '8px', textAlign: 'right', fontWeight: 600, color: '#38bdf8' }} className="font-mono">
                                  ${item.line_total?.toFixed(2)}
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  )}

                  {/* Validation Error Rules */}
                  {task.validation_records && task.validation_records.length > 0 && task.validation_records[0].errors?.length > 0 && (
                    <div style={{ background: 'rgba(244, 63, 94, 0.08)', border: '1px solid rgba(244, 63, 94, 0.2)', padding: '12px 16px', borderRadius: '10px', marginBottom: '20px' }}>
                      <div style={{ fontSize: '0.75rem', fontWeight: 700, color: '#f87171', marginBottom: '6px' }}>
                        DETERMINISTIC VALIDATION ERRORS
                      </div>
                      {task.validation_records[0].errors.map((err, i) => (
                        <div key={i} style={{ fontSize: '0.82rem', color: '#fca5a5', display: 'flex', alignItems: 'center', gap: '6px', marginTop: '4px' }}>
                          • <strong>[{err.rule_name}]</strong>: {err.message}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {/* MODE 2: RAW JSON PAYLOAD VIEW */}
              {currentMode === 'json' && (
                <div style={{
                  background: 'rgba(0, 0, 0, 0.55)',
                  border: '1px solid rgba(255, 255, 255, 0.1)',
                  borderRadius: '12px',
                  padding: '16px',
                  marginBottom: '20px'
                }}>
                  <div style={{ fontSize: '0.75rem', color: '#94a3b8', marginBottom: '8px', display: 'flex', alignItems: 'center', justifyBetween: 'space-between' }}>
                    <span>FULL EXTRACTED INVOICE JSON PAYLOAD</span>
                  </div>
                  <pre style={{ fontSize: '0.78rem', color: '#38bdf8', whiteSpace: 'pre-wrap', maxHeight: '300px', overflowY: 'auto' }} className="font-mono">
                    {JSON.stringify(task.raw_json || {}, null, 2)}
                  </pre>
                </div>
              )}

              {/* Action Buttons */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', borderTop: '1px solid rgba(255, 255, 255, 0.08)', paddingTop: '18px' }}>
                <button
                  className="btn-primary"
                  style={{ background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)', justifyContent: 'center', padding: '12px', fontSize: '0.92rem' }}
                  onClick={() => handleAction(task.id, 'approve')}
                  disabled={actionLoading === task.id}
                >
                  <CheckCircle2 size={18} /> Approve Invoice
                </button>

                <button
                  className="btn-secondary"
                  style={{ background: 'rgba(244, 63, 94, 0.15)', color: '#f87171', borderColor: 'rgba(244, 63, 94, 0.3)', justifyContent: 'center', padding: '12px', fontSize: '0.92rem' }}
                  onClick={() => handleAction(task.id, 'reject')}
                  disabled={actionLoading === task.id}
                >
                  <XCircle size={18} /> Reject Invoice
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
