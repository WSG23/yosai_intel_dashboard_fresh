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
  Activity
} from 'lucide-react';

// Navigation items configuration
const navigationItems = [
  {
    name: 'Upload',
    href: '/upload',
    icon: Upload,
    description: 'Upload and process data files'
  },
  {
    name: 'Analytics',
    href: '/analytics',
    icon: BarChart3,
    description: 'Deep insights and pattern analysis'
  },
  {
    name: 'Graphs',
    href: '/graphs',
    icon: TrendingUp,
    description: 'Interactive charts and visualizations'
  },
  {
    name: 'Export',
    href: '/export',
    icon: Download,
    description: 'Export data in various formats'
  },
  {
    name: 'Settings',
    href: '/settings',
    icon: Settings,
    description: 'Application settings and preferences'
  }
];

interface NavigationProps {
  className?: string;
  orientation?: 'horizontal' | 'vertical';
}

const Navigation: React.FC<NavigationProps> = ({ 
  className = '', 
  orientation = 'horizontal' 
}) => {
  const location = useLocation();
  const navigate = useNavigate();
  
  const isActive = (href: string) => {
    return location.pathname === href;
  };

  if (orientation === 'vertical') {
    return (
      <nav className={cn("flex flex-col space-y-2", className)} aria-label="Main navigation">
        {navigationItems.map((item) => {
          const Icon = item.icon;
          return (
            <Link
              key={item.name}
              to={item.href}
              onClick={() => navigate(item.href)}
              className={cn(
                "flex items-center space-x-3 px-3 py-2 rounded-md text-sm font-medium transition-colors",
                isActive(item.href)
                  ? "bg-blue-100 text-blue-700"
                  : "text-gray-600 hover:bg-gray-100 hover:text-gray-900"
              )}
              title={item.description}
              aria-current={isActive(item.href) ? "page" : undefined}
            >
              <Icon className="h-5 w-5" />
              <span>{item.name}</span>
            </Link>
          );
        })}
      </nav>
    );
  }

  return (
    <nav className={cn("flex items-center space-x-1", className)} aria-label="Main navigation">
      {navigationItems.map((item) => {
        const Icon = item.icon;
        return (
          <Link
            key={item.name}
            to={item.href}
            onClick={() => navigate(item.href)}
            className={cn(
              "flex items-center space-x-2 px-3 py-2 rounded-md text-sm font-medium transition-colors",
              isActive(item.href)
                ? "bg-blue-100 text-blue-700"
                : "text-gray-600 hover:bg-gray-100 hover:text-gray-900"
            )}
            title={item.description}
            aria-current={isActive(item.href) ? "page" : undefined}
          >
            <Icon className="h-4 w-4" />
            <span className="hidden sm:inline">{item.name}</span>
          </Link>
        );
      })}
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
    <aside className={cn(
      "fixed inset-y-0 left-0 z-50 w-64 bg-white shadow-lg transform transition-transform duration-200 ease-in-out",
      isOpen ? "translate-x-0" : "-translate-x-full"
    )}>
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
