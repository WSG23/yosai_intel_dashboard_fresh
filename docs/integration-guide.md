# COMPLETE COMPLIANCE FRAMEWORK INTEGRATION GUIDE
"""
Complete step-by-step integration guide for GDPR/APPI compliance framework
into your existing Yōsai Intel application
"""

# =============================================================================
# STEP 1: Update your main app.py to include compliance
# =============================================================================

# Replace your existing app.py with this pattern:

from flask import Flask
from flask_login import login_required
from config import create_config_manager
from yosai_intel_dashboard.src.core.error_handlers import register_error_handlers
from yosai_intel_dashboard.src.core.container import Container
from database.connection import create_database_connection

# Import all compliance components
from config.compliance_setup import (
    setup_compliance_services,
    ensure_compliance_schema,
    register_compliance_middleware,
    audit_decorator,
    consent_required,
    setup_data_retention_scheduler
)
from controllers.compliance_controller import register_compliance_routes
from yosai_intel_dashboard.src.services.compliance.breach_notification_service import create_breach_notification_service
from yosai_intel_dashboard.src.services.compliance.cross_border_transfer_service import create_cross_border_transfer_service
from yosai_intel_dashboard.src.services.compliance.compliance_dashboard import create_compliance_dashboard
from yosai_intel_dashboard.src.services.compliance.data_retention_service import create_data_retention_service
from yosai_intel_dashboard.src.services.compliance.dpia_service import create_dpia_service

def create_app(config_name: str = None) -> Flask:
    """
    Enhanced app factory with full compliance integration
    """
    app = Flask(__name__)
    register_error_handlers(app)
    
    # Load configuration
    config_manager = create_config_manager()
    app.config.update(config_manager.get_app_config().__dict__)
    
    # Create DI container
    container = Container()
    container.register('config', config_manager)
    
    # Setup database
    db = create_database_connection()
    container.register('database', db)
    
    # =========================================================================
    # COMPLIANCE INTEGRATION - Critical Section
    # =========================================================================
    
    # 1. Ensure database schema includes compliance tables
    try:
        if not ensure_compliance_schema(db):
            app.logger.warning("Failed to setup compliance database schema")
            # In production, you might want to fail here
    except Exception as e:
        app.logger.error(f"Compliance schema setup failed: {e}")
        if app.config.get('ENVIRONMENT') == 'production':
            raise  # Fail fast in production
    
    # 2. Register all compliance services with DI container
    setup_compliance_services(container)
    
    # 3. Register additional compliance services
    audit_logger = container.get('audit_logger')
    
    # Breach notification service
    breach_service = create_breach_notification_service(db, audit_logger)
    container.register('breach_notification_service', breach_service)
    
    # Cross-border transfer service
    transfer_service = create_cross_border_transfer_service(db, audit_logger)
    container.register('cross_border_transfer_service', transfer_service)
    
    # Data retention service
    retention_service = create_data_retention_service(db, audit_logger)
    container.register('data_retention_service', retention_service)
    
    # DPIA service
    dpia_service = create_dpia_service(db, audit_logger)
    container.register('dpia_service', dpia_service)
    
    # Compliance dashboard
    dashboard = create_compliance_dashboard(
        db, audit_logger, 
        container.get('consent_service'),
        container.get('dsar_service'),
        retention_service,
        dpia_service
    )
    container.register('compliance_dashboard', dashboard)
    
    # 4. Register compliance middleware (audit trails, request IDs, etc.)
    register_compliance_middleware(app)
    
    # 5. Register compliance API routes
    register_compliance_routes(app)
    
    # 6. Setup automated data retention (background processing)
    setup_data_retention_scheduler()
    
    # =========================================================================
    # Your existing service registrations go here
    # =========================================================================
    
    # Register your existing services (analytics, etc.)
    # ... your current service registration code ...
    
    # Store container in app for access in views
    app.container = container
    
    # Example of how to modify existing routes with compliance decorators
    @app.route('/api/users/<user_id>/profile')
    @login_required
    @audit_decorator('VIEW_USER_PROFILE', 'user_profile')
    def get_user_profile(user_id: str):
        """Enhanced user profile endpoint with automatic audit logging"""
        # Your existing profile logic
        profile_data = get_user_profile_data(user_id)
        return jsonify(profile_data)
    
    @app.route('/api/biometric/process')
    @login_required
    @consent_required('facial_recognition', 'EU')  # Requires consent before processing
    @audit_decorator('BIOMETRIC_PROCESSING', 'biometric_data')
    def process_biometric_data():
        """Biometric processing with automatic consent verification"""
        # Your existing biometric processing logic
        # This will only execute if user has valid consent
        return jsonify({'status': 'processed'})
    
    return app


