import React, { useEffect, useRef } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import Hammer from 'hammerjs';
import { Plus } from 'lucide-react';
import { navigationItems } from '../Navigation';

const BottomNav: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const navRef = useRef<HTMLDivElement>(null);

  const items = navigationItems.filter((item) => item.level === 0);
  const currentIndex = items.findIndex((item) => item.href === location.pathname);

  const goToIndex = (index: number) => {
    if (index >= 0 && index < items.length) {
      const target = items[index];
      if (target.href) {
        navigate(target.href);
      }
    }
  };

  useEffect(() => {
    if (!navRef.current) return;
    const hammer = new Hammer(navRef.current);
    hammer.on('swipeleft', () => goToIndex(currentIndex + 1));
    hammer.on('swiperight', () => goToIndex(currentIndex - 1));
    return () => {
      hammer.destroy();
    };
  }, [currentIndex]);

  return (
    <nav
      ref={navRef}
      className="fixed bottom-0 left-0 right-0 z-50 bg-white border-t shadow-inner sm:hidden"
      aria-label="Bottom navigation"
    >
      <ul className="flex justify-around">
        {items.map((item) => {
          const Icon = item.icon;
          const active = location.pathname === item.href;
          return (
            <li key={item.name}>
              <Link
                to={item.href || '#'}
                className={`flex flex-col items-center justify-center py-2 px-3 ${active ? 'text-blue-600' : 'text-gray-600'}`}
                aria-label={item.name}
              >
                {Icon && <Icon className="h-6 w-6" />}
                <span className="text-xs">{item.name}</span>
              </Link>
            </li>
          );
        })}
      </ul>
      <button
        className="absolute -top-6 right-4 bg-blue-600 text-white rounded-full p-4 shadow-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
        aria-label="Primary action"
      >
        <Plus className="h-6 w-6" />
      </button>
    </nav>
  );
};

export default BottomNav;

