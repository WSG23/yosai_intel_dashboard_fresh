import React, { useState } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { Plus } from 'lucide-react';
import { useSwipe } from '../../lib/gestures';
import { navItems } from './navItems';

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
              <item.icon size={24} />
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

