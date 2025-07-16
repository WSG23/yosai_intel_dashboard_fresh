# plugins/compliance_plugin/__init__.py
"""
GDPR/APPI Compliance Plugin for Yōsai Intel Dashboard

A complete compliance framework implemented as a plugin that can be
enabled/disabled independently from the core application.
"""

from .plugin import CompliancePlugin

__version__ = "1.0.0"
__plugin_name__ = "compliance_plugin"
__description__ = "GDPR/APPI compliance framework with consent management, DSAR processing, and audit logging"

# Plugin entry point
def create_plugin():
    """Create and return the compliance plugin instance"""
    return CompliancePlugin()

# plugins/compliance_plugin/plugin.py
"""Main compliance plugin class"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from pathlib import Path

from core.plugins.base import BasePlugin
from core.container import Container
from .services import ComplianceServices
from .api import ComplianceAPI
from .middleware import ComplianceMiddleware
from .database import ComplianceDatabase
from .config import ComplianceConfig

logger = logging.getLogger(__name__)


class CompliancePlugin(BasePlugin):
    """
    Main compliance plugin that provides GDPR/APPI compliance features
    as an optional add-on to the core application
    """
    
    def __init__(self):
        super().__init__()
        self.name = "compliance_plugin"
        self.version = "1.0.0"
        self.description = "GDPR/APPI compliance framework"
        self.author = "Yōsai Intel Compliance Team"
        self.dependencies = []  # No dependencies on other plugins
        
        # Plugin components
        self.services: Optional[ComplianceServices] = None
        self.api: Optional[ComplianceAPI] = None
        self.middleware: Optional[ComplianceMiddleware] = None
        self.database: Optional[ComplianceDatabase] = None
        self.config: Optional[ComplianceConfig] = None
        
        # Plugin state
        self.is_initialized = False
        self.is_database_ready = False
        
    def initialize(self, container: Container, config: Dict[str, Any]) -> bool:
        """Initialize the compliance plugin"""
        try:
            logger.info("Initializing Compliance Plugin v%s", self.version)
            
            # 1. Load plugin configuration
            self.config = ComplianceConfig(config.get('compliance', {}))
            
            if not self.config.enabled:
                logger.info("Compliance plugin is disabled in configuration")
                return True
            
            # 2. Initialize database components
            self.database = ComplianceDatabase(container.get('database'))
            if not self.database.ensure_schema():
                logger.error("Failed to initialize compliance database schema")
                return False
            self.is_database_ready = True
            
            # 3. Initialize services
            self.services = ComplianceServices(container, self.config)
            if not self.services.initialize():
                logger.error("Failed to initialize compliance services")
                return False
            
            # 4. Register services with DI container
            self._register_services_with_container(container)
            
            # 5. Initialize API endpoints
            self.api = ComplianceAPI(container, self.config)
            
            # 6. Initialize middleware
            self.middleware = ComplianceMiddleware(container, self.config)
            
            self.is_initialized = True
            logger.info("Compliance plugin initialized successfully")
            return True
            
        except Exception as e:
            logger.error("Failed to initialize compliance plugin: %s", e)
            return False
    
    def register_routes(self, app) -> bool:
        """Register compliance API routes with Flask app"""
        if not self.is_initialized or not self.api:
            logger.warning("Cannot register routes - plugin not initialized")
            return False
        
        try:
            # Register compliance API routes
            self.api.register_routes(app)
            
            # Register middleware
            if self.middleware:
                self.middleware.register_middleware(app)
            
            logger.info("Compliance plugin routes registered")
            return True
            
        except Exception as e:
            logger.error("Failed to register compliance routes: %s", e)
            return False
    
    def get_hooks(self) -> Dict[str, Any]:
        """Return hooks that integrate with core application workflows"""
        if not self.is_initialized:
            return {}
        
        return {
            # CSV processing hooks
            'csv_upload_pre_process': self._hook_csv_pre_process,
            'csv_upload_post_process': self._hook_csv_post_process,
            'csv_data_access': self._hook_csv_data_access,
            'csv_data_deletion': self._hook_csv_data_deletion,
            
            # User management hooks
            'user_registration': self._hook_user_registration,
            'user_deletion': self._hook_user_deletion,
            'user_data_export': self._hook_user_data_export,
            
            # Biometric processing hooks
            'biometric_processing_pre': self._hook_biometric_pre_process,
            'biometric_processing_post': self._hook_biometric_post_process,
            
            # Analytics hooks
            'analytics_access_request': self._hook_analytics_access_request,
            'analytics_processing': self._hook_analytics_processing,
            
            # System hooks
            'daily_maintenance': self._hook_daily_maintenance,
            'health_check': self._hook_health_check
        }
    
    def get_dashboard_widgets(self) -> List[Dict[str, Any]]:
        """Return dashboard widgets for compliance monitoring"""
        if not self.is_initialized or not self.services:
            return []
        
        return [
            {
                'id': 'compliance_score',
                'title': 'Compliance Score',
                'type': 'metric_card',
                'component': 'ComplianceScoreWidget',
                'data_source': '/api/v1/compliance/dashboard/score',
                'refresh_interval': 300  # 5 minutes
            },
            {
                'id': 'consent_status',
                'title': 'Consent Management',
                'type': 'chart',
                'component': 'ConsentStatusChart',
                'data_source': '/api/v1/compliance/dashboard/consent',
                'refresh_interval': 600  # 10 minutes
            },
            {
                'id': 'dsar_queue',
                'title': 'DSAR Requests',
                'type': 'table',
                'component': 'DSARQueueTable',
                'data_source': '/api/v1/compliance/dashboard/dsar',
                'refresh_interval': 300
            },
            {
                'id': 'compliance_alerts',
                'title': 'Compliance Alerts',
                'type': 'alert_list',
                'component': 'ComplianceAlerts',
                'data_source': '/api/v1/compliance/dashboard/alerts',
                'refresh_interval': 60  # 1 minute
            }
        ]
    
    def shutdown(self) -> bool:
        """Shutdown the compliance plugin"""
        try:
            logger.info("Shutting down compliance plugin")
            
            # Stop background services
            if self.services:
                self.services.shutdown()
            
            # Clean up resources
            self.is_initialized = False
            logger.info("Compliance plugin shutdown complete")
            return True
            
        except Exception as e:
            logger.error("Error during compliance plugin shutdown: %s", e)
            return False
    
    def get_plugin_info(self) -> Dict[str, Any]:
        """Return plugin information for admin interface"""
        return {
            'name': self.name,
            'version': self.version,
            'description': self.description,
            'author': self.author,
            'status': 'active' if self.is_initialized else 'inactive',
            'database_ready': self.is_database_ready,
            'features': [
                'Consent Management',
                'Data Subject Rights (DSAR)',
                'Audit Logging',
                'Data Retention',
                'Breach Notification',
                'Cross-Border Transfers',
                'DPIA Automation',
                'Compliance Dashboard'
            ],
            'configuration': self.config.to_dict() if self.config else {},
            'health_status': self._get_health_status()
        }
    
    # Hook implementations
    def _hook_csv_pre_process(self, **kwargs) -> Dict[str, Any]:
        """Hook called before CSV processing"""
        if not self.services or not self.services.csv_processor:
            return {'status': 'proceed'}
        
        file_path = kwargs.get('file_path')
        upload_context = kwargs.get('upload_context', {})
        uploaded_by = kwargs.get('uploaded_by')
        
        # Run compliance analysis
        result = self.services.csv_processor.analyze_csv_compliance(
            file_path, upload_context, uploaded_by
        )
        
        if not result.get('authorized', True):
            return {
                'status': 'block',
                'reason': result.get('reason', 'Compliance check failed'),
                'details': result
            }
        
        return {
            'status': 'proceed',
            'compliance_metadata': result
        }
    
    def _hook_csv_post_process(self, **kwargs) -> Dict[str, Any]:
        """Hook called after CSV processing"""
        if not self.services:
            return {}
        
        # Apply retention policies and audit logging
        processing_id = kwargs.get('processing_id')
        compliance_metadata = kwargs.get('compliance_metadata', {})
        
        if processing_id and compliance_metadata:
            self.services.retention_service.apply_csv_retention_policy(
                processing_id, compliance_metadata
            )
        
        return {}
    
    def _hook_biometric_pre_process(self, **kwargs) -> Dict[str, Any]:
        """Hook called before biometric processing"""
        if not self.services or not self.services.consent_service:
            return {'status': 'proceed'}
        
        user_id = kwargs.get('user_id')
        processing_type = kwargs.get('processing_type', 'biometric_access')
        
        # Check consent
        from .models import ConsentType
        consent_type = ConsentType.FACIAL_RECOGNITION if 'facial' in processing_type else ConsentType.BIOMETRIC_ACCESS
        
        has_consent = self.services.consent_service.check_consent(
            user_id=user_id,
            consent_type=consent_type,
            jurisdiction='EU'
        )
        
        if not has_consent:
            return {
                'status': 'block',
                'reason': f'No consent for {processing_type}',
                'consent_required': consent_type.value
            }
        
        return {'status': 'proceed'}
    
    def _hook_daily_maintenance(self, **kwargs) -> Dict[str, Any]:
        """Hook called during daily maintenance"""
        if not self.services:
            return {}
        
        # Run automated data retention
        if self.services.retention_service:
            deleted_count = self.services.retention_service.process_scheduled_deletions()
            logger.info("Compliance maintenance: processed %d scheduled deletions", deleted_count)
        
        return {'deleted_records': deleted_count if 'deleted_count' in locals() else 0}
    
    def _register_services_with_container(self, container: Container) -> None:
        """Register compliance services with the DI container"""
        if not self.services:
            return
        
        # Register all compliance services
        container.register('compliance_audit_logger', self.services.audit_logger)
        container.register('compliance_consent_service', self.services.consent_service)
        container.register('compliance_dsar_service', self.services.dsar_service)
        container.register('compliance_retention_service', self.services.retention_service)
        container.register('compliance_dpia_service', self.services.dpia_service)
        container.register('compliance_dashboard', self.services.dashboard)
        container.register('compliance_csv_processor', self.services.csv_processor)
        
        # Register plugin itself for access to hooks
        container.register('compliance_plugin', self)
    
    def _get_health_status(self) -> Dict[str, Any]:
        """Get health status of compliance plugin"""
        if not self.is_initialized:
            return {'status': 'inactive', 'issues': ['Plugin not initialized']}
        
        issues = []
        
        # Check database connectivity
        if not self.is_database_ready:
            issues.append('Database schema not ready')
        
        # Check services
        if not self.services or not self.services.is_healthy():
            issues.append('Services not healthy')
        
        return {
            'status': 'healthy' if not issues else 'degraded',
            'issues': issues,
            'last_check': self._get_current_timestamp()
        }


# plugins/compliance_plugin/config.py
"""Compliance plugin configuration"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Any, List


