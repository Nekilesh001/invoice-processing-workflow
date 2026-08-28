import React, { useState, useEffect } from 'react';
import { Bot, Sparkles, Send, CheckCircle2, Database, AlertCircle, HelpCircle, Trash2, Clock } from 'lucide-react';
import { apiFetch } from '../api';

export default function DataAnalystWidget() {
  const [question, setQuestion] = useState('');
  const [loading, setLoading] = useState(false);
  const [history, setHistory] = useState([]);
  const [error, setError] = useState('');

  const sampleQueries = [
    "How many invoices are pending review?",
    "Which vendor has the highest invoice volume?",
    "What is the total monetary value of purchase orders?",
    "How much invoice value was rejected this month?"
  ];

  // Load chat history from backend database and localStorage fallback
  const fetchHistory = async () => {
    try {
      const res = await apiFetch('/api/v1/analytics/history');
      if (res.ok) {
        const data = await res.json();
        if (Array.isArray(data) && data.length > 0) {
          setHistory(data);
          localStorage.setItem('analyst_chat_history', JSON.stringify(data));
          return;
        }
      }
    } catch (err) {
      console.warn('Failed to load history from DB endpoint, falling back to LocalStorage', err);
    }

    // Fallback to LocalStorage
    const saved = localStorage.getItem('analyst_chat_history');
    if (saved) {
      try {
        setHistory(JSON.parse(saved));
      } catch (e) {
        console.error('LocalStorage parse error', e);
      }
    }
  };

  useEffect(() => {
    fetchHistory();
  }, []);

  const handleAsk = async (queryText) => {
    const q = queryText || question;
    if (!q || !q.trim()) return;

    setLoading(true);
    setError('');

    try {
      const res = await apiFetch('/api/v1/analytics/ask', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ question: q.trim() })
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || 'Data Analyst query failed.');
      }

      const newRecord = {
        id: Date.now(),
        question: q.trim(),
        answer: data.answer,
        tools_used: data.tools_used || [],
        sources: data.sources || [],
        created_at: new Date().toISOString()
      };

      const updated = [...history, newRecord];
      setHistory(updated);
      localStorage.setItem('analyst_chat_history', JSON.stringify(updated));
      setQuestion('');
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleClearHistory = async () => {
    try {
      await apiFetch('/api/v1/analytics/history', {
        method: 'DELETE'
      });
    } catch (e) {
      console.warn('Backend history clear failed', e);
    }
    setHistory([]);
    localStorage.removeItem('analyst_chat_history');
  };

  return (
    <div className="glass-panel" style={{ padding: '24px', borderRadius: '16px', marginBottom: '28px' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px', flexWrap: 'wrap', gap: '12px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{
            width: '40px',
            height: '40px',
            borderRadius: '12px',
            background: 'linear-gradient(135deg, #6366f1 0%, #06b6d4 100%)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 0 15px rgba(99, 102, 241, 0.4)'
          }}>
            <Bot size={22} color="#ffffff" />
          </div>
          <div>
            <h3 style={{ fontSize: '1.05rem', fontWeight: 700, color: '#f8fafc', margin: 0, display: 'flex', alignItems: 'center', gap: '8px' }}>
              Invoice Data Analyst Assistant <Sparkles size={16} color="#fbbf24" />
            </h3>
            <span style={{ fontSize: '0.78rem', color: '#94a3b8' }}>
              Ask natural-language business intelligence questions about AP operations & database statistics
            </span>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          {history.length > 0 && (
            <button
              onClick={handleClearHistory}
              className="btn-secondary"
              style={{ padding: '4px 10px', fontSize: '0.75rem', color: '#f87171', borderColor: 'rgba(239, 68, 68, 0.3)', display: 'flex', alignItems: 'center', gap: '4px' }}
            >
              <Trash2 size={12} /> Clear History
            </button>
          )}
          <span className="badge badge-info" style={{ fontSize: '0.7rem' }}>
            Read-Only DB Tools
          </span>
        </div>
      </div>

      {/* Sample Query Pills */}
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', marginBottom: '16px' }}>
        {sampleQueries.map((sq, idx) => (
          <button
            key={idx}
            type="button"
            className="btn-secondary"
            style={{
              padding: '6px 12px',
              fontSize: '0.78rem',
              borderRadius: '20px',
              background: 'rgba(255, 255, 255, 0.04)',
              border: '1px solid rgba(255, 255, 255, 0.08)',
              color: '#cbd5e1',
              cursor: 'pointer'
            }}
            onClick={() => {
              setQuestion(sq);
              handleAsk(sq);
            }}
          >
            <HelpCircle size={13} style={{ marginRight: '4px' }} /> {sq}
          </button>
        ))}
      </div>

      {/* Input Box */}
      <form
        onSubmit={(e) => {
          e.preventDefault();
          handleAsk();
        }}
        style={{ display: 'flex', gap: '10px', marginBottom: '16px' }}
      >
        <input
          type="text"
          className="input-field"
          style={{ flex: 1, padding: '10px 16px', fontSize: '0.88rem' }}
          placeholder="Ask a question (e.g. Which vendor has the most invoices?)..."
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
        />
        <button
          type="submit"
          className="btn-primary"
          disabled={loading || !question.trim()}
          style={{ padding: '0 20px', fontSize: '0.88rem' }}
        >
          {loading ? 'Analyzing...' : <><Send size={15} /> Ask</>}
        </button>
      </form>

      {/* Error Alert */}
      {error && (
        <div style={{
          padding: '12px 16px',
          borderRadius: '10px',
          background: 'rgba(239, 68, 68, 0.1)',
          border: '1px solid rgba(239, 68, 68, 0.3)',
          color: '#f87171',
          fontSize: '0.85rem',
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          marginBottom: '16px'
        }}>
          <AlertCircle size={16} />
          <span>{error}</span>
        </div>
      )}

      {/* Chronological Chat History List */}
      {history.length > 0 && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '14px', maxHeight: '400px', overflowY: 'auto', paddingRight: '4px' }}>
          {history.slice().reverse().map((item, idx) => (
            <div
              key={item.id || idx}
              style={{
                padding: '18px 20px',
                borderRadius: '12px',
                background: 'rgba(99, 102, 241, 0.08)',
                border: '1px solid rgba(99, 102, 241, 0.2)'
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <HelpCircle size={15} color="#cbd5e1" />
                  <span style={{ fontSize: '0.88rem', fontWeight: 600, color: '#f8fafc' }}>
                    {item.question}
                  </span>
                </div>
                {item.created_at && (
                  <span style={{ fontSize: '0.7rem', color: '#64748b', display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <Clock size={11} /> {new Date(item.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </span>
                )}
              </div>

              <div style={{ display: 'flex', alignItems: 'flex-start', gap: '8px', marginBottom: '10px' }}>
                <CheckCircle2 size={16} color="#818cf8" style={{ marginTop: '2px', flexShrink: 0 }} />
                <p style={{ fontSize: '0.88rem', color: '#e2e8f0', margin: 0, lineHeight: 1.5 }}>
                  {item.answer}
                </p>
              </div>

              {/* Tools & Sources Footnote */}
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '12px', paddingTop: '8px', borderTop: '1px solid rgba(255, 255, 255, 0.06)', fontSize: '0.73rem', color: '#94a3b8' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <Database size={12} color="#38bdf8" />
                  <span>Sources: <strong>{item.sources?.join(', ') || 'invoices'}</strong></span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <Bot size={12} color="#a855f7" />
                  <span>Tools Used: <strong>{item.tools_used?.join(', ') || 'get_invoice_summary'}</strong></span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

