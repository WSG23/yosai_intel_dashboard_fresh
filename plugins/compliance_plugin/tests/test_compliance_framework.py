# tests/compliance/test_compliance_framework.py
"""Comprehensive test suite for GDPR/APPI compliance framework"""

import json
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, Mock, patch
from uuid import uuid4

import pytest
from yosai_intel_dashboard.models.compliance import ConsentType, DataSensitivityLevel

from core.audit_logger import ComplianceAuditLogger
from yosai_intel_dashboard.src.services.compliance.consent_service import ConsentService
from yosai_intel_dashboard.src.services.compliance.data_retention_service import DataRetentionService
from yosai_intel_dashboard.src.services.compliance.dpia_service import DPIAService, DPIATrigger, RiskLevel
from yosai_intel_dashboard.src.services.compliance.dsar_service import DSARRequestType, DSARService, DSARStatus


class TestConsentService:
    """Test consent management functionality"""

    @pytest.fixture
    def mock_db(self):
        """Mock database for testing"""
        db = Mock()
        # Mock successful database operations
        db.execute_command.return_value = 1
        db.execute_query.return_value = Mock(empty=True)
        return db

    @pytest.fixture
    def mock_audit_logger(self):
        """Mock audit logger"""
        return Mock(spec=ComplianceAuditLogger)

    @pytest.fixture
    def consent_service(self, mock_db, mock_audit_logger):
        """Create consent service for testing"""
        return ConsentService(mock_db, mock_audit_logger)

    def test_grant_consent_success(self, consent_service, mock_db):
        """Test successful consent granting"""
        # Arrange
        user_id = "test_user_123"
        consent_type = ConsentType.BIOMETRIC_ACCESS
        jurisdiction = "EU"

        # Mock no existing consent
        mock_db.execute_query.return_value = Mock(empty=True)

        # Act
        result = consent_service.grant_consent(user_id, consent_type, jurisdiction)

        # Assert
        assert result is True
        mock_db.execute_command.assert_called_once()
        consent_service.audit_logger.log_action.assert_called_once()

    def test_grant_consent_already_exists(self, consent_service, mock_db):
        """Test granting consent when it already exists"""
        # Arrange
        user_id = "test_user_123"
        consent_type = ConsentType.FACIAL_RECOGNITION
        jurisdiction = "EU"

        # Mock existing consent
        existing_consent = Mock(empty=False)
        existing_consent.iloc = [Mock()]
        existing_consent.iloc[0].to_dict.return_value = {"id": "existing_id"}
        mock_db.execute_query.return_value = existing_consent

        # Act
        result = consent_service.grant_consent(user_id, consent_type, jurisdiction)

        # Assert
        assert result is True
        # Should not attempt to insert again
        mock_db.execute_command.assert_not_called()

    def test_withdraw_consent_success(self, consent_service, mock_db):
        """Test successful consent withdrawal"""
        # Arrange
        user_id = "test_user_123"
        consent_type = ConsentType.BIOMETRIC_ACCESS
        jurisdiction = "EU"

        # Mock existing active consent
        existing_consent = Mock(empty=False)
        existing_consent.iloc = [Mock()]
        existing_consent.iloc[0].to_dict.return_value = {
            "id": "consent_id_123",
            "user_id": user_id,
            "consent_type": consent_type.value,
            "jurisdiction": jurisdiction,
            "is_active": True,
        }
        mock_db.execute_query.return_value = existing_consent
        mock_db.execute_command.return_value = 1  # 1 row affected

        # Act
        result = consent_service.withdraw_consent(user_id, consent_type, jurisdiction)

        # Assert
        assert result is True
        assert mock_db.execute_command.call_count == 1  # Update consent
        consent_service.audit_logger.log_action.assert_called()

    def test_check_consent_valid(self, consent_service, mock_db):
        """Test consent check with valid consent"""
        # Arrange
        user_id = "test_user_123"
        consent_type = ConsentType.SECURITY_ANALYTICS
        jurisdiction = "EU"

        # Mock active consent exists
        mock_consent = Mock(empty=False)
        mock_consent.iloc = [Mock()]
        mock_consent.iloc[0].to_dict.return_value = {"id": "consent_id"}
        mock_db.execute_query.return_value = mock_consent

        # Act
        result = consent_service.check_consent(user_id, consent_type, jurisdiction)

        # Assert
        assert result is True

    def test_check_consent_invalid(self, consent_service, mock_db):
        """Test consent check with no valid consent"""
        # Arrange
        user_id = "test_user_123"
        consent_type = ConsentType.LOCATION_TRACKING
        jurisdiction = "EU"

        # Mock no consent exists
        mock_db.execute_query.return_value = Mock(empty=True)

        # Act
        result = consent_service.check_consent(user_id, consent_type, jurisdiction)

        # Assert
        assert result is False

    def test_bulk_consent_check(self, consent_service, mock_db):
        """Test bulk consent checking for multiple users"""
        # Arrange
        user_ids = ["user1", "user2", "user3"]
        consent_type = ConsentType.BIOMETRIC_ACCESS
        jurisdiction = "EU"

        # Mock that user1 and user3 have consent
        mock_result = Mock(empty=False)
        mock_result.tolist.return_value = ["user1", "user3"]
        mock_result.__getitem__.return_value = mock_result  # For df['user_id']
        mock_db.execute_query.return_value = mock_result

        # Act
        result = consent_service.bulk_consent_check(
            user_ids, consent_type, jurisdiction
        )

        # Assert
        expected = {"user1": True, "user2": False, "user3": True}
        assert result == expected