@dataclass
class ComplianceConfig:
    """Configuration for compliance plugin"""
    
    # Core settings
    enabled: bool = True
    jurisdiction: str = 'EU'  # Primary jurisdiction
    
    # Consent management
    consent_enabled: bool = True
    default_consent_jurisdiction: str = 'EU'
    require_explicit_consent: bool = True
    consent_withdrawal_immediate: bool = True
    
    # Data retention
    retention_enabled: bool = True
    automated_cleanup: bool = True
    cleanup_schedule: str = "02:00"  # Daily at 2 AM
    grace_period_days: int = 30
    
    # Audit logging
    audit_enabled: bool = True
    audit_retention_days: int = 2555  # 7 years
    audit_encryption_enabled: bool = True
    
    # DSAR processing
    dsar_enabled: bool = True
    dsar_response_time_hours: int = 72
    dsar_auto_processing: bool = False
    
    # Breach notification
    breach_notification_enabled: bool = True
    supervisor_notification_hours: int = 72
    individual_notification_enabled: bool = True
    
    # Cross-border transfers
    transfer_assessment_enabled: bool = True
    adequacy_monitoring: bool = True
    
    # Dashboard and monitoring
    dashboard_enabled: bool = True
    alerts_enabled: bool = True
    email_notifications: bool = False
    compliance_officer_email: str = ""
    
    # CSV processing
    csv_compliance_enabled: bool = True
    csv_auto_classification: bool = True
    csv_consent_checking: bool = True
    
    def __init__(self, config_dict: Dict[str, Any]):
        """Initialize from configuration dictionary"""
        for key, value in config_dict.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            field.name: getattr(self, field.name)
            for field in self.__dataclass_fields__.values()
        }


