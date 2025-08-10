import React, { useState, useEffect } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { Menu, X, Shield } from 'lucide-react';
import { navItems } from '../navigation/navItems';
import { useNavbarTitle } from './NavbarTitleContext';
import './Navbar.css';
import useIsMobile from '../../hooks/useIsMobile';

const Navbar: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { title } = useNavbarTitle();
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [activeTab, setActiveTab] = useState(location.pathname);
  const isMobile = useIsMobile();

  useEffect(() => {
    setActiveTab(location.pathname);
  }, [location]);

  useEffect(() => {
    if (!isMobile) setIsMenuOpen(false);
  }, [isMobile]);

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
          <span id="navbar-title" className="navbar-title">
            {title}
          </span>
        </div>

        {isMobile && (
          <button
            className="mobile-menu-toggle"
            onClick={() => setIsMenuOpen(!isMenuOpen)}
            aria-label="Toggle menu"
          >
            {isMenuOpen ? <X size={24} /> : <Menu size={24} />}
          </button>
        )}

        <div className={`navbar-menu ${isMobile && isMenuOpen ? 'is-active' : ''}`}>
          {navItems.map((item) => (
            <Link
              key={item.path}
              to={item.path}
              className={`navbar-item ${activeTab === item.path ? 'is-active' : ''}`}
              onClick={() => handleNavClick(item.path)}
            >
              <item.icon size={20} />
              <span className="navbar-label">{item.label}</span>
            </Link>
          ))}
        </div>
      </div>
    </nav>
  );
};

export default Navbar;