class TestDSARService:
    """Test Data Subject Access Request functionality"""

    @pytest.fixture
    def mock_db(self):
        db = Mock()
        db.execute_command.return_value = 1
        db.execute_query.return_value = Mock(empty=True)
        return db

    @pytest.fixture
    def mock_audit_logger(self):
        return Mock(spec=ComplianceAuditLogger)

    @pytest.fixture
    def dsar_service(self, mock_db, mock_audit_logger):
        return DSARService(mock_db, mock_audit_logger)

    def test_create_access_request(self, dsar_service, mock_db):
        """Test creating a data access request"""
        # Arrange
        user_id = "test_user_123"
        email = "test@example.com"
        request_type = DSARRequestType.ACCESS

        # Act
        request_id = dsar_service.create_request(user_id, request_type, email)

        # Assert
        assert request_id.startswith("DSAR-")
        mock_db.execute_command.assert_called_once()
        dsar_service.audit_logger.log_action.assert_called_once()

    def test_create_erasure_request(self, dsar_service, mock_db):
        """Test creating an erasure request"""
        # Arrange
        user_id = "test_user_123"
        email = "test@example.com"
        request_type = DSARRequestType.ERASURE

        # Act
        request_id = dsar_service.create_request(user_id, request_type, email)

        # Assert
        assert request_id is not None
        assert len(request_id) > 10
        mock_db.execute_command.assert_called_once()

    def test_process_access_request(self, dsar_service, mock_db):
        """Test processing a data access request"""
        # Arrange
        request_id = "DSAR-20250715-ABC123"
        processed_by = "admin_user"

        # Mock request data
        mock_request = Mock(empty=False)
        mock_request.iloc = [Mock()]
        mock_request.iloc[0].to_dict.return_value = {
            "request_id": request_id,
            "user_id": "test_user_123",
            "request_type": "access",
            "status": "pending",
            "requestor_email": "test@example.com",
        }

        # Mock user data for access request
        mock_user_data = Mock(empty=False)
        mock_user_data.iloc = [Mock()]
        mock_user_data.iloc[0].to_dict.return_value = {
            "person_id": "test_user_123",
            "name": "Test User",
            "department": "Engineering",
        }

        mock_db.execute_query.side_effect = [mock_request, mock_user_data]

        # Act
        result = dsar_service.process_request(request_id, processed_by)

        # Assert
        assert result is True
        # Should have multiple database calls for updating status and getting data
        assert mock_db.execute_command.call_count >= 2


