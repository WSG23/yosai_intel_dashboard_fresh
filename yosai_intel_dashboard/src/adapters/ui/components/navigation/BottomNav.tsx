import React, { useState } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { Upload, BarChart3, LineChart, Download, Settings, Plus } from 'lucide-react';
import { useSwipe } from '../../lib/gestures';

interface NavItem {
  path: string;
  label: string;
  icon: React.ReactNode;
}

const navItems: NavItem[] = [
  { path: '/upload', label: 'Upload', icon: <Upload size={24} /> },
  { path: '/analytics', label: 'Analytics', icon: <BarChart3 size={24} /> },
  { path: '/graphs', label: 'Graphs', icon: <LineChart size={24} /> },
  { path: '/export', label: 'Export', icon: <Download size={24} /> },
  { path: '/settings', label: 'Settings', icon: <Settings size={24} /> },
];

const BottomNav: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const [activeIndex, setActiveIndex] = useState(
    Math.max(0, navItems.findIndex((n) => n.path === location.pathname))
  );

  const swipeRef = useSwipe((dir) => {
    if (dir === 'left') {
      const next = (activeIndex + 1) % navItems.length;
      setActiveIndex(next);
      navigate(navItems[next].path);
    }
    if (dir === 'right') {
      const prev = (activeIndex - 1 + navItems.length) % navItems.length;
      setActiveIndex(prev);
      navigate(navItems[prev].path);
    }
  });

  return (
    <nav
      ref={swipeRef}
      className="fixed bottom-0 left-0 right-0 bg-white border-t shadow-md z-50"
    >
      <ul className="flex justify-around items-center py-2">
        {navItems.map((item, idx) => (
          <li key={item.path}>
            <Link
              to={item.path}
              onClick={() => setActiveIndex(idx)}
              className={`flex flex-col items-center justify-center w-11 h-11 rounded-full ${
                activeIndex === idx ? 'text-blue-600' : 'text-gray-600'
              }`}
              aria-label={item.label}
            >
              {item.icon}
            </Link>
          </li>
        ))}
      </ul>
      <button
        className="absolute -top-6 left-1/2 -translate-x-1/2 w-14 h-14 bg-blue-600 text-white rounded-full flex items-center justify-center shadow-lg"
        aria-label="Primary action"
      >
        <Plus size={28} />
      </button>
    </nav>
  );
};

export default BottomNav;

