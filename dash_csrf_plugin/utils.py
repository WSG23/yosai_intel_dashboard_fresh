"""
Utility functions for CSRF protection plugin
"""

import secrets
import hashlib
import logging
from typing import Dict, Any, Optional, List
from urllib.parse import urlparse
import dash
from flask import request, current_app

logger = logging.getLogger(__name__)


class CSRFUtils:
    """Utility class for CSRF-related operations"""
    
    @staticmethod
    def generate_secret_key(length: int = 32) -> str:
        """Generate a cryptographically secure secret key"""
        return secrets.token_urlsafe(length)
    
    @staticmethod
    def is_safe_url(target: str, allowed_hosts: Optional[List[str]] = None) -> bool:
        """Check if a URL is safe for redirects"""
        if not target:
            return False
        
        parsed = urlparse(target)
        
        # Relative URLs are safe
        if not parsed.netloc:
            return True
        
        # Check against allowed hosts
        if allowed_hosts and parsed.netloc in allowed_hosts:
            return True
        
        # Check against current request host
        if hasattr(request, 'host') and parsed.netloc == request.host:
            return True
        
        return False
    
    @staticmethod
    def hash_token(token: str, algorithm: str = 'sha256') -> str:
        """Hash a token using specified algorithm"""
        hasher = hashlib.new(algorithm)
        hasher.update(token.encode('utf-8'))
        return hasher.hexdigest()
    
    @staticmethod
    def detect_dash_app_type(app: dash.Dash) -> str:
        """Detect the type of Dash application"""
        if hasattr(app, '_dev_tools'):
            if app._dev_tools.get('dev_tools_hot_reload', False):
                return 'development'
        
        if hasattr(app, 'server'):
            if app.server.config.get('TESTING', False):
                return 'testing'
            if app.server.config.get('DEBUG', False):
                return 'development'
        
        return 'production'
    
    @staticmethod
    def get_client_ip() -> str:
        """Get client IP address from request"""
        # Check for forwarded headers first
        if request.headers.get('X-Forwarded-For'):
            return request.headers.get('X-Forwarded-For').split(',')[0].strip()
        elif request.headers.get('X-Real-IP'):
            return request.headers.get('X-Real-IP')
        else:
            return request.remote_addr or 'unknown'
    
    @staticmethod
    def log_csrf_attempt(success: bool, details: Dict[str, Any] = None) -> None:
        """Log CSRF validation attempts"""
        details = details or {}
        ip = CSRFUtils.get_client_ip()
        user_agent = request.headers.get('User-Agent', 'unknown')
        
        log_data = {
            'success': success,
            'ip': ip,
            'user_agent': user_agent,
            'path': request.path,
            'method': request.method,
            **details
        }
        
        if success:
            logger.info(f"CSRF validation successful: {log_data}")
        else:
            logger.warning(f"CSRF validation failed: {log_data}")
    
    @staticmethod
    def extract_dash_routes(app: dash.Dash) -> List[str]:
        """Extract Dash-specific routes from application"""
        routes = []
        
        if hasattr(app, 'server') and hasattr(app.server, 'url_map'):
            for rule in app.server.url_map.iter_rules():
                if rule.rule.startswith('/_dash'):
                    routes.append(rule.rule)
        
        return routes
    
    @staticmethod
    def validate_config_security(config_dict: Dict[str, Any]) -> Dict[str, List[str]]:
        """Validate configuration for security issues"""
        issues = {
            'warnings': [],
            'errors': [],
            'recommendations': []
        }
        
        # Check secret key
        secret_key = config_dict.get('secret_key')
        if not secret_key:
            issues['errors'].append('No secret key configured')
        elif len(secret_key) < 16:
            issues['warnings'].append('Secret key is too short (< 16 characters)')
        elif secret_key in ['secret', 'dev', 'test', 'development']:
            issues['errors'].append('Insecure default secret key detected')
        
        # Check SSL settings
        if config_dict.get('ssl_strict', False) == False:
            issues['warnings'].append('SSL strict mode is disabled')
        
        # Check time limit
        time_limit = config_dict.get('time_limit', 3600)
        if time_limit > 86400:  # 24 hours
            issues['warnings'].append('CSRF token time limit is very long (>24h)')
        elif time_limit < 300:  # 5 minutes
            issues['warnings'].append('CSRF token time limit is very short (<5min)')
        
        # Check methods
        methods = config_dict.get('methods', [])
        if 'GET' in methods:
            issues['warnings'].append('GET method should not require CSRF protection')
        
        return issues
    
    @staticmethod
    def create_debug_info(app: dash.Dash, config) -> Dict[str, Any]:
        """Create debug information for troubleshooting"""
        return {
            'dash_version': dash.__version__,
            'flask_config': {
                'SECRET_KEY': '***' if app.server.config.get('SECRET_KEY') else None,
                'WTF_CSRF_ENABLED': app.server.config.get('WTF_CSRF_ENABLED'),
                'DEBUG': app.server.config.get('DEBUG'),
                'TESTING': app.server.config.get('TESTING')
            },
            'csrf_config': config.to_dict(),
            'server_name': app.server.config.get('SERVER_NAME'),
            'app_routes': [rule.rule for rule in app.server.url_map.iter_rules()],
            'request_info': {
                'method': request.method if request else None,
                'path': request.path if request else None,
                'headers': dict(request.headers) if request else None
            }
        }
    
    @staticmethod
    def measure_performance(func):
        """Decorator to measure function performance"""
        import time
        from functools import wraps
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            result = func(*args, **kwargs)
            end_time = time.time()
            
            logger.debug(f"{func.__name__} took {end_time - start_time:.4f} seconds")
            return result
        
        return wrapper