class TestDataRetentionService:
    """Test data retention and anonymization functionality"""

    @pytest.fixture
    def mock_db(self):
        db = Mock()
        db.execute_command.return_value = 1
        return db

    @pytest.fixture
    def mock_audit_logger(self):
        return Mock(spec=ComplianceAuditLogger)

    @pytest.fixture
    def retention_service(self, mock_db, mock_audit_logger):
        return DataRetentionService(mock_db, mock_audit_logger)

    def test_schedule_deletion(self, retention_service, mock_db):
        """Test scheduling data for deletion"""
        # Arrange
        user_id = "test_user_123"
        data_types = ["biometric_templates", "access_logs"]
        retention_days = 30

        # Act
        result = retention_service.schedule_deletion(
            user_id, data_types, retention_days
        )

        # Assert
        assert result is True
        mock_db.execute_command.assert_called_once()
        retention_service.audit_logger.log_action.assert_called_once()

    def test_anonymize_user_completely(self, retention_service, mock_db):
        """Test complete user anonymization"""
        # Arrange
        user_id = "test_user_123"

        # Act
        result = retention_service.anonymize_user_completely(user_id)

        # Assert
        assert result is True
        # Should have multiple database operations for different data types
        assert mock_db.execute_command.call_count >= 4


class TestDPIAService:
    """Test Data Protection Impact Assessment functionality"""

    @pytest.fixture
    def mock_db(self):
        db = Mock()
        db.execute_command.return_value = 1
        return db

    @pytest.fixture
    def mock_audit_logger(self):
        return Mock(spec=ComplianceAuditLogger)

    @pytest.fixture
    def dpia_service(self, mock_db, mock_audit_logger):
        return DPIAService(mock_db, mock_audit_logger)

    def test_assess_low_risk_activity(self, dpia_service):
        """Test DPIA assessment for low-risk activity"""
        # Arrange
        activity_name = "Employee Contact Management"
        data_types = ["contact_information", "employee_data"]
        processing_purposes = ["employee_management"]
        data_subjects_count = 100
        geographic_scope = ["EU"]

        # Act
        assessment = dpia_service.assess_processing_activity(
            activity_name,
            data_types,
            processing_purposes,
            data_subjects_count,
            geographic_scope,
        )

        # Assert
        assert assessment["risk_level"] in ["low", "medium"]
        assert assessment["dpia_required"] is False
        assert "assessment_id" in assessment
        assert "recommendations" in assessment

    def test_assess_high_risk_biometric_activity(self, dpia_service):
        """Test DPIA assessment for high-risk biometric processing"""
        # Arrange
        activity_name = "Biometric Access Control"
        data_types = ["biometric_templates", "facial_recognition_data"]
        processing_purposes = ["security_monitoring", "automated_decision_making"]
        data_subjects_count = 5000
        geographic_scope = ["EU"]
        automated_processing = True

        # Act
        assessment = dpia_service.assess_processing_activity(
            activity_name,
            data_types,
            processing_purposes,
            data_subjects_count,
            geographic_scope,
            automated_processing,
        )

        # Assert
        assert assessment["risk_level"] in ["high", "critical"]
        assert assessment["dpia_required"] is True
        assert DPIATrigger.BIOMETRIC_IDENTIFICATION.value in assessment["dpia_triggers"]
        assert DPIATrigger.LARGE_SCALE_PROCESSING.value in assessment["dpia_triggers"]
        assert len(assessment["recommendations"]) > 0


# Example usage patterns and integration tests
class TestComplianceIntegration:
    """Integration tests for complete compliance workflows"""

    def test_complete_user_consent_flow(self):
        """Test complete user consent workflow"""
        # This would be an integration test using a test database
        pass

    def test_erasure_request_full_workflow(self):
        """Test complete erasure request workflow"""
        # This would test the full flow from request creation to completion
        pass


