import React, { useState, useRef } from 'react';
import { Upload, FileUp, Sparkles, CheckCircle, AlertTriangle, ArrowRight, Eye, RefreshCw } from 'lucide-react';

export default function InvoiceUpload({ onProcessingComplete }) {
  const [dragActive, setDragActive] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [currentStep, setCurrentStep] = useState('');
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
  };

  const processInvoice = async () => {
    if (!selectedFile) return;

    setIsProcessing(true);
    setError(null);
    setCurrentStep('Extracting PDF text (PyMuPDF / Tesseract OCR fallback)...');

    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
      setTimeout(() => setCurrentStep('LLM GLM-4.7-Flash JSON Structured Parsing...'), 600);
      setTimeout(() => setCurrentStep('Executing 7 Deterministic Business Validation Checks...'), 1200);
      setTimeout(() => setCurrentStep('Autonomous InvoiceAgent Reasoning & PO Matching...'), 1800);

      const response = await fetch('/api/v1/invoices/process', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.detail || 'Failed to process invoice document');
      }

      const data = await response.json();
      setResult(data);
      if (onProcessingComplete) {
        onProcessingComplete(data);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1.1fr', gap: '24px' }}>
      {/* Left: Upload Card */}
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
            <button className="btn-secondary" style={{ padding: '4px 10px', fontSize: '0.75rem' }} onClick={(e) => { e.stopPropagation(); setSelectedFile(null); setResult(null); }}>
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
          onClick={processInvoice}
          disabled={!selectedFile || isProcessing}
        >
          {isProcessing ? (
            <>
              <RefreshCw size={18} className="animate-spin" style={{ animation: 'spin 1s linear infinite' }} /> Processing Pipeline...
            </>
          ) : (
            <>
              <Sparkles size={18} /> Run Agentic Pipeline
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

      {/* Right: Processing Results Output */}
      <div className="glass-panel" style={{ padding: '32px' }}>
        <h2 style={{ fontSize: '1.2rem', fontWeight: 700, marginBottom: '20px', display: 'flex', alignItems: 'center', gap: '10px' }}>
          <Sparkles size={20} color="#06b6d4" /> Pipeline Execution Results
        </h2>

        {!result && !isProcessing && (
          <div style={{ height: '300px', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', color: '#64748b', textAlign: 'center' }}>
            <FileUp size={48} style={{ opacity: 0.3, marginBottom: '16px' }} />
            <p style={{ fontSize: '0.9rem' }}>Upload an invoice to view live extraction & agent reasoning trace</p>
          </div>
        )}

        {result && (
          <div>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '20px', background: 'rgba(255, 255, 255, 0.03)', padding: '16px', borderRadius: '12px' }}>
              <div>
                <span className="font-mono" style={{ fontSize: '0.75rem', color: '#94a3b8' }}>STATUS</span>
                <div style={{ marginTop: '4px' }}>
                  <span className={result.status === 'SUCCESS' ? 'badge badge-success' : result.status === 'DUPLICATE_SUSPECTED' ? 'badge badge-warning' : 'badge badge-danger'} style={{ fontSize: '0.85rem' }}>
                    {result.status}
                  </span>
                </div>
              </div>
              <div style={{ textAlign: 'right' }}>
                <span className="font-mono" style={{ fontSize: '0.75rem', color: '#94a3b8' }}>EXTRACTION</span>
                <div style={{ fontSize: '0.85rem', fontWeight: 600, color: '#38bdf8', marginTop: '4px' }}>
                  {result.extraction_method === 'native_pdf' ? '⚡ Native PDF' : '🔍 Tesseract OCR'}
                </div>
              </div>
            </div>

            {result.extracted_invoice && (
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '20px' }}>
                <div style={{ background: 'rgba(255, 255, 255, 0.02)', padding: '14px', borderRadius: '10px', border: '1px solid rgba(255, 255, 255, 0.05)' }}>
                  <div style={{ fontSize: '0.75rem', color: '#94a3b8' }}>VENDOR</div>
                  <div style={{ fontSize: '0.95rem', fontWeight: 600, marginTop: '4px' }}>
                    {result.extracted_invoice.vendor?.vendor_name || 'N/A'}
                  </div>
                </div>
                <div style={{ background: 'rgba(255, 255, 255, 0.02)', padding: '14px', borderRadius: '10px', border: '1px solid rgba(255, 255, 255, 0.05)' }}>
                  <div style={{ fontSize: '0.75rem', color: '#94a3b8' }}>INVOICE NUMBER</div>
                  <div style={{ fontSize: '0.95rem', fontWeight: 600, marginTop: '4px' }} className="font-mono">
                    {result.extracted_invoice.invoice_number || 'N/A'}
                  </div>
                </div>
                <div style={{ background: 'rgba(255, 255, 255, 0.02)', padding: '14px', borderRadius: '10px', border: '1px solid rgba(255, 255, 255, 0.05)' }}>
                  <div style={{ fontSize: '0.75rem', color: '#94a3b8' }}>PO NUMBER</div>
                  <div style={{ fontSize: '0.95rem', fontWeight: 600, marginTop: '4px', color: result.extracted_invoice.po_number ? '#34d399' : '#94a3b8' }} className="font-mono">
                    {result.extracted_invoice.po_number || 'NONE'}
                  </div>
                </div>
                <div style={{ background: 'rgba(255, 255, 255, 0.02)', padding: '14px', borderRadius: '10px', border: '1px solid rgba(255, 255, 255, 0.05)' }}>
                  <div style={{ fontSize: '0.75rem', color: '#94a3b8' }}>TOTAL AMOUNT</div>
                  <div style={{ fontSize: '1.1rem', fontWeight: 700, marginTop: '4px', color: '#818cf8' }}>
                    ${result.extracted_invoice.total_amount?.toFixed(2)}
                  </div>
                </div>
              </div>
            )}

            {result.validation_result && (
              <div style={{ background: 'rgba(255, 255, 255, 0.02)', padding: '16px', borderRadius: '12px', border: '1px solid rgba(255, 255, 255, 0.05)' }}>
                <div style={{ fontSize: '0.8rem', fontWeight: 600, marginBottom: '8px', color: '#94a3b8' }}>
                  DETERMINISTIC VALIDATION CHECKS
                </div>
                {result.validation_result.is_valid ? (
                  <div className="badge badge-success" style={{ gap: '6px' }}>
                    <CheckCircle size={14} /> All 7 Business Math & Date Checks Passed
                  </div>
                ) : (
                  <div style={{ color: '#f87171', fontSize: '0.8rem' }}>
                    {result.validation_result.errors?.map((err, i) => (
                      <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '6px', marginTop: '4px' }}>
                        <AlertTriangle size={14} /> {err.message}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
