import React from 'react';
import './styles/upload.css';
import { Upload } from './components/upload';
import { Shield } from 'lucide-react';

function App() {
  return (
    <div className="App">
      <nav className="bg-gray-900 mb-4">
        <div className="container mx-auto px-4">
          <span className="flex items-center text-white text-xl font-semibold">
            <Shield className="w-6 h-6 mr-2" />
            Yōsai Intel Dashboard
          </span>
        </div>
      </nav>
      <div className="container mx-auto px-4">
        <Upload />
      </div>
    </div>
  );
}

export default App;
