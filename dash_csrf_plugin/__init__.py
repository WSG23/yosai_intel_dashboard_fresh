"""
Enhanced Dash CSRF Protection Plugin with improved route exemption logic
Includes wildcard route support and enhanced view function handling
"""

__version__ = "1.1.0"  # Updated version with enhancements

import os
import logging
from typing import Optional, Dict, Any, List
from enum import Enum

# Core imports
import dash
from flask import request, session, current_app
from dash import html, dcc

logger = logging.getLogger(__name__)


class CSRFMode(Enum):
    """CSRF protection modes"""
    AUTO = "auto"
    ENABLED = "enabled"
    DISABLED = "disabled"
    DEVELOPMENT = "development"
    PRODUCTION = "production"
    TESTING = "testing"


class CSRFConfig:
    """Enhanced configuration class for CSRF protection"""
    
    def __init__(self, 
                 enabled: bool = True,
                 secret_key: Optional[str] = None,
                 time_limit: int = 3600,
                 ssl_strict: bool = True,
                 exempt_routes: List[str] = None,
                 exempt_views: List[str] = None):
        self.enabled = enabled
        self.secret_key = secret_key or os.getenv('SECRET_KEY')
        self.time_limit = time_limit
        self.ssl_strict = ssl_strict
        self.exempt_routes = exempt_routes or []
        self.exempt_views = exempt_views or []
        self.methods = ['POST', 'PUT', 'PATCH', 'DELETE']
        self.check_referer = True
        self.custom_error_handler = None
        
    @classmethod
    def for_development(cls, **kwargs):
        """Create development configuration"""
        defaults = {
            'enabled': False,
            'ssl_strict': False,
            'secret_key': 'change-me'
        }
        defaults.update(kwargs)
        return cls(**defaults)
    
    @classmethod
    def for_production(cls, secret_key: str, **kwargs):
        """Create production configuration"""
        defaults = {
            'enabled': True,
            'secret_key': secret_key,
            'ssl_strict': True
        }
        defaults.update(kwargs)
        return cls(**defaults)
    
    @classmethod
    def for_testing(cls, **kwargs):
        """Create testing configuration"""
        defaults = {
            'enabled': False,
            'secret_key': 'test-secret-key'
        }
        defaults.update(kwargs)
        return cls(**defaults)