# =============================================================================
# STEP 2: Update existing models to include compliance fields
# =============================================================================

# Update your existing models/base.py:

def upgrade_existing_people_table():
    """
    SQL to upgrade your existing people table with compliance fields
    Run this as a database migration
    """
    upgrade_sql = """
    -- Add compliance fields to existing people table
    ALTER TABLE people ADD COLUMN IF NOT EXISTS data_sensitivity_level VARCHAR(20) DEFAULT 'internal';
    ALTER TABLE people ADD COLUMN IF NOT EXISTS consent_status JSONB DEFAULT '{}';
    ALTER TABLE people ADD COLUMN IF NOT EXISTS data_retention_date TIMESTAMP WITH TIME ZONE;
    ALTER TABLE people ADD COLUMN IF NOT EXISTS last_consent_update TIMESTAMP WITH TIME ZONE;
    
    -- Add compliance fields to access_events table
    ALTER TABLE access_events ADD COLUMN IF NOT EXISTS contains_biometric_data BOOLEAN DEFAULT FALSE;
    ALTER TABLE access_events ADD COLUMN IF NOT EXISTS data_sensitivity_level VARCHAR(20) DEFAULT 'confidential';
    ALTER TABLE access_events ADD COLUMN IF NOT EXISTS legal_basis VARCHAR(50) DEFAULT 'legitimate_interests';
    
    -- Add indexes for compliance queries
    CREATE INDEX IF NOT EXISTS idx_people_data_retention_date ON people(data_retention_date);
    CREATE INDEX IF NOT EXISTS idx_people_consent_status ON people USING gin(consent_status);
    CREATE INDEX IF NOT EXISTS idx_access_events_contains_biometric ON access_events(contains_biometric_data);
    """
    return upgrade_sql


# =============================================================================
# STEP 3: Enhanced service layer with compliance integration
# =============================================================================

# Update your existing services to include compliance:

from flask_login import current_user
from yosai_intel_dashboard.src.core.container import Container

class EnhancedAnalyticsService:
    """
    Example of how to enhance existing services with compliance
    """
    
    def __init__(self, db, audit_logger):
        self.db = db
        self.audit_logger = audit_logger
    
    def analyze_access_patterns(self, user_id: str, days: int = 30) -> Dict[str, Any]:
        """Enhanced analytics with consent checking and audit logging"""
        
        # Get compliance services
        container = Container()
        consent_service = container.get('consent_service')
        
        # Check if we have consent for behavioral analysis
        has_consent = consent_service.check_consent(
            user_id=user_id,
            consent_type=ConsentType.BEHAVIORAL_ANALYSIS,
            jurisdiction='EU'
        )
        
        if not has_consent:
            # Log the denied access
            self.audit_logger.log_action(
                actor_user_id=current_user.id if current_user.is_authenticated else 'system',
                target_user_id=user_id,
                action_type='ANALYTICS_ACCESS_DENIED',
                resource_type='behavioral_data',
                description='Behavioral analysis denied - no consent',
                legal_basis='consent_required'
            )
            
            # Return limited analysis or request consent
            return {
                'error': 'Consent required for behavioral analysis',
                'consent_required': True,
                'consent_type': 'behavioral_analysis'
            }
        
        # Proceed with analysis
        analysis_data = self._perform_analysis(user_id, days)
        
        # Audit the analysis
        self.audit_logger.log_data_access(
            actor_user_id=current_user.id if current_user.is_authenticated else 'system',
            target_user_id=user_id,
            data_accessed=['access_patterns', 'behavioral_data'],
            purpose='security_analytics',
            legal_basis='consent'
        )
        
        return analysis_data


# =============================================================================
# STEP 4: Frontend integration for consent management
# =============================================================================

# Add to your Dash callbacks or Flask templates:

CONSENT_MANAGEMENT_UI = """
<!-- Add this to your user profile page or settings -->
<div class="consent-management-section">
    <h3>Privacy Preferences</h3>
    <div class="consent-options">
        <div class="consent-item">
            <input type="checkbox" id="biometric-consent" data-consent-type="biometric_access">
            <label for="biometric-consent">
                Allow biometric data processing for secure access
                <span class="consent-info">Required for facial recognition and fingerprint access</span>
            </label>
        </div>
        
        <div class="consent-item">
            <input type="checkbox" id="analytics-consent" data-consent-type="behavioral_analysis">
            <label for="analytics-consent">
                Allow behavioral analysis for security monitoring
                <span class="consent-info">Helps detect unusual access patterns</span>
            </label>
        </div>
        
        <div class="consent-item">
            <input type="checkbox" id="location-consent" data-consent-type="location_tracking">
            <label for="location-consent">
                Allow location tracking for enhanced security
                <span class="consent-info">Tracks device location during access attempts</span>
            </label>
        </div>
    </div>
    
    <button id="save-consent-preferences">Save Preferences</button>
    <button id="download-my-data">Download My Data</button>
    <button id="delete-my-data" class="danger-button">Delete My Data</button>
</div>

<script>
// Consent management JavaScript
document.getElementById('save-consent-preferences').onclick = function() {
    const consents = [];
    document.querySelectorAll('.consent-item input[type="checkbox"]:checked').forEach(checkbox => {
        consents.push(checkbox.dataset.consentType);
    });
    
    // Save consents via API
    fetch('/api/v1/compliance/consent', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            consents: consents,
            jurisdiction: 'EU'
        })
    }).then(response => response.json())
      .then(data => alert('Preferences saved successfully'));
};

document.getElementById('download-my-data').onclick = function() {
    // Request data export
    fetch('/api/v1/compliance/dsar/request', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            request_type: 'access',
            email: userEmail,  // Get from user session
            jurisdiction: 'EU'
        })
    }).then(response => response.json())
      .then(data => alert('Data export request submitted. You will receive an email when ready.'));
};

document.getElementById('delete-my-data').onclick = function() {
    if (confirm('Are you sure you want to permanently delete all your data? This cannot be undone.')) {
        fetch('/api/v1/compliance/dsar/request', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                request_type: 'erasure',
                email: userEmail,
                jurisdiction: 'EU'
            })
        }).then(response => response.json())
          .then(data => alert('Data deletion request submitted.'));
    }
};
</script>
"""


# =============================================================================
# STEP 5: Compliance monitoring dashboard integration
# =============================================================================

# Add to your existing Dash app or create new compliance dashboard:

import dash
from dash import dcc, html, Input, Output, callback
import plotly.graph_objs as go

def create_compliance_dashboard_layout():
    """Create compliance monitoring dashboard layout"""
    return html.Div([
        html.H1("Compliance Dashboard", className="dashboard-title"),
        
        # Summary cards
        html.Div([
            html.Div([
                html.H3("Overall Compliance Score"),
                html.H2(id="compliance-score", children="--"),
                html.P("Based on all compliance metrics")
            ], className="metric-card"),
            
            html.Div([
                html.H3("Active Consents"),
                html.H2(id="active-consents", children="--"),
                html.P("Users with valid consents")
            ], className="metric-card"),
            
            html.Div([
                html.H3("Pending DSARs"),
                html.H2(id="pending-dsars", children="--"),
                html.P("Data subject requests to process")
            ], className="metric-card"),
            
            html.Div([
                html.H3("Compliance Alerts"),
                html.H2(id="compliance-alerts", children="--"),
                html.P("Issues requiring attention")
            ], className="metric-card critical"),
        ], className="metrics-row"),
        
        # Charts
        html.Div([
            html.Div([
                html.H3("DSAR Response Times"),
                dcc.Graph(id="dsar-response-chart")
            ], className="chart-container"),
            
            html.Div([
                html.H3("Consent Breakdown"),
                dcc.Graph(id="consent-breakdown-chart")
            ], className="chart-container"),
        ], className="charts-row"),
        
        # Alerts table
        html.Div([
            html.H3("Active Compliance Alerts"),
            html.Div(id="alerts-table")
        ], className="alerts-section"),
        
        # Auto-refresh
        dcc.Interval(
            id='compliance-refresh',
            interval=30*1000,  # Refresh every 30 seconds
            n_intervals=0
        )
    ])