# plugins/compliance_plugin/services/__init__.py
"""Compliance services container"""

from __future__ import annotations

import logging
from typing import Optional

from core.container import Container
from .audit_logger import ComplianceAuditLogger
from .consent_service import ConsentService
from .dsar_service import DSARService
from .retention_service import DataRetentionService
from .dpia_service import DPIAService
from .dashboard import ComplianceDashboard
from .csv_processor import ComplianceCSVProcessor

logger = logging.getLogger(__name__)


class ComplianceServices:
    """Container for all compliance services"""
    
    def __init__(self, container: Container, config):
        self.container = container
        self.config = config
        
        # Initialize services
        self.audit_logger: Optional[ComplianceAuditLogger] = None
        self.consent_service: Optional[ConsentService] = None
        self.dsar_service: Optional[DSARService] = None
        self.retention_service: Optional[DataRetentionService] = None
        self.dpia_service: Optional[DPIAService] = None
        self.dashboard: Optional[ComplianceDashboard] = None
        self.csv_processor: Optional[ComplianceCSVProcessor] = None
        
    def initialize(self) -> bool:
        """Initialize all compliance services"""
        try:
            db = self.container.get('database')
            
            # Initialize in dependency order
            if self.config.audit_enabled:
                self.audit_logger = ComplianceAuditLogger(db)
            
            if self.config.consent_enabled and self.audit_logger:
                self.consent_service = ConsentService(db, self.audit_logger)
            
            if self.config.dsar_enabled and self.audit_logger:
                self.dsar_service = DSARService(db, self.audit_logger)
            
            if self.config.retention_enabled and self.audit_logger:
                self.retention_service = DataRetentionService(db, self.audit_logger)
            
            if self.audit_logger:
                self.dpia_service = DPIAService(db, self.audit_logger)
            
            if self.config.dashboard_enabled:
                self.dashboard = ComplianceDashboard(
                    db, self.audit_logger, self.consent_service,
                    self.dsar_service, self.retention_service, self.dpia_service
                )
            
            if self.config.csv_compliance_enabled:
                self.csv_processor = ComplianceCSVProcessor(
                    db, self.audit_logger, self.consent_service, self.retention_service
                )
            
            logger.info("Compliance services initialized successfully")
            return True
            
        except Exception as e:
            logger.error("Failed to initialize compliance services: %s", e)
            return False
    
    def shutdown(self) -> None:
        """Shutdown all services"""
        # Stop background tasks, close connections, etc.
        if self.retention_service:
            self.retention_service.stop_scheduler()
    
    def is_healthy(self) -> bool:
        """Check if all services are healthy"""
        # Implement health checks for each service
        return True


