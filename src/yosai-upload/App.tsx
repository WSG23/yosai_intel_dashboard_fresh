import React, { useEffect } from 'react';
import logo from './logo.svg';
import './App.css';
import { request } from './api';
import { log } from './logger';

function App() {
  useEffect(() => {
    request('/api/ping')
      .then(() => log('info', 'ping ok'))
      .catch(err => log('error', 'ping failed', err));
  }, []);
  return (
    <div className="App">
      <header className="App-header">
        <img src={logo} className="App-logo" alt="logo" />
        <p>
          Edit <code>src/App.tsx</code> and save to reload.
        </p>
        <a
          className="App-link"
          href="https://reactjs.org"
          target="_blank"
          rel="noopener noreferrer"
        >
          Learn React
        </a>
      </header>
    </div>
  );
}

export default App;
