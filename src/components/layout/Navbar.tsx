import React, { useState, useEffect } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import {
  ChartBarIcon,
  CloudArrowUpIcon,
  ChartPieIcon,
  ArrowDownTrayIcon,
  CogIcon,
  Bars3Icon,
  XMarkIcon,
  MoonIcon,
  SunIcon,
  ComputerDesktopIcon,
  UserCircleIcon,
  ArrowRightOnRectangleIcon,
} from '@heroicons/react/24/outline';
import { useTheme } from '../../hooks/useTheme';
import { useAuth } from '../../hooks/useAuth';
import { MobileMenu } from './MobileMenu';
import { NotificationBell } from '../shared/NotificationBell';

interface NavItem {
  path: string;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  aliases?: string[];
  requiresAuth?: boolean;
}

const navItems: NavItem[] = [
  {
    path: '/analytics',
    label: 'Analytics',
    icon: ChartBarIcon,
    aliases: ['/', '/dashboard'],
  },
  {
    path: '/upload',
    label: 'Upload',
    icon: CloudArrowUpIcon,
    requiresAuth: true,
  },
  {
    path: '/graphs',
    label: 'Graphs',
    icon: ChartPieIcon,
  },
  {
    path: '/export',
    label: 'Export',
    icon: ArrowDownTrayIcon,
    requiresAuth: true,
  },
  {
    path: '/settings',
    label: 'Settings',
    icon: CogIcon,
  },
];

export const Navbar: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { theme, setTheme } = useTheme();
  const { user, logout } = useAuth();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [userMenuOpen, setUserMenuOpen] = useState(false);

  useEffect(() => {
    setMobileMenuOpen(false);
  }, [location.pathname]);

  const isActive = (item: NavItem): boolean => {
    if (location.pathname === item.path) return true;
    if (item.aliases?.includes(location.pathname)) return true;
    return false;
  };

  const visibleNavItems = navItems.filter(
    (item) => !item.requiresAuth || (item.requiresAuth && user)
  );

  const themeOptions = [
    { value: 'light', label: 'Light', icon: SunIcon },
    { value: 'dark', label: 'Dark', icon: MoonIcon },
    { value: 'system', label: 'System', icon: ComputerDesktopIcon },
  ];

  return (
    <>
      <nav className="bg-gray-900 border-b border-gray-800 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center">
              <Link to="/" className="flex-shrink-0">
                <img
                  className="h-8 w-auto"
                  src="/assets/yosai_logo_name_white.png"
                  alt="Yōsai Intel Dashboard"
                />
              </Link>
            </div>

            <div className="hidden md:flex md:items-center md:space-x-4">
              {visibleNavItems.map((item) => {
                const Icon = item.icon;
                const active = isActive(item);

                return (
                  <Link
                    key={item.path}
                    to={item.path}
                    className={`
                      px-3 py-2 rounded-md text-sm font-medium
                      flex items-center gap-2 transition-colors
                      ${active ? 'bg-gray-800 text-white' : 'text-gray-300 hover:bg-gray-700 hover:text-white'}
                    `}
                  >
                    <Icon className="h-5 w-5" aria-hidden="true" />
                    <span>{item.label}</span>
                  </Link>
                );
              })}
            </div>

            <div className="hidden md:flex md:items-center md:space-x-4">
              {user && <NotificationBell />}

              <div className="relative">
                <button
                  onClick={() => setUserMenuOpen(!userMenuOpen)}
                  className="p-2 rounded-md text-gray-300 hover:text-white hover:bg-gray-700"
                  aria-label="Change theme"
                >
                  {theme === 'dark' ? (
                    <MoonIcon className="h-5 w-5" />
                  ) : theme === 'light' ? (
                    <SunIcon className="h-5 w-5" />
                  ) : (
                    <ComputerDesktopIcon className="h-5 w-5" />
                  )}
                </button>

                {userMenuOpen && (
                  <div className="absolute right-0 mt-2 w-48 rounded-md shadow-lg bg-white dark:bg-gray-800 ring-1 ring-black ring-opacity-5">
                    <div className="py-1">
                      {themeOptions.map((option) => {
                        const Icon = option.icon;
                        return (
                          <button
                            key={option.value}
                            onClick={() => {
                              setTheme(option.value as any);
                              setUserMenuOpen(false);
                            }}
                            className="flex items-center px-4 py-2 text-sm text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700 w-full"
                          >
                            <Icon className="h-5 w-5 mr-3" />
                            {option.label}
                          </button>
                        );
                      })}
                    </div>
                  </div>
                )}
              </div>

              {user ? (
                <div className="relative">
                  <button
                    onClick={() => setUserMenuOpen(!userMenuOpen)}
                    className="flex items-center p-2 rounded-md text-gray-300 hover:text-white hover:bg-gray-700"
                  >
                    <UserCircleIcon className="h-6 w-6" />
                  </button>

                  {userMenuOpen && (
                    <div className="absolute right-0 mt-2 w-48 rounded-md shadow-lg bg-white dark:bg-gray-800 ring-1 ring-black ring-opacity-5">
                      <div className="py-1">
                        <div className="px-4 py-2 text-sm text-gray-700 dark:text-gray-200">
                          {user.email}
                        </div>
                        <hr className="border-gray-200 dark:border-gray-700" />
                        <button
                          onClick={() => {
                            logout();
                            navigate('/login');
                          }}
                          className="flex items-center px-4 py-2 text-sm text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700 w-full"
                        >
                          <ArrowRightOnRectangleIcon className="h-5 w-5 mr-3" />
                          Logout
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              ) : (
                <Link
                  to="/login"
                  className="px-3 py-2 rounded-md text-sm font-medium text-gray-300 hover:text-white hover:bg-gray-700"
                >
                  Login
                </Link>
              )}

              <button
                onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                className="md:hidden p-2 rounded-md text-gray-300 hover:text-white hover:bg-gray-700"
              >
                {mobileMenuOpen ? (
                  <XMarkIcon className="h-6 w-6" />
                ) : (
                  <Bars3Icon className="h-6 w-6" />
                )}
              </button>
            </div>
          </div>
        </div>

        <MobileMenu
          isOpen={mobileMenuOpen}
          onClose={() => setMobileMenuOpen(false)}
          navItems={visibleNavItems}
          currentPath={location.pathname}
        />
      </nav>

      {userMenuOpen && (
        <div
          className="fixed inset-0 z-40"
          onClick={() => {
            setUserMenuOpen(false);
          }}
        />
      )}
    </>
  );
};