# Mock data generators for testing
class ComplianceTestDataFactory:
    """Factory for generating test data"""

    @staticmethod
    def create_test_user(user_id: str = None) -> Dict[str, Any]:
        """Create test user data"""
        return {
            "person_id": user_id or f"test_user_{uuid4().hex[:8]}",
            "name": "Test User",
            "employee_id": f"EMP_{uuid4().hex[:6]}",
            "department": "Engineering",
            "clearance_level": 2,
            "access_groups": ["standard_access"],
            "is_visitor": False,
            "created_at": datetime.now(timezone.utc),
            "data_sensitivity_level": "internal",
        }

    @staticmethod
    def create_test_access_event(user_id: str) -> Dict[str, Any]:
        """Create test access event"""
        return {
            "event_id": f"event_{uuid4().hex[:8]}",
            "timestamp": datetime.now(timezone.utc),
            "person_id": user_id,
            "door_id": "door_001",
            "badge_id": f"badge_{uuid4().hex[:6]}",
            "access_result": "granted",
            "badge_status": "valid",
            "door_held_open_time": 2.5,
            "contains_biometric_data": True,
            "data_sensitivity_level": "confidential",
        }

    @staticmethod
    def create_test_consent(user_id: str, consent_type: ConsentType) -> Dict[str, Any]:
        """Create test consent record"""
        return {
            "id": str(uuid4()),
            "user_id": user_id,
            "consent_type": consent_type.value,
            "jurisdiction": "EU",
            "is_active": True,
            "granted_timestamp": datetime.now(timezone.utc),
            "policy_version": "1.0",
            "legal_basis": "consent",
        }


# Performance tests for compliance operations
class TestCompliancePerformance:
    """Performance tests for compliance operations"""

    def test_bulk_consent_check_performance(self):
        """Test performance of bulk consent checking"""
        # Test with large number of users
        user_ids = [f"user_{i}" for i in range(10000)]
        # Measure performance of bulk consent check
        pass

    def test_audit_log_insertion_performance(self):
        """Test audit log insertion performance"""
        # Test high-volume audit log insertion
        pass


# Compliance API endpoint tests
class TestComplianceAPI:
    """Test compliance API endpoints"""

    def test_grant_consent_endpoint(self):
        """Test consent granting API endpoint"""
        # Test with Flask test client
        pass

    def test_create_dsar_request_endpoint(self):
        """Test DSAR request creation endpoint"""
        # Test with Flask test client
        pass


# Example usage patterns for developers
class ComplianceUsageExamples:
    """Example usage patterns for the compliance framework"""

    def example_user_registration_with_consent(self):
        """Example: User registration requiring consent"""
        example_code = """
        from flask import request, jsonify
        from flask_login import current_user
        from core.container import Container
        from yosai_intel_dashboard.models.compliance import ConsentType
        
        @app.route('/api/users/register', methods=['POST'])
        def register_user():
            data = request.get_json()
            
            # Get compliance services
            container = Container()
            consent_service = container.get('consent_service')
            audit_logger = container.get('audit_logger')
            
            # Register user (your existing logic)
            user_id = create_user_account(data)
            
            # Grant required consents if provided
            consents = data.get('consents', [])
            for consent_type_str in consents:
                try:
                    consent_type = ConsentType(consent_type_str)
                    consent_service.grant_consent(
                        user_id=user_id,
                        consent_type=consent_type,
                        jurisdiction='EU'
                    )
                except ValueError:
                    logger.warning(f"Invalid consent type: {consent_type_str}")
            
            # Audit the registration
            audit_logger.log_action(
                actor_user_id=user_id,
                action_type='USER_REGISTRATION',
                resource_type='user_account',
                description='New user account created',
                legal_basis='contract'
            )
            
            return jsonify({'user_id': user_id, 'status': 'registered'})
        """
        return example_code

    def example_biometric_processing_with_consent_check(self):
        """Example: Biometric processing with consent verification"""
        example_code = '''
        from yosai_intel_dashboard.src.services.compliance.consent_service import ConsentService
        from yosai_intel_dashboard.models.compliance import ConsentType
        from core.audit_logger import ComplianceAuditLogger
        
        def process_facial_recognition(user_id: str, image_data: bytes):
            """Process facial recognition with consent verification"""
            
            # Check consent before processing
            container = Container()
            consent_service = container.get('consent_service')
            audit_logger = container.get('audit_logger')
            
            has_consent = consent_service.check_consent(
                user_id=user_id,
                consent_type=ConsentType.FACIAL_RECOGNITION,
                jurisdiction='EU'
            )
            
            if not has_consent:
                # Log denied access
                audit_logger.log_action(
                    actor_user_id='system',
                    target_user_id=user_id,
                    action_type='BIOMETRIC_PROCESSING_DENIED',
                    resource_type='biometric_data',
                    description='Facial recognition denied - no consent',
                    legal_basis='consent_required'
                )
                raise PermissionError("Consent required for facial recognition")
            
            # Process biometric data
            biometric_template = extract_biometric_features(image_data)
            
            # Audit the processing
            audit_logger.log_biometric_processing(
                actor_user_id='system',
                target_user_id=user_id,
                processing_type='facial_recognition',
                consent_verified=True
            )
            
            return biometric_template
        '''
        return example_code

    def example_automated_data_retention(self):
        """Example: Automated data retention policy"""
        example_code = '''
        import schedule
        import time
        from threading import Thread
        from core.container import Container
        
        def setup_automated_retention():
            """Setup automated data retention processing"""
            
            def process_data_retention():
                container = Container()
                retention_service = container.get('data_retention_service')
                
                # Process scheduled deletions
                processed_count = retention_service.process_scheduled_deletions()
                logger.info(f"Processed {processed_count} scheduled deletions")
                
                # Generate retention report
                report = retention_service.generate_retention_report(days_ahead=30)
                logger.info(f"Upcoming deletions: {len(report.get('upcoming_deletions', []))}")
            
            # Schedule daily at 2 AM
            schedule.every().day.at("02:00").do(process_data_retention)
            
            def run_scheduler():
                while True:
                    schedule.run_pending()
                    time.sleep(3600)  # Check every hour
            
            # Run in background thread
            scheduler_thread = Thread(target=run_scheduler, daemon=True)
            scheduler_thread.start()
        '''
        return example_code


