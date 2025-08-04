import React, { useEffect } from 'react';
import './App.css';
import { request } from './api';
import { log } from './logger';
import ResponsiveImage from '../components/ResponsiveImage';
import logoSmall from '../assets/yosai_logo.png';
import logoLarge from '../assets/yosai_logo_name_white.png';

function App() {
  useEffect(() => {
    request('/api/ping')
      .then(() => log('info', 'ping ok'))
      .catch((err) => log('error', 'ping failed', err));
  }, []);
  return (
    <div className="App">
      <header className="App-header">
        <ResponsiveImage
          className="App-logo"
          alt="logo"
          sources={[
            { srcSet: logoSmall, media: '(max-width: 600px)' },
            { srcSet: logoLarge, media: '(min-width: 601px)' },
          ]}
          src={logoLarge}
        />
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
