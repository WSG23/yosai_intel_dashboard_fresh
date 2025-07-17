import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Navbar } from './components/layout';
import { Upload, Analytics, Graphs, Export, Settings } from './pages';
import './App.css';

function App() {
  return (
    <Router>
      <div className="app">
        <Navbar />
        <main className="main-content">
          <Routes>
            <Route path="/" element={<Navigate to="/upload" replace />} />
            <Route path="/upload" element={<Upload />} />
            <Route path="/analytics" element={<Analytics />} />
            <Route path="/graphs" element={<Graphs />} />
            <Route path="/export" element={<Export />} />
            <Route path="/settings" element={<Settings />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;
