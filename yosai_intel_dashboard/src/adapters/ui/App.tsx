import React from 'react';
import 'bootstrap/dist/css/bootstrap.min.css';
import '@fortawesome/fontawesome-free/css/all.min.css';
import './styles/upload.css';
import { Upload } from './components/upload';

function App() {
  return (
    <div className="App">
      <nav className="navbar navbar-dark bg-dark mb-4">
        <div className="container-fluid">
          <span className="navbar-brand mb-0 h1">
            <i className="fas fa-shield-alt me-2"></i>
            Yōsai Intel Dashboard
          </span>
        </div>
      </nav>
      <div className="container-fluid">
        <Upload />
      </div>
    </div>
  );
}

export default App;