class EnhancedCSRFManager:
    """
    Enhanced CSRF Manager with your improved route exemption logic
    """
    
    def __init__(self, 
                 app: Optional[dash.Dash] = None,
                 config: Optional[CSRFConfig] = None,
                 mode: CSRFMode = CSRFMode.AUTO):
        self.app = app
        self.config = config or CSRFConfig()
        self.mode = mode
        self._initialized = False
        self._enabled = True
        self._exempt_routes: List[str] = []
        self._exempt_views: List[str] = []
        self.csrf_protect = None
        
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app: dash.Dash) -> None:
        """Initialize the enhanced CSRF manager"""
        if self._initialized:
            return
            
        self.app = app
        
        try:
            # Detect mode if AUTO
            if self.mode == CSRFMode.AUTO:
                self.mode = self._detect_mode()
            
            # Configure Flask server
            self._configure_server()
            
            # Set up enhanced exemptions
            self._setup_enhanced_exemptions()
            
            self._initialized = True
            logger.info(f"Enhanced CSRF Manager initialized in {self.mode.value} mode")
            
        except Exception as e:
            logger.error(f"Failed to initialize enhanced CSRF manager: {e}")
            # Fallback: disable CSRF to prevent errors
            self._fallback_disable()
    
    def _detect_mode(self) -> CSRFMode:
        """Auto-detect appropriate mode"""
        server = self.app.server
        
        # Check environment
        env = os.getenv('FLASK_ENV', os.getenv('DASH_ENV', 'production')).lower()
        testing = server.config.get('TESTING', False)
        debug = server.config.get('DEBUG', False)
        
        if testing:
            return CSRFMode.TESTING
        elif env == 'development' or debug:
            return CSRFMode.DEVELOPMENT
        elif env == 'production':
            return CSRFMode.PRODUCTION
        else:
            return CSRFMode.DISABLED
    
    def _configure_server(self) -> None:
        """Configure Flask server for CSRF protection"""
        server = self.app.server
        
        # Set secret key if not present
        if not server.config.get('SECRET_KEY'):
            server.config['SECRET_KEY'] = self.config.secret_key or 'change-me'
        
        # Configure CSRF based on mode
        if self.mode in [CSRFMode.ENABLED, CSRFMode.PRODUCTION]:
            server.config['WTF_CSRF_ENABLED'] = True
            self._enabled = True
            self._init_csrf_protect()
        else:
            server.config['WTF_CSRF_ENABLED'] = False
            self._enabled = False
        
        logger.info(f"Enhanced CSRF enabled: {self._enabled}")
    
    def _init_csrf_protect(self) -> None:
        """Initialize CSRF protection if enabled"""
        if self._enabled:
            try:
                from flask_wtf import CSRFProtect
                self.csrf_protect = CSRFProtect()
                self.csrf_protect.init_app(self.app.server)
                logger.info("CSRFProtect initialized")
            except ImportError:
                logger.warning("flask-wtf not available, disabling CSRF")
                self._fallback_disable()
            except Exception as e:
                logger.warning(f"CSRF setup failed: {e}, falling back to disabled mode")
                self._fallback_disable()
    
    def _setup_enhanced_exemptions(self) -> None:
        """Set up enhanced route exemptions with your improvements"""
        # Default Dash routes with wildcard support
        default_exempt_routes = [
            '/_dash-dependencies',
            '/_dash-layout',
            '/_dash-component-suites',
            '/_dash-update-component',
            '/_favicon.ico',
            '/_reload-hash',
            '/assets/*',  # Wildcard route
            '/health',
            '/healthz'
        ]
        
        for route in default_exempt_routes:
            self.add_exempt_route(route)
        
        # Add custom exempt routes from config
        for route in self.config.exempt_routes:
            self.add_exempt_route(route)
        
        # Add custom exempt views from config
        for view in self.config.exempt_views:
            self.add_exempt_view(view)
    
    def add_exempt_route(self, route: str) -> None:
        """Add a route to CSRF exemption list with enhanced logic (YOUR IMPROVEMENTS)"""
        if route not in self._exempt_routes:
            self._exempt_routes.append(route)
            
            if self.csrf_protect:
                # Try to exempt the associated view function if it exists
                view_func = None
                for rule in self.app.server.url_map.iter_rules():
                    # Support wildcard routes using '*' suffix
                    if rule.rule == route or (
                        route.endswith('*') and rule.rule.startswith(route[:-1])
                    ):
                        view_func = self.app.server.view_functions.get(rule.endpoint)
                        break

                if view_func:
                    try:
                        self.csrf_protect.exempt(view_func)
                        logger.debug(f"Successfully exempted view for route {route}")
                    except Exception as e:
                        logger.warning(
                            f"Could not exempt view for route {route}: {e}"
                        )
                else:
                    logger.debug(
                        "No view function found for route %s; exemption may be applied later",
                        route,
                    )
    
    def add_exempt_view(self, view_function: str) -> None:
        """Add a view function to CSRF exemption list with enhanced logic (YOUR IMPROVEMENTS)"""
        if view_function not in self._exempt_views:
            self._exempt_views.append(view_function)
            
            if self.csrf_protect:
                view = self.app.server.view_functions.get(view_function)
                if view:
                    try:
                        self.csrf_protect.exempt(view)
                        logger.debug(f"Successfully exempted view function {view_function}")
                    except Exception as e:
                        logger.warning(
                            f"Could not exempt view function {view_function}: {e}"
                        )
                else:
                    logger.debug(
                        "View function %s not found when attempting to exempt",
                        view_function,
                    )
    
    def _fallback_disable(self) -> None:
        """Fallback: disable CSRF to prevent errors"""
        if self.app and self.app.server:
            self.app.server.config['WTF_CSRF_ENABLED'] = False
        self._enabled = False
        self.mode = CSRFMode.DISABLED
        logger.info("CSRF protection disabled (fallback)")
    
    def create_csrf_component(self, component_id: str = "csrf-token"):
        """Create CSRF component for Dash layout"""
        if not self._enabled:
            return html.Div(style={'display': 'none'})
        
        # Simple hidden div for CSRF token
        return html.Div([
            html.Meta(name="csrf-token", content="csrf-disabled-in-dev"),
            dcc.Store(id=component_id, data={'csrf_enabled': self._enabled})
        ], style={'display': 'none'})
    
    def get_csrf_token(self) -> str:
        """Get current CSRF token"""
        if not self._enabled:
            return ""
        
        try:
            from flask_wtf.csrf import generate_csrf
            return generate_csrf()
        except:
            return ""
    
    def validate_csrf(self) -> bool:
        """Validate CSRF token"""
        if not self._enabled:
            return True
        
        try:
            from flask_wtf.csrf import validate_csrf
            token = (request.headers.get('X-CSRFToken') or 
                    request.form.get('csrf_token'))
            if token:
                validate_csrf(token)
                return True
        except:
            pass
        return False
    
    def get_status(self) -> Dict[str, Any]:
        """Get enhanced plugin status"""
        return {
            'initialized': self._initialized,
            'enabled': self._enabled,
            'mode': self.mode.value,
            'csrf_config_enabled': self.config.enabled,
            'flask_csrf_enabled': self.app.server.config.get('WTF_CSRF_ENABLED', False) if self.app else False,
            'enhanced_exemptions': True,  # Indicates this version has your improvements
            'wildcard_routes_supported': True,
            'exempt_routes': self._exempt_routes,
            'exempt_views': self._exempt_views
        }
    
    @property
    def is_enabled(self) -> bool:
        """Check if CSRF protection is enabled"""
        return self._enabled
    
    def disable(self) -> None:
        """Disable CSRF protection"""
        self._enabled = False
        if self.app:
            self.app.server.config['WTF_CSRF_ENABLED'] = False
    
    def enable(self) -> None:
        """Enable CSRF protection"""
        self._enabled = True
        if self.app:
            self.app.server.config['WTF_CSRF_ENABLED'] = True