# plugins/compliance_plugin/plugin_manifest.yaml
# The following YAML manifest is included for reference only.
PLUGIN_MANIFEST = """
name: compliance_plugin
version: 1.0.0
description: GDPR/APPI compliance framework
author: Yōsai Intel Compliance Team
homepage: https://github.com/yosai-intel/compliance-plugin
license: MIT

# Plugin metadata
category: compliance
tags: [gdpr, appi, privacy, consent, audit]

# Dependencies
dependencies:
  python: ">=3.8"
  packages:
    - pandas>=1.3.0
    - sqlalchemy>=1.4.0

# Configuration schema
config_schema:
  type: object
  properties:
    enabled:
      type: boolean
      default: true
      description: "Enable compliance plugin"

    jurisdiction:
      type: string
      enum: [EU, JP, US, CA]
      default: EU
      description: "Primary jurisdiction for compliance"

    consent_enabled:
      type: boolean
      default: true
      description: "Enable consent management"

    audit_enabled:
      type: boolean
      default: true
      description: "Enable audit logging"

    retention_enabled:
      type: boolean
      default: true
      description: "Enable automated data retention"

# Hooks provided by this plugin
hooks:
  - csv_upload_pre_process
  - csv_upload_post_process
  - biometric_processing_pre
  - biometric_processing_post
  - user_registration
  - user_deletion
  - daily_maintenance

# API endpoints provided
api_endpoints:
  - path: /api/v1/compliance/consent
    methods: [POST, DELETE, GET]
  - path: /api/v1/compliance/dsar
    methods: [POST, GET]
  - path: /api/v1/compliance/dashboard
    methods: [GET]

# Database tables created by this plugin
database_tables:
  - consent_log
  - dsar_requests
  - compliance_audit_log
  - data_retention_policies

# Dashboard widgets
dashboard_widgets:
  - id: compliance_score
    title: "Compliance Score"
    type: metric_card
  - id: consent_status
    title: "Consent Management"
    type: chart
"""


