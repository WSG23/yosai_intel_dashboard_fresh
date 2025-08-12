import React, { useState, Suspense } from 'react';
import './styles/upload.css';
import Navigation from './components/Navigation';
import { Shield, Menu, Sun, Moon } from 'lucide-react';
import useDarkMode from './hooks/useDarkMode';
import CenteredSpinner from './components/shared/CenteredSpinner';

const Upload = React.lazy(() => import('./components/upload'));

function App() {
  const [menuOpen, setMenuOpen] = useState(false);
  const { isDark, toggle } = useDarkMode();

  return (
    <div className="min-h-screen bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100">
      <header className="bg-white dark:bg-gray-800 shadow-sm mb-4">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <button
                className="mr-2 md:hidden"
                onClick={() => setMenuOpen(!menuOpen)}
                aria-label="Toggle menu"
              >
                <Menu className="h-6 w-6" />
              </button>
              <span className="flex items-center text-xl font-semibold">
                <Shield className="w-6 h-6 mr-2 text-blue-600" />
                Yōsai Intel Dashboard
              </span>
            </div>
            <nav className="hidden md:block">
              <Navigation />
            </nav>
            <button
              className="ml-4 p-2 rounded-md text-gray-600 dark:text-gray-300"
              onClick={toggle}
              aria-label="Toggle dark mode"
            >
              {isDark ? <Sun className="h-5 w-5" /> : <Moon className="h-5 w-5" />}
            </button>
          </div>
        </div>
        {menuOpen && (
          <div className="md:hidden px-4 pb-4">
            <Navigation orientation="vertical" />
          </div>
        )}
      </header>
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <Suspense fallback={<CenteredSpinner />}>
          <Upload />
        </Suspense>
      </main>
    </div>
  );
}

export default App;
