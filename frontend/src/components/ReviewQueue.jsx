import React, { useState, useEffect } from 'react';
import { ShieldAlert, CheckCircle2, XCircle, AlertTriangle, RefreshCw, UserCheck } from 'lucide-react';

export default function ReviewQueue({ onCountChange }) {
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(null);

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

  return (
    <div className="glass-panel" style={{ padding: '32px' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '24px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{ width: '40px', height: '40px', borderRadius: '12px', background: 'rgba(244, 63, 94, 0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <ShieldAlert size={22} color="#f43f5e" />
          </div>
          <div>
            <h2 style={{ fontSize: '1.2rem', fontWeight: 700 }}>Human-in-the-Loop Review Queue</h2>
            <p style={{ fontSize: '0.8rem', color: '#94a3b8' }}>Flagged invoices requiring human verification</p>
          </div>
        </div>

        <button className="btn-secondary" style={{ padding: '8px 14px', fontSize: '0.8rem', display: 'flex', alignItems: 'center', gap: '6px' }} onClick={fetchTasks}>
          <RefreshCw size={14} className={loading ? 'animate-spin' : ''} /> Refresh Queue
        </button>
      </div>

      {tasks.length === 0 && !loading && (
        <div style={{ height: '240px', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', color: '#34d399', textAlign: 'center' }}>
          <UserCheck size={48} style={{ opacity: 0.8, marginBottom: '16px' }} />
          <h3 style={{ fontSize: '1.1rem', fontWeight: 600, marginBottom: '4px' }}>Review Queue Empty</h3>
          <p style={{ fontSize: '0.85rem', color: '#94a3b8' }}>All processed invoices are verified and approved.</p>
        </div>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(340px, 1fr))', gap: '20px' }}>
        {tasks.map((task) => (
          <div key={task.id} style={{
            background: 'rgba(255, 255, 255, 0.025)',
            border: '1px solid rgba(244, 63, 94, 0.25)',
            borderRadius: '14px',
            padding: '20px',
            position: 'relative'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '14px' }}>
              <span className="font-mono" style={{ fontSize: '0.8rem', color: '#f43f5e', fontWeight: 700 }}>
                TASK #{task.id}
              </span>
              <span className="badge badge-warning" style={{ fontSize: '0.7rem' }}>
                <AlertTriangle size={12} /> {task.status}
              </span>
            </div>

            <div style={{ marginBottom: '14px' }}>
              <div style={{ fontSize: '0.75rem', color: '#94a3b8' }}>FLAGGED REASON</div>
              <div style={{ fontSize: '0.9rem', fontWeight: 600, color: '#fbbf24', marginTop: '2px' }}>
                {task.primary_reason}
              </div>
            </div>

            <div style={{ background: 'rgba(0, 0, 0, 0.3)', padding: '12px', borderRadius: '8px', marginBottom: '18px', fontSize: '0.82rem', color: '#cbd5e1' }}>
              {task.reason_description}
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
              <button
                className="btn-primary"
                style={{ background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)', justifyContent: 'center', padding: '10px', fontSize: '0.85rem' }}
                onClick={() => handleAction(task.id, 'approve')}
                disabled={actionLoading === task.id}
              >
                <CheckCircle2 size={16} /> Approve
              </button>
              <button
                className="btn-secondary"
                style={{ background: 'rgba(244, 63, 94, 0.15)', color: '#f87171', borderColor: 'rgba(244, 63, 94, 0.3)', justifyContent: 'center', padding: '10px', fontSize: '0.85rem' }}
                onClick={() => handleAction(task.id, 'reject')}
                disabled={actionLoading === task.id}
              >
                <XCircle size={16} /> Reject
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
