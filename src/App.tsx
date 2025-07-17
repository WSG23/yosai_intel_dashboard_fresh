import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from '@/components/ui/toaster';

// Import existing components
import Layout from '@/components/Layout';
import Upload from '@/pages/Upload';
import Settings from '@/pages/Settings';

// Import new components
import AnalyticsPage from '@/pages/Analytics';
import GraphsPage from '@/pages/Graphs';
import ExportPage from '@/pages/Export';

// Import any existing error boundary or loading components
import ErrorBoundary from '@/components/ErrorBoundary';

const App: React.FC = () => {
  return (
    <ErrorBoundary>
      <Router>
        <div className="min-h-screen bg-gray-50">
          <Layout>
            <Routes>
              {/* Default route - redirect to upload */}
              <Route path="/" element={<Navigate to="/upload" replace />} />
              
              {/* Existing routes */}
              <Route path="/upload" element={<Upload />} />
              <Route path="/settings" element={<Settings />} />
              
              {/* New routes */}
              <Route path="/analytics" element={<AnalyticsPage />} />
              <Route path="/graphs" element={<GraphsPage />} />
              <Route path="/export" element={<ExportPage />} />
              
              {/* Fallback for unknown routes */}
              <Route path="*" element={<Navigate to="/upload" replace />} />
            </Routes>
          </Layout>
          
          {/* Global toast notifications */}
          <Toaster />
        </div>
      </Router>
    </ErrorBoundary>
  );
};

export default App;
