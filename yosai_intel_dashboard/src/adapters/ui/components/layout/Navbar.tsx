import React, { useState, useEffect } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { 
  Upload, 
  BarChart3, 
  LineChart, 
  Download, 
  Settings,
  Menu,
  X,
  Shield
} from 'lucide-react';
import './Navbar.css';

interface NavItem {
  path: string;
  label: string;
  icon: React.ReactNode;
}

const Navbar: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [activeTab, setActiveTab] = useState(location.pathname);

  const navItems: NavItem[] = [
    { path: '/upload', label: 'Upload', icon: <Upload size={20} /> },
    { path: '/analytics', label: 'Analytics', icon: <BarChart3 size={20} /> },
    { path: '/graphs', label: 'Graphs', icon: <LineChart size={20} /> },
    { path: '/export', label: 'Export', icon: <Download size={20} /> },
    { path: '/settings', label: 'Settings', icon: <Settings size={20} /> }
  ];

  useEffect(() => {
    setActiveTab(location.pathname);
  }, [location]);

  const handleNavClick = (path: string) => {
    setActiveTab(path);
    setIsMenuOpen(false);
    navigate(path);
  };

  return (
    <nav className="navbar">
      <div className="navbar-container">
        <div className="navbar-brand">
          <Shield className="brand-icon" size={24} />
          <span className="brand-text">YOSAI Intelligence</span>
        </div>

        <button 
          className="mobile-menu-toggle"
          onClick={() => setIsMenuOpen(!isMenuOpen)}
          aria-label="Toggle menu"
        >
          {isMenuOpen ? <X size={24} /> : <Menu size={24} />}
        </button>

        <div className={`navbar-menu ${isMenuOpen ? 'is-active' : ''}`}>
          {navItems.map((item) => (
            <Link
              key={item.path}
              to={item.path}
              className={`navbar-item ${activeTab === item.path ? 'is-active' : ''}`}
              onClick={() => handleNavClick(item.path)}
            >
              {item.icon}
              <span className="navbar-label">{item.label}</span>
            </Link>
          ))}
        </div>
      </div>
    </nav>
  );
};

export default Navbar;