class DashCSRFPlugin:
    """
    Enhanced plugin class that uses your improved CSRF manager
    """
    
    def __init__(self, 
                 app: Optional[dash.Dash] = None,
                 config: Optional[CSRFConfig] = None,
                 mode: CSRFMode = CSRFMode.AUTO):
        self.app = app
        self.config = config or CSRFConfig()
        self.mode = mode
        self.manager: Optional[EnhancedCSRFManager] = None
        self._initialized = False
        
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app: dash.Dash) -> None:
        """Initialize the plugin with enhanced manager"""
        if self._initialized:
            return
        
        self.app = app
        self.manager = EnhancedCSRFManager(app, self.config, self.mode)
        self._initialized = True
        
        logger.info("Enhanced CSRF Plugin initialized")
    
    def create_csrf_component(self, component_id: str = "csrf-token"):
        """Create CSRF component using enhanced manager"""
        if self.manager:
            return self.manager.create_csrf_component(component_id)
        return html.Div(style={'display': 'none'})
    
    def get_csrf_token(self) -> str:
        """Get CSRF token using enhanced manager"""
        if self.manager:
            return self.manager.get_csrf_token()
        return ""
    
    def add_exempt_route(self, route: str) -> None:
        """Add exempt route using enhanced logic"""
        if self.manager:
            self.manager.add_exempt_route(route)
    
    def add_exempt_view(self, view_function: str) -> None:
        """Add exempt view using enhanced logic"""
        if self.manager:
            self.manager.add_exempt_view(view_function)
    
    def get_status(self) -> Dict[str, Any]:
        """Get plugin status"""
        if self.manager:
            return self.manager.get_status()
        return {'initialized': False}
    
    @property
    def is_enabled(self) -> bool:
        """Check if plugin is enabled"""
        return self.manager.is_enabled if self.manager else False
    
    @property
    def version(self) -> str:
        """Get plugin version"""
        return "1.1.0"  # Enhanced version


# Convenience functions
def setup_enhanced_csrf_protection(app: dash.Dash, mode: CSRFMode = CSRFMode.AUTO) -> DashCSRFPlugin:
    """Quick setup function for enhanced CSRF protection"""
    return DashCSRFPlugin(app, mode=mode)


def disable_csrf_for_development(app: dash.Dash) -> DashCSRFPlugin:
    """Quick function to disable CSRF for development"""
    config = CSRFConfig.for_development()
    return DashCSRFPlugin(app, config, CSRFMode.DEVELOPMENT)


# Export main classes
__all__ = [
    'DashCSRFPlugin',
    'EnhancedCSRFManager',
    'CSRFConfig', 
    'CSRFMode',
    'setup_enhanced_csrf_protection',
    'disable_csrf_for_development'
]
