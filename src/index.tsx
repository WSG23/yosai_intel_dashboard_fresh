import React from 'react';
import ReactDOM from 'react-dom/client';
import RealTimeAnalyticsPage from './pages/RealTimeAnalyticsPage';
import {
  Upload,
  Analytics,
  Graphs,
  Export,
  Settings
} from './pages';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import "./index.css";
const rootEl = document.getElementById('root');
if (rootEl) {
  const root = ReactDOM.createRoot(rootEl as HTMLElement);
  root.render(
    <React.StrictMode>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Navigate to="/upload" replace />} />
          <Route path="/upload" element={<Upload />} />
          <Route path="/analytics" element={<Analytics />} />
          <Route path="/graphs" element={<Graphs />} />
          <Route path="/export" element={<Export />} />
          <Route path="/settings" element={<Settings />} />
        </Routes>
      </BrowserRouter>
    </React.StrictMode>
  );
}

const rtEl = document.getElementById('real-time-root');
if (rtEl) {
  const rtRoot = ReactDOM.createRoot(rtEl as HTMLElement);
  rtRoot.render(
    <React.StrictMode>
      <RealTimeAnalyticsPage />
    </React.StrictMode>
  );
}
