import React, { Suspense } from 'react';
import ReactDOM from 'react-dom/client';
const SuspenseList = (React as any).SuspenseList;
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClientProvider } from '@tanstack/react-query';
import { queryClient } from './queryClient';
import { ZustandProvider } from './state';
import { SelectionProvider } from './core/interaction/SelectionContext';
import BottomNav from './components/navigation/BottomNav';
import { config } from '@fortawesome/fontawesome-svg-core';
import '@fortawesome/fontawesome-svg-core/styles.css';
import useIsMobile from './hooks/useIsMobile';
import ErrorBoundary from './components/ErrorBoundary';

type PreloadableComponent<T = {}> = React.LazyExoticComponent<React.FC<T>> & {
  preload?: () => void;
};

config.autoAddCss = false;

const RealTimeAnalyticsPage: PreloadableComponent = React.lazy(
  () => import('./pages/RealTimeAnalyticsPage'),
);
RealTimeAnalyticsPage.preload = () => {
  import('./pages/RealTimeAnalyticsPage');
};

const Upload: PreloadableComponent = React.lazy(() => import('./pages/Upload'));
Upload.preload = () => {
  import('./pages/Upload');
};

const Analytics: PreloadableComponent = React.lazy(
  () => import('./pages/Analytics'),
);
Analytics.preload = () => {
  import('./pages/Analytics');
};

const Graphs: PreloadableComponent = React.lazy(() => import('./pages/Graphs'));
Graphs.preload = () => {
  import('./pages/Graphs');
};

const Export: PreloadableComponent = React.lazy(() => import('./pages/Export'));
Export.preload = () => {
  import('./pages/Export');
};

const Settings: PreloadableComponent = React.lazy(
  () => import('./pages/Settings'),
);
Settings.preload = () => {
  import('./pages/Settings');
};

const DashboardBuilder: PreloadableComponent = React.lazy(
  () => import('./pages/DashboardBuilder'),
);
DashboardBuilder.preload = () => {
  import('./pages/DashboardBuilder');
};

import './index.css';

const rootEl = document.getElementById('root');
if (rootEl) {
  const root = ReactDOM.createRoot(rootEl as HTMLElement);
  const AppRoot: React.FC = () => {
    const isMobile = useIsMobile();

    return (
      <SelectionProvider>
        <QueryClientProvider client={queryClient}>
          <BrowserRouter>
            <SuspenseList revealOrder="forwards" tail="collapsed">
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
            </SuspenseList>
            {isMobile && <BottomNav />}
          </BrowserRouter>
        </QueryClientProvider>
      </SelectionProvider>
    );
  };

  root.render(
    <React.StrictMode>
      <ErrorBoundary>
        <AppRoot />
      </ErrorBoundary>
    </React.StrictMode>,
  );

  const pages = [Upload, Analytics, Graphs, Export, Settings, DashboardBuilder];
  if ('requestIdleCallback' in window) {
    (window as any).requestIdleCallback(() =>
      pages.forEach((p) => p.preload?.()),
    );
  } else {
    setTimeout(() => pages.forEach((p) => p.preload?.()), 2000);
  }
}

const rtEl = document.getElementById('real-time-root');
if (rtEl) {
  const rtRoot = ReactDOM.createRoot(rtEl as HTMLElement);
  rtRoot.render(
    <React.StrictMode>
      <SelectionProvider>
        <ZustandProvider>
          <Suspense fallback={<div>Loading...</div>}>
            <RealTimeAnalyticsPage />
          </Suspense>
        </ZustandProvider>
      </SelectionProvider>
    </React.StrictMode>,
  );
}

if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/service-worker.js').catch((err) => {
      console.error('Service worker registration failed', err);
    });
  });
}

export {
  RealTimeAnalyticsPage,
  Upload,
  Analytics,
  Graphs,
  Export,
  Settings,
  DashboardBuilder,
};
