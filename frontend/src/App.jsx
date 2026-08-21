import React, { useState, useEffect } from 'react';
import Navbar from './components/Navbar';
import Prism from './components/Prism';
import InvoiceUpload from './components/InvoiceUpload';
import AgentTraceViewer from './components/AgentTraceViewer';
import InvoicesTable from './components/InvoicesTable';
import ReviewQueue from './components/ReviewQueue';

export default function App() {
  const [activeTab, setActiveTab] = useState('upload');
  const [lastResult, setLastResult] = useState(null);
  const [pendingReviewCount, setPendingReviewCount] = useState(0);
  const [apiOnline, setApiOnline] = useState(true);

  useEffect(() => {
    // Check backend connection health
    fetch('/api/v1/reviews?status=PENDING')
      .then(res => {
        if (res.ok) {
          setApiOnline(true);
          return res.json();
        } else {
          setApiOnline(false);
        }
      })
      .then(data => {
        if (Array.isArray(data)) {
          setPendingReviewCount(data.length);
        }
      })
      .catch(() => setApiOnline(false));
  }, []);

  const handleProcessingComplete = (resultData) => {
    setLastResult(resultData);
    // Switch to trace tab automatically to show live agent reasoning
    setActiveTab('trace');
  };

  return (
    <div style={{ position: 'relative', minHeight: '100vh', background: '#07090e', color: '#f8fafc', overflowX: 'hidden' }}>
      {/* 3D WebGL Prism Shader Background */}
      <div style={{ position: 'fixed', inset: 0, zIndex: 0, opacity: 0.45, pointerEvents: 'none' }}>
        <Prism
          animationType="rotate"
          timeScale={0.3}
          height={3.5}
          baseWidth={5.5}
          scale={3.6}
          hueShift={0}
          colorFrequency={1}
          noise={0.15}
          glow={1.2}
        />
      </div>

      {/* Main Glassmorphism Dashboard Layout */}
      <div style={{ position: 'relative', zIndex: 10, maxWidth: '1400px', margin: '0 auto', paddingBottom: '40px' }}>
        <Navbar
          activeTab={activeTab}
          setActiveTab={setActiveTab}
          pendingReviewCount={pendingReviewCount}
          apiOnline={apiOnline}
        />

        <main style={{ padding: '0 24px', marginTop: '16px' }}>
          {activeTab === 'upload' && (
            <InvoiceUpload onProcessingComplete={handleProcessingComplete} />
          )}

          {activeTab === 'trace' && (
            <AgentTraceViewer lastResult={lastResult} />
          )}

          {activeTab === 'invoices' && (
            <InvoicesTable />
          )}

          {activeTab === 'reviews' && (
            <ReviewQueue onCountChange={(count) => setPendingReviewCount(count)} />
          )}
        </main>
      </div>
    </div>
  );
}
