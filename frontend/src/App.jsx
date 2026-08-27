import React, { useState, useEffect } from 'react';
import Navbar from './components/Navbar';
import Prism from './components/Prism';
import InvoiceUpload from './components/InvoiceUpload';
import AgentTraceViewer from './components/AgentTraceViewer';
import InvoicesTable from './components/InvoicesTable';
import ReviewQueue from './components/ReviewQueue';
import InvoiceDetailView from './components/InvoiceDetailView';
import VendorsView from './components/VendorsView';
import PurchaseOrdersView from './components/PurchaseOrdersView';
import DashboardView from './components/DashboardView';
import LoginView from './components/LoginView';

export default function App() {
  const [token, setToken] = useState(() => localStorage.getItem('invoicemind_token') || null);
  const [user, setUser] = useState(() => {
    const saved = localStorage.getItem('invoicemind_user');
    return saved ? JSON.parse(saved) : null;
  });

  const [activeTab, setActiveTab] = useState('dashboard');
  const [lastResult, setLastResult] = useState(null);
  const [selectedInvoiceId, setSelectedInvoiceId] = useState(null);
  const [selectedVendorId, setSelectedVendorId] = useState(null);
  const [selectedPoId, setSelectedPoId] = useState(null);
  const [pendingReviewCount, setPendingReviewCount] = useState(0);
  const [apiOnline, setApiOnline] = useState(true);

  const handleLoginSuccess = (newToken, newUser) => {
    setToken(newToken);
    setUser(newUser);
    localStorage.setItem('invoicemind_token', newToken);
    localStorage.setItem('invoicemind_user', JSON.stringify(newUser));
  };

  const handleLogout = () => {
    setToken(null);
    setUser(null);
    localStorage.removeItem('invoicemind_token');
    localStorage.removeItem('invoicemind_user');
  };

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
    if (resultData?.result?.database_invoice_id) {
      setSelectedInvoiceId(resultData.result.database_invoice_id);
    }
    setActiveTab('trace');
  };

  const handleSelectInvoice = (invoiceId) => {
    setSelectedInvoiceId(invoiceId);
    setActiveTab('detail');
  };

  const handleSelectVendor = (vendorId) => {
    setSelectedVendorId(vendorId);
    setActiveTab('vendors');
  };

  const handleSelectPo = (poId) => {
    setSelectedPoId(poId);
    setActiveTab('purchase_orders');
  };

  const handleTabChange = (tabKey) => {
    setSelectedInvoiceId(null);
    setSelectedVendorId(null);
    setSelectedPoId(null);
    setActiveTab(tabKey);
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
        {token && user && (
          <Navbar
            activeTab={activeTab}
            setActiveTab={handleTabChange}
            pendingReviewCount={pendingReviewCount}
            apiOnline={apiOnline}
            user={user}
            onLogout={handleLogout}
          />
        )}

        <main style={{ padding: '0 24px', marginTop: '16px' }}>
          {!token || !user ? (
            <LoginView onLoginSuccess={handleLoginSuccess} />
          ) : (
            <>
              {selectedInvoiceId || activeTab === 'detail' ? (
            <InvoiceDetailView
              invoiceId={selectedInvoiceId || lastResult?.result?.database_invoice_id}
              onBack={() => {
                setSelectedInvoiceId(null);
                setActiveTab('invoices');
              }}
              onStatusUpdated={() => {
                fetch('/api/v1/reviews?status=PENDING')
                  .then(res => res.json())
                  .then(data => setPendingReviewCount(Array.isArray(data) ? data.length : 0));
              }}
            />
          ) : (
            <>
              {activeTab === 'dashboard' && (
                <DashboardView
                  onSelectInvoice={handleSelectInvoice}
                  onNavigateUpload={() => setActiveTab('upload')}
                />
              )}

              {activeTab === 'upload' && (
                <InvoiceUpload onProcessingComplete={handleProcessingComplete} />
              )}

              {activeTab === 'trace' && (
                <AgentTraceViewer
                  lastResult={lastResult}
                  onInspectDetail={(invId) => handleSelectInvoice(invId)}
                />
              )}

              {activeTab === 'invoices' && (
                <InvoicesTable onSelectInvoice={handleSelectInvoice} />
              )}

              {activeTab === 'vendors' && (
                <VendorsView
                  onSelectVendor={handleSelectVendor}
                  onSelectPo={handleSelectPo}
                  onSelectInvoice={handleSelectInvoice}
                />
              )}

              {activeTab === 'purchase_orders' && (
                <PurchaseOrdersView
                  onSelectPo={handleSelectPo}
                  onSelectVendor={handleSelectVendor}
                  onSelectInvoice={handleSelectInvoice}
                />
              )}

              {activeTab === 'reviews' && (
                <ReviewQueue
                  onCountChange={(count) => setPendingReviewCount(count)}
                  onSelectInvoice={handleSelectInvoice}
                />
              )}
            </>
          )}
            </>
          )}
        </main>
      </div>
    </div>
  );
}