# Run the test suite
if __name__ == "__main__":
    # Example of running compliance tests
    print("Running compliance framework tests...")

    # In a real scenario, you'd use:
    # pytest tests/compliance/test_compliance_framework.py -v

    # Example usage
    factory = ComplianceTestDataFactory()
    examples = ComplianceUsageExamples()

    print("Test data factory available")
    print("Usage examples available")
    print("Run with: pytest tests/compliance/ -v --cov=services/compliance")


# Compliance checklist for developers
COMPLIANCE_IMPLEMENTATION_CHECKLIST = """
GDPR/APPI Compliance Implementation Checklist:

[ ] 1. Database Schema
    [ ] Run compliance table creation SQL
    [ ] Add data sensitivity columns to existing tables
    [ ] Set up audit log table with proper indexing

[ ] 2. Service Integration
    [ ] Register compliance services in DI container
    [ ] Add compliance middleware to Flask app
    [ ] Configure audit logging for all data operations

[ ] 3. Consent Management
    [ ] Implement consent collection in user flows
    [ ] Add consent withdrawal mechanisms
    [ ] Update processing to check consent before biometric operations

[ ] 4. Data Subject Rights
    [ ] Set up DSAR request processing workflows
    [ ] Implement data export functionality
    [ ] Configure automated erasure processing

[ ] 5. Data Retention
    [ ] Define retention policies for each data type
    [ ] Set up automated retention enforcement
    [ ] Implement secure deletion procedures

[ ] 6. Impact Assessments
    [ ] Run DPIA for all high-risk processing activities
    [ ] Document legal basis for each processing purpose
    [ ] Update DPIAs when processing changes

[ ] 7. Monitoring & Compliance
    [ ] Set up compliance dashboard monitoring
    [ ] Configure compliance alerts and notifications
    [ ] Establish regular compliance reporting

[ ] 8. Security Measures
    [ ] Implement encryption for sensitive data
    [ ] Set up access controls and authentication
    [ ] Configure audit trail protection

[ ] 9. Documentation
    [ ] Create privacy policy reflecting actual processing
    [ ] Document all processing activities
    [ ] Maintain record of processing activities (ROPA)

[ ] 10. Testing & Validation
    [ ] Run compliance test suite
    [ ] Validate consent flows end-to-end
    [ ] Test DSAR request processing
    [ ] Verify data retention automation

[ ] 11. Deployment
    [ ] Configure production environment variables
    [ ] Set up monitoring and alerting
    [ ] Plan incident response procedures

[ ] 12. Ongoing Compliance
    [ ] Schedule regular compliance reviews
    [ ] Plan privacy policy updates
    [ ] Monitor regulatory changes
"""