# plugins/compliance_plugin/install.py
"""Installation and setup script for compliance plugin"""

import logging
from pathlib import Path
from typing import Dict, Any

logger = logging.getLogger(__name__)


def install_plugin(container, config: Dict[str, Any]) -> bool:
    """Install the compliance plugin"""
    try:
        logger.info("Installing compliance plugin...")
        
        # 1. Create database schema
        db = container.get('database')
        schema_path = Path(__file__).parent / 'database' / 'schema.sql'
        
        if schema_path.exists():
            with open(schema_path, 'r') as f:
                schema_sql = f.read()
            db.execute_command(schema_sql)
            logger.info("Compliance database schema created")
        
        # 2. Create default configuration
        default_config = {
            'compliance': {
                'enabled': True,
                'jurisdiction': 'EU',
                'consent_enabled': True,
                'audit_enabled': True,
                'retention_enabled': True
            }
        }
        
        # 3. Set up plugin directory structure
        plugin_dir = Path(__file__).parent
        directories = ['logs', 'data', 'exports', 'config']
        
        for directory in directories:
            (plugin_dir / directory).mkdir(exist_ok=True)
        
        logger.info("Compliance plugin installed successfully")
        return True
        
    except Exception as e:
        logger.error("Failed to install compliance plugin: %s", e)
        return False


def uninstall_plugin(container) -> bool:
    """Uninstall the compliance plugin"""
    try:
        logger.info("Uninstalling compliance plugin...")
        
        # 1. Drop database tables (with confirmation)
        db = container.get('database')
        
        # WARNING: This will delete all compliance data!
        drop_tables = [
            'DROP TABLE IF EXISTS compliance_audit_log',
            'DROP TABLE IF EXISTS dsar_requests', 
            'DROP TABLE IF EXISTS consent_log',
            'DROP TABLE IF EXISTS data_retention_policies'
        ]
        
        for sql in drop_tables:
            db.execute_command(sql)
        
        logger.info("Compliance plugin uninstalled")
        return True
        
    except Exception as e:
        logger.error("Failed to uninstall compliance plugin: %s", e)
        return False


# Core application integration points
# =============================================================================

# In your main app factory, modify to support compliance plugin:

def create_app_with_compliance_plugin(config_name: str = None) -> Flask:
    """
    Enhanced app factory that automatically loads compliance plugin if available
    """
    app = Flask(__name__)
    
    # Load configuration
    config_manager = create_config_manager()
    app.config.update(config_manager.get_app_config().__dict__)
    
    # Create DI container
    container = Container()
    container.register('config', config_manager)
    
    # Setup database
    db = create_database_connection()
    container.register('database', db)
    
    # Initialize plugin manager
    from core.plugins.performance_manager import EnhancedThreadSafePluginManager
    plugin_manager = EnhancedThreadSafePluginManager(container, config_manager)
    
    # Try to load compliance plugin
    try:
        compliance_plugin = plugin_manager.load_plugin('compliance_plugin')
        if compliance_plugin and compliance_plugin.initialize(container, config_manager.to_dict()):
            # Register compliance routes
            compliance_plugin.register_routes(app)
            
            # Register hooks with application
            hooks = compliance_plugin.get_hooks()
            app.compliance_hooks = hooks  # Store for use in CSV processing
            
            logger.info("Compliance plugin loaded successfully")
        else:
            logger.info("Compliance plugin not available or failed to initialize")
            app.compliance_hooks = {}
            
    except ImportError:
        logger.info("Compliance plugin not installed")
        app.compliance_hooks = {}
    
    # Register your existing services
    # ... your current service registration code ...
    
    # Store container in app
    app.container = container
    app.plugin_manager = plugin_manager
    
    return app


