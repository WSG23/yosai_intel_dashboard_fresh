"""
CSRF Manager for handling CSRF protection in Dash applications
"""

import logging
from typing import Optional, List, Dict, Any
from flask import request, session, current_app
from flask_wtf.csrf import CSRFProtect, generate_csrf, validate_csrf
from werkzeug.exceptions import BadRequest
import dash
from dash import html, dcc

from .config import CSRFConfig, CSRFMode
from .exceptions import CSRFError, CSRFValidationError
from .utils import CSRFUtils

logger = logging.getLogger(__name__)


class CSRFManager:
    """
    Manages CSRF protection for Dash applications
    
    Handles:
    - CSRF token generation and validation
    - Route exemptions for Dash-specific endpoints
    - Error handling and recovery
    - Mode-specific behavior
    """
    
    def __init__(self, 
                 app: dash.Dash,
                 config: CSRFConfig,
                 mode: CSRFMode):
        """
        Initialize CSRF manager
        
        Args:
            app: Dash application instance
            config: CSRF configuration
            mode: Protection mode
        """
        self.app = app
        self.config = config
        self.mode = mode
        self.csrf_protect: Optional[CSRFProtect] = None
        self.utils = CSRFUtils()
        self._enabled = True
        self._exempt_routes: List[str] = []
        self._exempt_views: List[str] = []
        self._initialized = False
        
    def init_app(self) -> None:
        """Initialize CSRF protection for the application"""
        if self._initialized:
            return
        
        server = self.app.server
        
        # Apply configuration to Flask server
        self._apply_config_to_server()
        
        # Initialize CSRF protection based on mode
        if self.mode in [CSRFMode.ENABLED, CSRFMode.PRODUCTION]:
            self._init_csrf_protection()
        elif self.mode == CSRFMode.DEVELOPMENT:
            self._init_development_mode()
        elif self.mode == CSRFMode.TESTING:
            self._init_testing_mode()
        elif self.mode == CSRFMode.DISABLED:
            self._init_disabled_mode()
        
        # Set up exempt routes
        self._setup_default_exemptions()
        
        # Set up error handlers
        self._setup_error_handlers()
        
        self._initialized = True
        logger.info(f"CSRF Manager initialized in {self.mode.value} mode")
    
    def _apply_config_to_server(self) -> None:
        """Apply CSRF configuration to Flask server"""
        server = self.app.server
        
        config_mapping = {
            'SECRET_KEY': self.config.secret_key,
            'WTF_CSRF_TIME_LIMIT': self.config.time_limit,
            'WTF_CSRF_SSL_STRICT': self.config.ssl_strict,
            'WTF_CSRF_METHODS': self.config.methods,
            'WTF_CSRF_CHECK_DEFAULT': self.config.check_referer,
            'WTF_CSRF_ENABLED': self._should_enable_csrf()
        }
        
        for key, value in config_mapping.items():
            if value is not None:
                server.config[key] = value
    
    def _should_enable_csrf(self) -> bool:
        """Determine if CSRF should be enabled based on mode and config"""
        if not self.config.enabled:
            return False
        
        return self.mode in [CSRFMode.ENABLED, CSRFMode.PRODUCTION]
    
    def _init_csrf_protection(self) -> None:
        """Initialize full CSRF protection"""
        server = self.app.server
        self.csrf_protect = CSRFProtect()
        self.csrf_protect.init_app(server)
        logger.info("CSRF protection enabled")
    
    def _init_development_mode(self) -> None:
        """Initialize development mode (CSRF disabled with warnings)"""
        server = self.app.server
        server.config['WTF_CSRF_ENABLED'] = False
        logger.warning("CSRF protection disabled for development mode")
    
    def _init_testing_mode(self) -> None:
        """Initialize testing mode"""
        server = self.app.server
        server.config.update({
            'WTF_CSRF_ENABLED': False,
            'TESTING': True
        })
        logger.info("CSRF protection disabled for testing mode")
    
    def _init_disabled_mode(self) -> None:
        """Initialize disabled mode"""
        server = self.app.server
        server.config['WTF_CSRF_ENABLED'] = False
        logger.info("CSRF protection explicitly disabled")
    
    def _setup_default_exemptions(self) -> None:
        """Set up default route exemptions for Dash"""
        default_exempt_routes = [
            '/_dash-dependencies',
            '/_dash-layout',
            '/_dash-component-suites',
            '/_dash-update-component',
            '/_favicon.ico',
            '/_reload-hash',
            '/assets/*',
            '/health',
            '/healthz'
        ]
        
        for route in default_exempt_routes:
            self.add_exempt_route(route)
        
        # Add custom exempt routes from config
        for route in self.config.exempt_routes:
            self.add_exempt_route(route)
    
    def _setup_error_handlers(self) -> None:
        """Set up CSRF error handlers"""
        server = self.app.server
        
        @server.errorhandler(400)
        def handle_bad_request(error):
            """Handle CSRF-related bad requests"""
            if self._is_csrf_error(error):
                return self._create_csrf_error_response(error)
            return error
        
        @server.errorhandler(CSRFError)
        def handle_csrf_error(error):
            """Handle custom CSRF errors"""
            return self._create_csrf_error_response(error)
    
    def _is_csrf_error(self, error) -> bool:
        """Check if an error is CSRF-related"""
        error_str = str(error)
        csrf_indicators = ['CSRF', 'csrf', 'token', 'Cross-Site Request Forgery']
        return any(indicator in error_str for indicator in csrf_indicators)
    
    def _create_csrf_error_response(self, error) -> tuple:
        """Create user-friendly CSRF error response"""
        if self.config.custom_error_handler:
            return self.config.custom_error_handler(error)
        
        error_html = self._get_default_error_template()
        return error_html, 400, {'Content-Type': 'text/html'}
    
    def _get_default_error_template(self) -> str:
        """Get default CSRF error template"""
        return """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Security Error</title>
            <link rel="stylesheet" href="/assets/styles/csrf_error.css">
        </head>
        <body>
            <div class="error-container">
                <div class="error-icon">🛡️</div>
                <h1>Security Token Error</h1>
                <div class="error-message">
                    <strong>Security Protection Activated</strong><br>
                    Your session has expired or there was a security token mismatch. 
                    This is a protective measure to keep your data safe.
                </div>
                <p>This can happen when:</p>
                <ul>
                    <li>Your session has been inactive for too long</li>
                    <li>You opened the app in multiple browser tabs</li>
                    <li>There was a network connectivity issue</li>
                </ul>
                <div class="action-buttons">
                    <a href="/" class="btn">Reload Application</a>
                    <a href="/login" class="btn">Sign In Again</a>
                </div>
            </div>
        </body>
        </html>
        """
    
    def add_exempt_route(self, route: str) -> None:
        """Add a route to CSRF exemption list"""
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
        """Add a view function to CSRF exemption list"""
        if view_function not in self._exempt_views:
            self._exempt_views.append(view_function)

            if self.csrf_protect:
                view = self.app.server.view_functions.get(view_function)
                if view:
                    try:
                        self.csrf_protect.exempt(view)
                    except Exception as e:
                        logger.warning(
                            f"Could not exempt view function {view_function}: {e}"
                        )
                else:
                    logger.debug(
                        "View function %s not found when attempting to exempt",
                        view_function,
                    )
    
    def get_csrf_token(self) -> str:
        """Get current CSRF token"""
        if not self._should_enable_csrf():
            return ""
        
        try:
            return generate_csrf()
        except RuntimeError as e:
            logger.warning(f"Could not generate CSRF token: {e}")
            return ""
    
    def validate_csrf(self) -> bool:
        """Validate CSRF token for current request"""
        if not self._should_enable_csrf():
            return True
        
        try:
            # Try to get token from headers first, then form data
            token = (request.headers.get('X-CSRFToken') or 
                    request.headers.get('X-CSRF-Token') or
                    request.form.get('csrf_token'))
            
            if token:
                validate_csrf(token)
                return True
            else:
                logger.warning("No CSRF token found in request")
                return False
                
        except Exception as e:
            logger.warning(f"CSRF validation failed: {e}")
            return False
    
    def create_csrf_component(self, component_id: str = "csrf-token"):
        """Create CSRF component for Dash layout"""
        if not self._should_enable_csrf():
            return html.Div(style={'display': 'none'})
        
        token = self.get_csrf_token()
        
        return html.Div([
            # Store token in a hidden component
            dcc.Store(id=component_id, data={'csrf_token': token}),
            # Also add as meta tag for JavaScript access
            html.Meta(name="csrf-token", content=token)
        ], style={'display': 'none'})
    
    def disable(self) -> None:
        """Temporarily disable CSRF protection"""
        self._enabled = False
        if self.app.server:
            self.app.server.config['WTF_CSRF_ENABLED'] = False
        logger.info("CSRF protection temporarily disabled")
    
    def enable(self) -> None:
        """Re-enable CSRF protection"""
        self._enabled = True
        if self._should_enable_csrf() and self.app.server:
            self.app.server.config['WTF_CSRF_ENABLED'] = True
        logger.info("CSRF protection re-enabled")
    
    def update_config(self, config: CSRFConfig) -> None:
        """Update CSRF configuration"""
        self.config = config
        self._apply_config_to_server()
        logger.info("CSRF configuration updated")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current status of CSRF protection"""
        return {
            'enabled': self.is_enabled,
            'mode': self.mode.value,
            'csrf_protect_initialized': self.csrf_protect is not None,
            'exempt_routes': self._exempt_routes,
            'exempt_views': self._exempt_views,
            'config_enabled': self.config.enabled,
            'server_csrf_enabled': self.app.server.config.get('WTF_CSRF_ENABLED', False)
        }
    
    @property
    def is_enabled(self) -> bool:
        """Check if CSRF protection is currently enabled"""
        return (self._enabled and 
                self.config.enabled and 
                self.mode in [CSRFMode.ENABLED, CSRFMode.PRODUCTION])
    
    def health_check(self) -> Dict[str, Any]:
        """Perform health check on CSRF system"""
        status = {
            'healthy': True,
            'issues': [],
            'recommendations': []
        }
        
        # Check if secret key is set
        if not self.app.server.config.get('SECRET_KEY'):
            status['healthy'] = False
            status['issues'].append('No SECRET_KEY configured')
        
        # Check if secret key is secure
        secret_key = self.app.server.config.get('SECRET_KEY', '')
        if secret_key in ['dev', 'development', 'test', 'secret']:
            status['issues'].append('Insecure SECRET_KEY detected')
            status['recommendations'].append('Use a cryptographically secure secret key')
        
        # Check SSL configuration in production
        if self.mode == CSRFMode.PRODUCTION:
            if not self.config.ssl_strict:
                status['recommendations'].append('Enable SSL strict mode for production')
        
        return status
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get CSRF protection metrics"""
        return {
            'mode': self.mode.value,
            'enabled': self.is_enabled,
            'exempt_routes_count': len(self._exempt_routes),
            'exempt_views_count': len(self._exempt_views),
            'time_limit': self.config.time_limit,
            'methods_protected': len(self.config.methods)
        }
