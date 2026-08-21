import React, { useState, useRef } from 'react';
import { Upload, FileUp, Sparkles, CheckCircle, AlertTriangle, RefreshCw, FileText, Cpu, Terminal, ShieldCheck } from 'lucide-react';

export default function InvoiceUpload({ onProcessingComplete }) {
  const [dragActive, setDragActive] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);
  
  // Real-time streaming state
  const [currentStep, setCurrentStep] = useState('');
  const [rawText, setRawText] = useState('');
  const [extractionMethod, setExtractionMethod] = useState('');
  const [streamEvents, setStreamEvents] = useState([]);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const fileInputRef = useRef(null);

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      handleFile(e.target.files[0]);
    }
  };

  const handleFile = (file) => {
    if (!file.name.match(/\.(pdf|png|jpg|jpeg|tiff)$/i)) {
      setError('Please upload a valid PDF or Image file (.pdf, .png, .jpg, .jpeg)');
      return;
    }
    setSelectedFile(file);
    setError(null);
    setResult(null);
    setRawText('');
    setStreamEvents([]);
  };

  const processInvoiceStream = async () => {
    if (!selectedFile) return;

    setIsProcessing(true);
    setError(null);
    setResult(null);
    setRawText('');
    setStreamEvents([]);
    setCurrentStep('Initializing document processing stream...');

    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
      const response = await fetch('/api/v1/invoices/process-stream', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error('Failed to start streaming response');
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder('utf-8');
      let buffer = '';

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n\n');
        buffer = lines.pop() || ''; // Keep incomplete trailing chunk

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.replace('data: ', '').trim());
              handleStreamEvent(data);
            } catch (e) {
              console.error('Failed to parse SSE event', e);
            }
          }
        }
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleStreamEvent = (data) => {
    if (data.message) {
      setCurrentStep(data.message);
      setStreamEvents(prev => [...prev, { time: new Date().toLocaleTimeString(), message: data.message, stage: data.stage }]);
    }

    if (data.event === 'text_extracted') {
      setRawText(data.raw_text);
      setExtractionMethod(data.method);
    }

    if (data.event === 'complete' && data.result) {
      setResult(data.result);
      if (onProcessingComplete) {
        onProcessingComplete(data.result);
      }
    }

    if (data.event === 'error') {
      setError(data.message);
    }
  };

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1.15fr', gap: '24px' }}>
      {/* Left Column: Upload Card */}
      <div className="glass-panel" style={{ padding: '32px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '20px' }}>
          <div style={{ width: '38px', height: '38px', borderRadius: '10px', background: 'rgba(99, 102, 241, 0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Upload size={20} color="#818cf8" />
          </div>
          <div>
            <h2 style={{ fontSize: '1.2rem', fontWeight: 700 }}>Upload Invoice Document</h2>
            <p style={{ fontSize: '0.8rem', color: '#94a3b8' }}>PDF text extraction with Tesseract OCR fallback</p>
          </div>
        </div>

        <div
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
          style={{
            border: `2px dashed ${dragActive ? '#6366f1' : 'rgba(255, 255, 255, 0.15)'}`,
            borderRadius: '16px',
            padding: '40px 24px',
            textAlign: 'center',
            cursor: 'pointer',
            background: dragActive ? 'rgba(99, 102, 241, 0.08)' : 'rgba(255, 255, 255, 0.02)',
            transition: 'all 0.2s ease',
            marginBottom: '24px'
          }}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf,.png,.jpg,.jpeg,.tiff"
            onChange={handleFileChange}
            style={{ display: 'none' }}
          />

          <FileUp size={44} color="#6366f1" style={{ marginBottom: '14px', opacity: 0.8 }} />
          <h3 style={{ fontSize: '1rem', fontWeight: 600, marginBottom: '6px' }}>
            {selectedFile ? selectedFile.name : 'Drag & drop invoice PDF or browse'}
          </h3>
          <p style={{ fontSize: '0.75rem', color: '#64748b' }}>
            Supported formats: PDF, PNG, JPG (Max 25MB)
          </p>
        </div>

        {selectedFile && (
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '20px', background: 'rgba(255, 255, 255, 0.04)', padding: '12px 16px', borderRadius: '10px' }}>
            <div style={{ fontSize: '0.85rem', fontWeight: 500 }}>
              📄 {selectedFile.name} <span style={{ color: '#64748b', fontSize: '0.75rem' }}>({(selectedFile.size / 1024).toFixed(1)} KB)</span>
            </div>
            <button className="btn-secondary" style={{ padding: '4px 10px', fontSize: '0.75rem' }} onClick={(e) => { e.stopPropagation(); setSelectedFile(null); setResult(null); setRawText(''); setStreamEvents([]); }}>
              Change
            </button>
          </div>
        )}

        {error && (
          <div className="badge badge-danger" style={{ width: '100%', padding: '12px', borderRadius: '10px', marginBottom: '20px', justifyContent: 'center' }}>
            <AlertTriangle size={16} /> {error}
          </div>
        )}

        <button
          className="btn-primary"
          style={{ width: '100%', justifyContent: 'center', padding: '14px', fontSize: '0.95rem' }}
          onClick={processInvoiceStream}
          disabled={!selectedFile || isProcessing}
        >
          {isProcessing ? (
            <>
              <RefreshCw size={18} className="animate-spin" style={{ animation: 'spin 1s linear infinite' }} /> Streaming Real-Time Pipeline...
            </>
          ) : (
            <>
              <Sparkles size={18} /> Run Streaming Agentic Pipeline
            </>
          )}
        </button>

        {isProcessing && (
          <div style={{ marginTop: '16px', fontSize: '0.8rem', color: '#818cf8', textAlign: 'center', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px' }}>
            <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#6366f1', animation: 'pulse 1s infinite' }} />
            {currentStep}
          </div>
        )}
      </div>

      {/* Right Column: Live Streaming Concept View */}
      <div className="glass-panel" style={{ padding: '32px', display: 'flex', flexDirection: 'column', gap: '20px' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <h2 style={{ fontSize: '1.2rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '10px' }}>
            <Sparkles size={20} color="#06b6d4" /> Pipeline Execution & Ideation Stream
          </h2>

          {extractionMethod && (
            <span className="badge badge-info" style={{ fontSize: '0.75rem' }}>
              {extractionMethod === 'native_pdf' ? '⚡ PyMuPDF Native' : '🔍 Tesseract OCR'}
            </span>
          )}
        </div>

        {/* 1. Real-Time Raw Text Stream Terminal */}
        <div style={{
          background: 'rgba(0, 0, 0, 0.55)',
          border: '1px solid rgba(255, 255, 255, 0.08)',
          borderRadius: '12px',
          padding: '16px',
          fontFamily: 'JetBrains Mono, monospace'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '10px', color: '#94a3b8', fontSize: '0.75rem' }}>
            <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Terminal size={14} color="#38bdf8" /> INSTANT EXTRACTED RAW TEXT STREAM
            </span>
            {rawText && <span style={{ color: '#34d399' }}>{rawText.length} chars extracted</span>}
          </div>

          <div style={{
            maxHeight: '160px',
            overflowY: 'auto',
            fontSize: '0.78rem',
            color: '#38bdf8',
            whiteSpace: 'pre-wrap',
            lineHeight: '1.5'
          }}>
            {rawText ? rawText : (
              <span style={{ color: '#64748b', italic: true }}>
                {isProcessing ? '> Waiting for document text extraction...' : '> Upload an invoice to stream raw document text immediately.'}
              </span>
            )}
          </div>
        </div>

        {/* 2. Real-Time LLM Ideation & Tool Event Stream Log */}
        <div style={{
          background: 'rgba(255, 255, 255, 0.02)',
          border: '1px solid rgba(255, 255, 255, 0.06)',
          borderRadius: '12px',
          padding: '16px'
        }}>
          <div style={{ fontSize: '0.75rem', fontWeight: 600, color: '#94a3b8', marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '6px' }}>
            <Cpu size={14} color="#818cf8" /> LLM IDEATION & TOOL REASONING STREAM
          </div>

          <div style={{ maxHeight: '160px', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {streamEvents.length === 0 && !isProcessing && (
              <span style={{ fontSize: '0.8rem', color: '#64748b' }}>
                No events streamed yet. Click "Run Streaming Agentic Pipeline" to start.
              </span>
            )}

            {streamEvents.map((evt, idx) => (
              <div key={idx} style={{ display: 'flex', alignItems: 'flex-start', gap: '10px', fontSize: '0.8rem' }}>
                <span className="font-mono" style={{ color: '#64748b', fontSize: '0.7rem', marginTop: '2px' }}>{evt.time}</span>
                <span style={{
                  color: evt.stage === 'AGENT_DECISION' ? '#34d399' : evt.stage === 'TEXT_EXTRACTED' ? '#38bdf8' : '#e2e8f0',
                  fontWeight: evt.stage === 'AGENT_DECISION' ? 600 : 400
                }}>
                  {evt.message}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* 3. Final Result Badge Card */}
        {result && (
          <div style={{
            background: result.status === 'SUCCESS' ? 'rgba(16, 185, 129, 0.1)' : 'rgba(244, 63, 94, 0.1)',
            border: `1px solid ${result.status === 'SUCCESS' ? 'rgba(16, 185, 129, 0.3)' : 'rgba(244, 63, 94, 0.3)'}`,
            padding: '16px',
            borderRadius: '12px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <ShieldCheck size={20} color={result.status === 'SUCCESS' ? '#34d399' : '#f87171'} />
              <div>
                <div style={{ fontSize: '0.85rem', fontWeight: 700, color: result.status === 'SUCCESS' ? '#34d399' : '#f87171' }}>
                  PIPELINE COMPLETE: {result.status}
                </div>
                <div style={{ fontSize: '0.75rem', color: '#cbd5e1' }}>
                  Invoice #{result.extracted_invoice?.invoice_number || 'N/A'} for {result.extracted_invoice?.vendor?.vendor_name || 'N/A'} (${result.extracted_invoice?.total_amount?.toFixed(2)})
                </div>
              </div>
            </div>

            <button className="btn-secondary" style={{ padding: '6px 12px', fontSize: '0.75rem' }} onClick={() => {
              if (onProcessingComplete) onProcessingComplete(result);
            }}>
              View Full Agent Trace →
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