# Enhanced CSV upload route that uses plugin hooks
def create_csv_upload_route_with_plugin_support():
    """
    Example of how to modify your existing CSV upload to use compliance plugin hooks
    """
    
    @app.route('/api/upload/csv', methods=['POST'])
    @login_required
    def upload_csv_with_plugin_hooks():
        """CSV upload that automatically uses compliance plugin if available"""
        
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        file_path = save_uploaded_file(file)
        
        # Get upload context
        upload_context = {
            'processing_purpose': request.form.get('purpose', ''),
            'data_source': request.form.get('data_source', ''),
            'consent_confirmed': request.form.get('consent_confirmed') == 'true',
            'uploaded_by': current_user.id
        }
        
        try:
            # Call pre-process hook (compliance plugin will intercept if loaded)
            pre_process_result = call_hook('csv_upload_pre_process', 
                file_path=file_path,
                upload_context=upload_context,
                uploaded_by=current_user.id
            )
            
            # Check if compliance plugin blocked the upload
            if pre_process_result.get('status') == 'block':
                return jsonify({
                    'status': 'denied',
                    'reason': pre_process_result.get('reason'),
                    'details': pre_process_result.get('details', {})
                }), 403
            
            # Process CSV normally
            df = pd.read_csv(file_path)
            processing_id = str(uuid4())
            
            # Your existing processing logic
            processed_data = process_csv_data(df)
            
            # Store processed data
            store_csv_results(processing_id, processed_data)
            
            # Call post-process hook (compliance plugin handles retention, audit, etc.)
            call_hook('csv_upload_post_process',
                processing_id=processing_id,
                file_path=file_path,
                compliance_metadata=pre_process_result.get('compliance_metadata', {}),
                processed_data=processed_data
            )
            
            return jsonify({
                'status': 'success',
                'processing_id': processing_id,
                'rows_processed': len(processed_data),
                'compliance_status': pre_process_result.get('compliance_metadata', {})
            })
            
        except Exception as e:
            logger.error("CSV upload failed: %s", e)
            return jsonify({'error': 'Upload processing failed'}), 500


def call_hook(hook_name: str, **kwargs) -> Dict[str, Any]:
    """Helper function to call plugin hooks if they exist"""
    hooks = getattr(app, 'compliance_hooks', {})
    
    if hook_name in hooks:
        try:
            return hooks[hook_name](**kwargs)
        except Exception as e:
            logger.error("Hook %s failed: %s", hook_name, e)
            return {}
    
    return {}


# Plugin management commands for administrators
# =============================================================================

def compliance_plugin_admin_commands():
    """
    Administrative commands for managing the compliance plugin
    """
    
    import click
    
    @click.group()
    def compliance():
        """Compliance plugin management commands"""
        pass
    
    @compliance.command()
    def install():
        """Install the compliance plugin"""
        container = Container()
        # ... initialize container ...
        
        if install_plugin(container, {}):
            click.echo("✅ Compliance plugin installed successfully")
        else:
            click.echo("❌ Failed to install compliance plugin")
    
    @compliance.command()
    def uninstall():
        """Uninstall the compliance plugin"""
        if click.confirm('This will delete all compliance data. Are you sure?'):
            container = Container()
            # ... initialize container ...
            
            if uninstall_plugin(container):
                click.echo("✅ Compliance plugin uninstalled")
            else:
                click.echo("❌ Failed to uninstall compliance plugin")
    
    @compliance.command()
    def status():
        """Check compliance plugin status"""
        # Check if plugin is loaded and healthy
        # Display configuration, health status, etc.
        pass
    
    @compliance.command()
    def config():
        """Show compliance plugin configuration"""
        # Display current configuration
        pass
    
    return compliance