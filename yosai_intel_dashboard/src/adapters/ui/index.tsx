import React, { Suspense } from 'react';
import ReactDOM from 'react-dom/client';
const RealTimeAnalyticsPage = React.lazy(() => import('./pages/RealTimeAnalyticsPage'));
const Upload = React.lazy(() => import('./pages/Upload'));
const Analytics = React.lazy(() => import('./pages/Analytics'));
const Graphs = React.lazy(() => import('./pages/Graphs'));
const Export = React.lazy(() => import('./pages/Export'));
const Settings = React.lazy(() => import('./pages/Settings'));
const DashboardBuilder = React.lazy(() => import('./pages/DashboardBuilder'));
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClientProvider } from '@tanstack/react-query';
import { queryClient } from './queryClient';
import { Provider } from 'react-redux';
import { store } from './state';
import { SelectionProvider } from './core/interaction/SelectionContext';
import './index.css';

const rootEl = document.getElementById('root');
if (rootEl) {
  const root = ReactDOM.createRoot(rootEl as HTMLElement);
  root.render(
    <React.StrictMode>
      <QueryClientProvider client={queryClient}>
        <Provider store={store}>
          <BrowserRouter>
            <Suspense fallback={<div>Loading...</div>}>
              <Routes>
                <Route path="/" element={<Navigate to="/upload" replace />} />
                <Route path="/upload" element={<Upload />} />
                <Route path="/analytics" element={<Analytics />} />
                <Route path="/graphs" element={<Graphs />} />
                <Route path="/export" element={<Export />} />
                <Route path="/settings" element={<Settings />} />
                <Route path="/builder" element={<DashboardBuilder />} />
              </Routes>
            </Suspense>
          </BrowserRouter>
        </Provider>
      </QueryClientProvider>
    </React.StrictMode>
  );
}

const rtEl = document.getElementById('real-time-root');
if (rtEl) {
  const rtRoot = ReactDOM.createRoot(rtEl as HTMLElement);
  rtRoot.render(
    <React.StrictMode>
      <Provider store={store}>
        <SelectionProvider>
          <Suspense fallback={<div>Loading...</div>}>
            <RealTimeAnalyticsPage />
          </Suspense>
        </SelectionProvider>
      </Provider>
    </React.StrictMode>
  );
}
