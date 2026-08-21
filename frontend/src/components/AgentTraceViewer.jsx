import React from 'react';
import { Cpu, Terminal, ShieldCheck, AlertCircle, Wrench, CheckCircle2, ArrowRight } from 'lucide-react';

export default function AgentTraceViewer({ lastResult }) {
  const mockSampleTrace = {
    action: "AUTO_PROCESS",
    confidence_score: 1.0,
    vendor_verified: true,
    po_verified: true,
    reason: "Invoice 'INV-2026-001' fully verified via vendor lookup, PO matching (PO-8842), math validation, and duplicate checks.",
    executed_tools: [
      {
        tool: "check_duplicate_invoice",
        args: { vendor_name: "Acme Cloud Solutions Inc.", invoice_number: "INV-2026-001" },
        output: { is_duplicate: false, message: "No duplicate found in database." }
      },
      {
        tool: "lookup_vendor",
        args: { vendor_name: "Acme Cloud Solutions Inc." },
        output: { found: true, status: "VERIFIED", is_approved: true, tax_id: "TX-99881122" }
      },
      {
        tool: "lookup_purchase_order",
        args: { po_number: "PO-8842" },
        output: { found: true, status: "APPROVED", authorized_total: 3300.00, remaining_balance: 3300.00 }
      }
    ]
  };

  const traceData = lastResult?.agent_decision || mockSampleTrace;

  return (
    <div className="glass-panel" style={{ padding: '32px' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '24px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{ width: '40px', height: '40px', borderRadius: '12px', background: 'rgba(99, 102, 241, 0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Cpu size={22} color="#818cf8" />
          </div>
          <div>
            <h2 style={{ fontSize: '1.2rem', fontWeight: 700 }}>Autonomous InvoiceAgent Trace</h2>
            <p style={{ fontSize: '0.8rem', color: '#94a3b8' }}>Observe → Reason → Tool → Decision Execution Loop</p>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <span className="font-mono" style={{ fontSize: '0.75rem', color: '#94a3b8' }}>CONFIDENCE SCORE</span>
          <div style={{ background: 'rgba(16, 185, 129, 0.15)', border: '1px solid rgba(16, 185, 129, 0.3)', color: '#34d399', padding: '6px 14px', borderRadius: '9999px', fontSize: '0.9rem', fontWeight: 700 }}>
            {(traceData.confidence_score * 100).toFixed(0)}%
          </div>
        </div>
      </div>

      {/* Decision Summary Card */}
      <div style={{
        background: traceData.action === 'AUTO_PROCESS' ? 'rgba(16, 185, 129, 0.08)' : 'rgba(244, 63, 94, 0.08)',
        border: `1px solid ${traceData.action === 'AUTO_PROCESS' ? 'rgba(16, 185, 129, 0.25)' : 'rgba(244, 63, 94, 0.25)'}`,
        padding: '20px',
        borderRadius: '14px',
        marginBottom: '28px'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '8px' }}>
          {traceData.action === 'AUTO_PROCESS' ? (
            <ShieldCheck size={20} color="#34d399" />
          ) : (
            <AlertCircle size={20} color="#f87171" />
          )}
          <span style={{ fontSize: '1rem', fontWeight: 700, color: traceData.action === 'AUTO_PROCESS' ? '#34d399' : '#f87171' }}>
            AGENT DECISION: {traceData.action}
          </span>
        </div>
        <p style={{ fontSize: '0.88rem', color: '#cbd5e1', lineHeight: '1.5' }}>
          {traceData.reason}
        </p>
      </div>

      {/* Executed Tools Timeline */}
      <h3 style={{ fontSize: '1rem', fontWeight: 600, marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
        <Wrench size={16} color="#38bdf8" /> Executed Tool Calls & Observations ({traceData.executed_tools?.length || 0})
      </h3>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
        {traceData.executed_tools?.map((t, idx) => (
          <div key={idx} style={{
            background: 'rgba(255, 255, 255, 0.02)',
            border: '1px solid rgba(255, 255, 255, 0.06)',
            borderRadius: '12px',
            padding: '16px',
            position: 'relative'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '10px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span className="font-mono" style={{ background: 'rgba(99, 102, 241, 0.2)', color: '#818cf8', padding: '2px 8px', borderRadius: '6px', fontSize: '0.75rem', fontWeight: 700 }}>
                  STEP {idx + 1}
                </span>
                <span className="font-mono" style={{ fontSize: '0.9rem', fontWeight: 600, color: '#f8fafc' }}>
                  {t.tool}()
                </span>
              </div>
              <span className="badge badge-success" style={{ fontSize: '0.7rem' }}>
                <CheckCircle2 size={12} /> EXECUTED
              </span>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
              <div style={{ background: 'rgba(0, 0, 0, 0.3)', padding: '10px', borderRadius: '8px' }}>
                <div style={{ fontSize: '0.7rem', color: '#94a3b8', marginBottom: '4px' }}>ARGUMENTS</div>
                <pre style={{ fontSize: '0.75rem', color: '#38bdf8', whiteSpace: 'pre-wrap' }}>
                  {JSON.stringify(t.args || {}, null, 2)}
                </pre>
              </div>
              <div style={{ background: 'rgba(0, 0, 0, 0.3)', padding: '10px', borderRadius: '8px' }}>
                <div style={{ fontSize: '0.7rem', color: '#94a3b8', marginBottom: '4px' }}>OBSERVATION OUTPUT</div>
                <pre style={{ fontSize: '0.75rem', color: '#34d399', whiteSpace: 'pre-wrap' }}>
                  {JSON.stringify(t.output || {}, null, 2)}
                </pre>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