@callback(
    [Output('compliance-score', 'children'),
     Output('active-consents', 'children'),
     Output('pending-dsars', 'children'),
     Output('compliance-alerts', 'children')],
    [Input('compliance-refresh', 'n_intervals')]
)
def update_compliance_metrics(n):
    """Update compliance dashboard metrics"""
    try:
        # Get dashboard data from compliance service
        container = Container()
        dashboard = container.get('compliance_dashboard')
        data = dashboard.get_dashboard_summary()
        
        score = data.get('overall_compliance', {}).get('score', 0)
        consents = data.get('metrics_by_category', {}).get('consent_management', {}).get('active_consents', {}).get('value', 0)
        dsars = data.get('metrics_by_category', {}).get('data_subject_rights', {}).get('pending_dsars_due_soon', {}).get('value', 0)
        alerts = data.get('alerts_summary', {}).get('total_alerts', 0)
        
        return f"{score}%", str(consents), str(dsars), str(alerts)
        
    except Exception as e:
        return "Error", "Error", "Error", "Error"


# =============================================================================
# STEP 6: Deployment configuration
# =============================================================================

# Update your production configuration:

PRODUCTION_COMPLIANCE_CONFIG = """
# Add to your production.yaml or environment variables:

compliance:
  enabled: true
  audit_logging:
    enabled: true
    retention_days: 2555  # 7 years for legal compliance
    encryption_enabled: true
  
  consent_management:
    default_jurisdiction: EU
    require_explicit_consent: true
    consent_withdrawal_immediate: true
  
  data_retention:
    automated_cleanup: true
    cleanup_schedule: "02:00"  # Daily at 2 AM
    grace_period_days: 30
  
  breach_notification:
    enabled: true
    supervisor_notification_hours: 72
    individual_notification_enabled: true
  
  cross_border_transfers:
    assessment_required: true
    adequacy_monitoring: true
    scc_templates_path: "/opt/compliance/scc/"
  
  monitoring:
    dashboard_enabled: true
    alerts_enabled: true
    email_notifications: true
    compliance_officer_email: "dpo@yourcompany.com"

# Environment variables for production:
GDPR_COMPLIANCE_ENABLED=true
AUDIT_LOGGING_ENABLED=true
CONSENT_MANAGEMENT_ENABLED=true
DATA_RETENTION_AUTOMATED=true
BREACH_NOTIFICATION_ENABLED=true
SECRET_KEY=$SECRET_KEY
JWT_SECRET=$JWT_SECRET
"""


# =============================================================================
# STEP 7: Testing your compliance implementation
# =============================================================================

def run_compliance_tests():
    """
    Comprehensive test suite for compliance implementation
    Run this after deployment to verify everything works
    """
    
    test_results = {
        'database_schema': False,
        'consent_management': False,
        'dsar_processing': False,
        'audit_logging': False,
        'data_retention': False,
        'breach_notification': False,
        'api_endpoints': False
    }
    
    try:
        from yosai_intel_dashboard.src.core.container import Container
        container = Container()
        
        # Test 1: Database schema
        db = container.get('database')
        try:
            # Test if compliance tables exist
            result = db.execute_query("SELECT COUNT(*) FROM consent_log LIMIT 1")
            test_results['database_schema'] = True
            print("✓ Database schema test passed")
        except Exception as e:
            print(f"✗ Database schema test failed: {e}")
        
        # Test 2: Consent management
        try:
            consent_service = container.get('consent_service')
            # Test consent granting (with mock data)
            success = consent_service.grant_consent(
                "test_user", 
                ConsentType.BIOMETRIC_ACCESS, 
                "EU"
            )
            test_results['consent_management'] = True
            print("✓ Consent management test passed")
        except Exception as e:
            print(f"✗ Consent management test failed: {e}")
        
        # Test 3: DSAR processing
        try:
            dsar_service = container.get('dsar_service')
            request_id = dsar_service.create_request(
                "test_user",
                DSARRequestType.ACCESS,
                "test@example.com"
            )
            test_results['dsar_processing'] = True
            print("✓ DSAR processing test passed")
        except Exception as e:
            print(f"✗ DSAR processing test failed: {e}")
        
        # Test 4: Audit logging
        try:
            audit_logger = container.get('audit_logger')
            log_id = audit_logger.log_action(
                actor_user_id="test_user",
                action_type="COMPLIANCE_TEST",
                resource_type="test_resource",
                description="Compliance framework test"
            )
            test_results['audit_logging'] = True
            print("✓ Audit logging test passed")
        except Exception as e:
            print(f"✗ Audit logging test failed: {e}")
        
        # Additional tests...
        
        # Summary
        passed_tests = sum(test_results.values())
        total_tests = len(test_results)
        
        print(f"\n=== Compliance Test Results ===")
        print(f"Passed: {passed_tests}/{total_tests}")
        
        if passed_tests == total_tests:
            print("🎉 All compliance tests passed! Your implementation is ready.")
        else:
            print("⚠️  Some tests failed. Please review the errors above.")
            
        return test_results
        
    except Exception as e:
        print(f"Critical error in compliance testing: {e}")
        return test_results


