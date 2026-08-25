import React, { useState } from 'react';
import { Bot, Sparkles, Send, CheckCircle2, Database, AlertCircle, HelpCircle } from 'lucide-react';

export default function DataAnalystWidget() {
  const [question, setQuestion] = useState('');
  const [loading, setLoading] = useState(false);
  const [response, setResponse] = useState(null);
  const [error, setError] = useState('');

  const sampleQueries = [
    "How many invoices are pending review?",
    "Which vendor has the highest invoice volume?",
    "What is the total monetary value of purchase orders?",
    "How much invoice value was rejected this month?"
  ];

  const handleAsk = async (queryText) => {
    const q = queryText || question;
    if (!q || !q.trim()) return;

    setLoading(true);
    setError('');
    setResponse(null);

    try {
      const token = localStorage.getItem('token');
      const res = await fetch('/api/v1/analytics/ask', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {})
        },
        body: JSON.stringify({ question: q })
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || 'Data Analyst query failed.');
      }

      setResponse(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="glass-panel" style={{ padding: '24px', borderRadius: '16px', marginBottom: '28px' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
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
        <span className="badge badge-info" style={{ fontSize: '0.7rem' }}>
          Read-Only DB Tools
        </span>
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
          gap: '8px'
        }}>
          <AlertCircle size={16} />
          <span>{error}</span>
        </div>
      )}

      {/* Answer Response Card */}
      {response && (
        <div style={{
          padding: '18px 20px',
          borderRadius: '12px',
          background: 'rgba(99, 102, 241, 0.08)',
          border: '1px solid rgba(99, 102, 241, 0.2)',
          marginTop: '12px'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '10px' }}>
            <CheckCircle2 size={18} color="#818cf8" />
            <h4 style={{ fontSize: '0.9rem', fontWeight: 700, color: '#f8fafc', margin: 0 }}>
              Analyst Response
            </h4>
          </div>

          <p style={{ fontSize: '0.9rem', color: '#e2e8f0', margin: '0 0 14px 0', lineHeight: 1.5 }}>
            {response.answer}
          </p>

          {/* Tools & Sources Footnote */}
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '12px', paddingTop: '10px', borderTop: '1px solid rgba(255, 255, 255, 0.06)', fontSize: '0.75rem', color: '#94a3b8' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Database size={13} color="#38bdf8" />
              <span>Sources: <strong>{response.sources?.join(', ') || 'invoices'}</strong></span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Bot size={13} color="#a855f7" />
              <span>Tools Used: <strong>{response.tools_used?.join(', ') || 'get_invoice_summary'}</strong></span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
