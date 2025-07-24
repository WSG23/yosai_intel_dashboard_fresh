import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import RealTimeAnalyticsPage from './pages/RealTimeAnalyticsPage';
import { ZustandProvider } from './state';
import "./index.css";
const rootEl = document.getElementById('root');
if (rootEl) {
  const root = ReactDOM.createRoot(rootEl as HTMLElement);
  root.render(
    <React.StrictMode>
      <ZustandProvider>
        <App />
      </ZustandProvider>
    </React.StrictMode>
  );
}

const rtEl = document.getElementById('real-time-root');
if (rtEl) {
  const rtRoot = ReactDOM.createRoot(rtEl as HTMLElement);
  rtRoot.render(
    <React.StrictMode>
      <ZustandProvider>
        <RealTimeAnalyticsPage />
      </ZustandProvider>
    </React.StrictMode>
  );
}