# =============================================================================
# STEP 8: Operational procedures
# =============================================================================

COMPLIANCE_PROCEDURES = """
=== GDPR/APPI COMPLIANCE OPERATIONAL PROCEDURES ===

1. Daily Operations:
   - Monitor compliance dashboard for alerts
   - Review pending DSAR requests
   - Check automated data retention processing
   - Verify audit log integrity

2. Weekly Operations:
   - Review consent withdrawal requests
   - Analyze compliance metrics trends
   - Update risk assessments as needed
   - Check cross-border transfer compliance

3. Monthly Operations:
   - Generate compliance reports for leadership
   - Review and update retention policies
   - Conduct DPIA reviews for changed processing
   - Update privacy notices if needed

4. Incident Response:
   - Data Breach: Use breach notification service within 72 hours
   - Consent Issues: Immediately halt processing and investigate
   - DSAR Delays: Escalate to DPO and prioritize completion
   - Technical Failures: Check audit logs and restore service

5. Regulatory Inquiries:
   - Use compliance dashboard to generate reports
   - Provide audit trails from compliance_audit_log table
   - Export DSAR processing records
   - Present DPIA documentation

6. Regular Maintenance:
   - Update adequacy decision status
   - Review SCC templates annually
   - Test data retention procedures
   - Verify encryption implementations

Contact DPO: dpo@yourcompany.com
Compliance System Admin: compliance-admin@yourcompany.com
Emergency Contact: legal-emergency@yourcompany.com
"""


# =============================================================================
# FINAL IMPLEMENTATION CHECKLIST
# =============================================================================

FINAL_CHECKLIST = """
FINAL COMPLIANCE IMPLEMENTATION CHECKLIST:

□ Database Schema
  □ Created all compliance tables
  □ Added compliance fields to existing tables
  □ Set up proper indexes for performance
  □ Tested database connectivity

□ Service Integration  
  □ Registered all compliance services in DI container
  □ Added audit decorators to sensitive endpoints
  □ Implemented consent checks for biometric processing
  □ Set up automated data retention scheduling

□ API Endpoints
  □ Tested consent granting/withdrawal endpoints
  □ Verified DSAR request creation and processing
  □ Confirmed audit trail accessibility
  □ Validated breach notification workflow

□ Frontend Integration
  □ Added consent management UI
  □ Implemented data download functionality
  □ Created data deletion request interface
  □ Set up compliance dashboard access

□ Monitoring & Alerts
  □ Configured compliance dashboard
  □ Set up automated alerting
  □ Tested notification workflows
  □ Verified metrics collection

□ Documentation
  □ Updated privacy policy
  □ Created data processing records
  □ Documented retention policies
  □ Prepared DPIA templates

□ Testing
  □ Ran full compliance test suite
  □ Verified end-to-end workflows
  □ Tested data subject rights
  □ Validated audit trail integrity

□ Deployment
  □ Configured production environment
  □ Set up monitoring and alerting
  □ Trained operational staff
  □ Established incident procedures

□ Legal Review
  □ DPO approval of implementation
  □ Legal review of privacy notices
  □ Validation of processing legal bases
  □ Confirmation of regulatory compliance

IMPLEMENTATION COMPLETE ✓
Your GDPR/APPI compliance framework is now operational!
"""

if __name__ == "__main__":
    print("GDPR/APPI Compliance Framework Integration Guide")
    print("="*50)
    print("Follow the steps above to integrate compliance into your application.")
    print("\nTo test your implementation, run:")
    print("python -c 'from this_file import run_compliance_tests; run_compliance_tests()'")
    print("\nFor support, check the compliance framework documentation.")