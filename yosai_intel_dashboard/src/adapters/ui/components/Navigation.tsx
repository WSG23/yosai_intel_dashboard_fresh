import React from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { cn } from '../lib/utils';
import {
  Upload,
  BarChart3,
  TrendingUp,
  Download,
  Settings,
  Database,
  Shield,
  Activity,
  LayoutDashboard
} from 'lucide-react';
import { useProficiencyStore } from '../state/store';

interface NavItem {
  name: string;
  href?: string;
  icon?: any;
  description?: string;
  level: number;
  children?: NavItem[];
}

// Navigation items configuration
const navigationItems: NavItem[] = [
  {
    name: 'Upload',
    href: '/upload',
    icon: Upload,
    description: 'Upload and process data files',
    level: 0,
  },
  {
    name: 'Analytics',
    href: '/analytics',
    icon: BarChart3,
    description: 'Deep insights and pattern analysis',
    level: 0,
  },
  {
    name: 'Graphs',
    href: '/graphs',
    icon: TrendingUp,
    description: 'Interactive charts and visualizations',
    level: 0,
  },
  {
    name: 'Export',
    href: '/export',
    icon: Download,
    description: 'Export data in various formats',
    level: 0,
  },
  {
    name: 'Settings',
    href: '/settings',
    icon: Settings,
    description: 'Application settings and preferences',
    level: 0,
    children: [
      { name: 'Profile', href: '/settings/profile', level: 1 },
      {
        name: 'System',
        href: '/settings/system',
        level: 2,
        children: [
          { name: 'Debug', href: '/settings/system/debug', level: 3 },
          {
            name: 'Experimental',
            href: '/settings/system/experimental',
            level: 4,
          },
        ],
      },
    ],
  },
  {
    name: 'Builder',
    href: '/builder',
    icon: LayoutDashboard,
    description: 'Custom dashboard builder',
    level: 0,
  },
];

interface NavigationProps {
  className?: string;
  orientation?: 'horizontal' | 'vertical';
}

const Navigation: React.FC<NavigationProps> = ({ className = '', orientation = 'horizontal' }) => {
  const location = useLocation();
  const navigate = useNavigate();
  const { level: userLevel, logFeatureUsage } = useProficiencyStore();

  const isActive = (href?: string) => href && location.pathname === href;

  const renderItems = (items: NavItem[], depth = 0): React.ReactNode => (
    <ul
      className={cn(
        orientation === 'horizontal' && depth === 0
          ? 'flex items-center space-x-1'
          : 'flex flex-col space-y-2',
        depth > 0 ? 'ml-4' : ''
      )}
    >
      {items
        .filter((item) => item.level <= userLevel)
        .map((item) => {
          const Icon = item.icon;
          const active = isActive(item.href);
          const hasChildren = item.children && item.children.length > 0;
          const content = item.href ? (
            <Link
              to={item.href}
              onClick={() => {
                logFeatureUsage(item.name);
                navigate(item.href!);
              }}
              className={cn(
                'flex items-center space-x-2 px-3 py-2 rounded-md text-sm font-medium transition-colors',
                active
                  ? 'bg-blue-100 text-blue-700'
                  : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
              )}
              title={item.description}
              aria-current={active ? 'page' : undefined}
            >
              {Icon && (
                <Icon
                  className={
                    orientation === 'horizontal' && depth === 0 ? 'h-4 w-4' : 'h-5 w-5'
                  }
                />
              )}
              <span
                className={
                  orientation === 'horizontal' && depth === 0 ? 'hidden sm:inline' : undefined
                }
              >
                {item.name}
              </span>
            </Link>
          ) : (
            <span className="px-3 py-2 text-sm font-medium text-gray-500">{item.name}</span>
          );

          return (
            <li key={item.name}>
              {content}
              {hasChildren && renderItems(item.children!, depth + 1)}
            </li>
          );
        })}
    </ul>
  );

  return (
    <nav className={cn(className)} aria-label="Main navigation">
      {renderItems(navigationItems)}
    </nav>
  );
};

// Header component with navigation
export const Header: React.FC = () => {
  return (
    <header className="bg-white shadow-sm border-b">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo/Title */}
          <div className="flex items-center">
            <Shield className="h-8 w-8 text-blue-600 mr-3" />
            <h1 className="text-xl font-bold text-gray-900">
              Yosai Intel Dashboard
            </h1>
          </div>

          {/* Navigation */}
          <Navigation />

          {/* Status indicator */}
          <div className="flex items-center space-x-2">
            <div className="flex items-center space-x-1">
              <Activity className="h-4 w-4 text-green-500" />
              <span className="text-sm text-gray-600">Connected</span>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
};

// Sidebar component with navigation
export const Sidebar: React.FC<{ isOpen: boolean }> = ({ isOpen }) => {
  return (
    <aside
      className={cn(
        'fixed inset-y-0 left-0 z-50 w-64 bg-white shadow-lg transform transition-transform duration-200 ease-in-out',
        isOpen ? 'translate-x-0' : '-translate-x-full'
      )}
    >
      <div className="flex flex-col h-full">
        {/* Sidebar header */}
        <div className="flex items-center justify-center h-16 px-4 bg-blue-600">
          <Shield className="h-8 w-8 text-white mr-2" />
          <h2 className="text-lg font-semibold text-white">Yosai Intel</h2>
        </div>

        {/* Navigation */}
        <div className="flex-1 px-4 py-6">
          <Navigation orientation="vertical" />
        </div>

        {/* Sidebar footer */}
        <div className="px-4 py-4 border-t">
          <div className="flex items-center text-sm text-gray-600">
            <Database className="h-4 w-4 mr-2" />
            <span>Analytics Ready</span>
          </div>
        </div>
      </div>
    </aside>
  );
};

export default Navigation;
