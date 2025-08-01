# services/data_processing/compliance_csv_processor.py
"""Enhanced CSV processing with GDPR/APPI compliance integration"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set
from uuid import uuid4

import pandas as pd

from yosai_intel_dashboard.src.core.audit_logger import ComplianceAuditLogger
from yosai_intel_dashboard.src.core.interfaces.protocols import DatabaseProtocol
from database.secure_exec import execute_query
from yosai_intel_dashboard.src.services.compliance.consent_service import ConsentService
from yosai_intel_dashboard.src.services.compliance.data_retention_service import DataRetentionService
from yosai_intel_dashboard.src.services.data_processing.file_processor import FileProcessor
from yosai_intel_dashboard.models.compliance import ConsentType, DataSensitivityLevel

logger = logging.getLogger(__name__)


class DataClassificationResult:
    """Result of data classification analysis"""

    def __init__(self):
        self.personal_data_columns: List[str] = []
        self.sensitive_data_columns: List[str] = []
        self.data_types_detected: Set[str] = set()
        self.sensitivity_level: DataSensitivityLevel = DataSensitivityLevel.PUBLIC
        self.consent_types_required: List[ConsentType] = []
        self.legal_basis_recommendation: str = "legitimate_interests"
        self.retention_policy_recommendation: str = "default_retention"


class ComplianceCSVProcessor:
    """Enhanced CSV processor with full compliance integration"""

    def __init__(
        self,
        db: DatabaseProtocol,
        audit_logger: ComplianceAuditLogger,
        consent_service: ConsentService,
        retention_service: DataRetentionService,
    ):
        self.db = db
        self.audit_logger = audit_logger
        self.consent_service = consent_service
        self.retention_service = retention_service

        # Data classification patterns
        self._personal_data_patterns = {
            "person_id": ["person_id", "user_id", "employee_id", "id", "userid"],
            "names": ["name", "first_name", "last_name", "full_name", "employee_name"],
            "email": ["email", "email_address", "e_mail"],
            "phone": ["phone", "telephone", "mobile", "cell"],
            "badge_id": ["badge_id", "card_id", "access_card", "badge_number"],
            "biometric_data": ["biometric", "fingerprint", "facial", "template"],
            "location_data": ["door_id", "location", "building", "floor", "room"],
            "access_logs": ["timestamp", "access_time", "entry_time", "access_result"],
            "department": ["department", "division", "team", "group"],
            "clearance": ["clearance", "security_level", "access_level"],
            "health_data": ["health", "medical", "illness", "injury"],
            "financial_data": ["salary", "wage", "payment", "bank", "account"],
        }

        # Sensitivity scoring
        self._sensitivity_scores = {
            "biometric_data": 95,
            "health_data": 90,
            "financial_data": 80,
            "person_id": 70,
            "names": 60,
            "email": 50,
            "access_logs": 40,
            "department": 30,
            "location_data": 35,
        }

    def process_csv_with_compliance(
        self, file_path: str, upload_context: Dict[str, Any], uploaded_by: str
    ) -> Dict[str, Any]:
        """
        Main entry point for compliance-aware CSV processing

        Args:
            file_path: Path to uploaded CSV file
            upload_context: Context about upload (purpose, data source, etc.)
            uploaded_by: User who uploaded the file

        Returns:
            Processing result with compliance status
        """
        try:
            processing_id = f"CSV-PROC-{str(uuid4())[:8].upper()}"

            # 1. Load and analyze CSV data
            df = FileProcessor.read_large_csv(file_path)

            # 2. Classify data types and sensitivity
            classification = self._classify_csv_data(df, upload_context)

            # 3. Check consent requirements
            consent_check_result = self._check_consent_requirements(
                classification, upload_context, uploaded_by
            )

            # 4. Determine processing authorization
            processing_authorized = self._authorize_processing(
                classification, consent_check_result, upload_context
            )

            if not processing_authorized["authorized"]:
                # Log unauthorized processing attempt
                self.audit_logger.log_action(
                    actor_user_id=uploaded_by,
                    action_type="CSV_PROCESSING_DENIED",
                    resource_type="csv_data",
                    resource_id=processing_id,
                    description=f"CSV processing denied: {processing_authorized['reason']}",
                    legal_basis="compliance_check",
                    data_categories=list(classification.data_types_detected),
                )

                return {
                    "processing_id": processing_id,
                    "status": "denied",
                    "reason": processing_authorized["reason"],
                    "required_consents": classification.consent_types_required,
                    "classification": classification.__dict__,
                }

            # 5. Process data with compliance metadata
            processed_data = self._process_csv_data_with_compliance(
                df, classification, upload_context, processing_id
            )

            # 6. Apply retention policies
            retention_applied = self._apply_retention_policies(
                processed_data, classification, processing_id
            )

            # 7. Store with compliance metadata
            storage_result = self._store_csv_with_compliance(
                processed_data,
                classification,
                upload_context,
                processing_id,
                uploaded_by,
            )

            # 8. Audit successful processing
            self.audit_logger.log_action(
                actor_user_id=uploaded_by,
                action_type="CSV_PROCESSING_COMPLETED",
                resource_type="csv_data",
                resource_id=processing_id,
                description=f"CSV processed: {len(df)} rows, sensitivity: {classification.sensitivity_level.value}",
                legal_basis=classification.legal_basis_recommendation,
                data_categories=list(classification.data_types_detected),
                metadata={
                    "file_path": file_path,
                    "row_count": len(df),
                    "column_count": len(df.columns),
                    "personal_data_columns": classification.personal_data_columns,
                    "retention_policy": classification.retention_policy_recommendation,
                },
            )

            return {
                "processing_id": processing_id,
                "status": "completed",
                "classification": classification.__dict__,
                "consent_status": consent_check_result,
                "retention_policy": retention_applied,
                "storage_location": storage_result["location"],
                "rows_processed": len(processed_data),
                "compliance_score": self._calculate_compliance_score(classification),
            }

        except Exception as e:
            logger.error(f"CSV compliance processing failed: {e}")

            # Audit the failure
            self.audit_logger.log_action(
                actor_user_id=uploaded_by,
                action_type="CSV_PROCESSING_FAILED",
                resource_type="csv_data",
                description=f"CSV processing failed: {str(e)}",
                legal_basis="compliance_check",
            )

            return {"status": "error", "error": str(e)}

    def _classify_csv_data(
        self, df: pd.DataFrame, context: Dict[str, Any]
    ) -> DataClassificationResult:
        """Classify data types and determine sensitivity level"""

        result = DataClassificationResult()
        column_scores = {}

        # Analyze column headers
        for column in df.columns:
            column_lower = column.lower().strip()

            for data_type, patterns in self._personal_data_patterns.items():
                if any(pattern in column_lower for pattern in patterns):
                    result.data_types_detected.add(data_type)
                    column_scores[column] = self._sensitivity_scores.get(data_type, 10)

                    if data_type in ["person_id", "names", "email", "biometric_data"]:
                        result.personal_data_columns.append(column)

                    if data_type in ["biometric_data", "health_data", "financial_data"]:
                        result.sensitive_data_columns.append(column)

        # Analyze sample data for additional patterns
        sample_analysis = self._analyze_sample_data(df.head(10))
        result.data_types_detected.update(sample_analysis["detected_types"])

        # Determine overall sensitivity level
        max_score = max(column_scores.values()) if column_scores else 10

        if max_score >= 85:
            result.sensitivity_level = DataSensitivityLevel.SPECIAL_CATEGORY
        elif max_score >= 60:
            result.sensitivity_level = DataSensitivityLevel.CONFIDENTIAL
        elif max_score >= 30:
            result.sensitivity_level = DataSensitivityLevel.INTERNAL
        else:
            result.sensitivity_level = DataSensitivityLevel.PUBLIC

        # Determine required consent types
        if "biometric_data" in result.data_types_detected:
            result.consent_types_required.append(ConsentType.BIOMETRIC_ACCESS)
        if (
            "access_logs" in result.data_types_detected
            and "person_id" in result.data_types_detected
        ):
            result.consent_types_required.append(ConsentType.BEHAVIORAL_ANALYSIS)
        if "location_data" in result.data_types_detected:
            result.consent_types_required.append(ConsentType.LOCATION_TRACKING)

        # Recommend legal basis
        if result.consent_types_required:
            result.legal_basis_recommendation = "consent"
        elif "access_logs" in result.data_types_detected:
            result.legal_basis_recommendation = "legitimate_interests"
        else:
            result.legal_basis_recommendation = "contract"

        # Recommend retention policy
        if "biometric_data" in result.data_types_detected:
            result.retention_policy_recommendation = "biometric_data_1year"
        elif "access_logs" in result.data_types_detected:
            result.retention_policy_recommendation = "security_logs_7years"
        else:
            result.retention_policy_recommendation = "general_data_2years"

        return result

    def _analyze_sample_data(self, sample_df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze sample data for patterns not evident in headers"""

        detected_types = set()

        for column in sample_df.columns:
            sample_values = sample_df[column].dropna().astype(str)

            if len(sample_values) == 0:
                continue

            # Check for email patterns
            if sample_values.str.contains("@").any():
                detected_types.add("email")

            # Check for phone patterns
            if sample_values.str.match(r"^\+?[\d\s\-\(\)]+$").any():
                detected_types.add("phone")

            # Check for ID patterns
            if sample_values.str.match(r"^[A-Z0-9]{6,}$").any():
                detected_types.add("person_id")

            # Check for timestamp patterns
            try:
                pd.to_datetime(sample_values.iloc[0])
                detected_types.add("access_logs")
            except:
                pass

        return {"detected_types": detected_types}

    def _check_consent_requirements(
        self,
        classification: DataClassificationResult,
        context: Dict[str, Any],
        uploaded_by: str,
    ) -> Dict[str, Any]:
        """Check if required consents exist for processing"""

        consent_status = {
            "consent_required": len(classification.consent_types_required) > 0,
            "consent_types_needed": [
                ct.value for ct in classification.consent_types_required
            ],
            "consent_check_results": {},
            "processing_authorized": True,
            "missing_consents": [],
        }

        if not consent_status["consent_required"]:
            return consent_status

        # Check if CSV contains identifiable users
        if "person_id" not in classification.data_types_detected:
            # No identifiable users - general consent from uploader might be sufficient
            consent_status["consent_check_results"][
                "uploader"
            ] = "consent_from_uploader_sufficient"
            return consent_status

        # For identifiable user data, check individual consents
        # This is complex - you might need to:
        # 1. Extract user IDs from CSV
        # 2. Check consent for each user
        # 3. Filter data to only consented users

        # Simplified approach: require explicit confirmation from uploader
        upload_consent_confirmed = context.get("consent_confirmed", False)
        data_controller_authority = context.get("data_controller_upload", False)

        if upload_consent_confirmed or data_controller_authority:
            consent_status["consent_check_results"][
                "bulk_consent"
            ] = "confirmed_by_uploader"
        else:
            consent_status["processing_authorized"] = False
            consent_status["missing_consents"] = consent_status["consent_types_needed"]

        return consent_status

    def _authorize_processing(
        self,
        classification: DataClassificationResult,
        consent_check: Dict[str, Any],
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Determine if processing is authorized"""

        # Check consent requirements
        if not consent_check["processing_authorized"]:
            return {
                "authorized": False,
                "reason": "Missing required consents",
                "missing_consents": consent_check["missing_consents"],
            }

        # Check data sensitivity limits
        if classification.sensitivity_level == DataSensitivityLevel.SPECIAL_CATEGORY:
            dpo_approval = context.get("dpo_approval", False)
            if not dpo_approval:
                return {
                    "authorized": False,
                    "reason": "Special category data requires DPO approval",
                }

        # Check purpose limitation
        declared_purpose = context.get("processing_purpose", "")
        if not declared_purpose:
            return {
                "authorized": False,
                "reason": "Processing purpose must be declared",
            }

        return {"authorized": True}

    def _process_csv_data_with_compliance(
        self,
        df: pd.DataFrame,
        classification: DataClassificationResult,
        context: Dict[str, Any],
        processing_id: str,
    ) -> pd.DataFrame:
        """Process CSV data with compliance metadata"""

        # Add compliance metadata columns
        df_processed = df.copy()

        # Add processing metadata
        df_processed["_compliance_processing_id"] = processing_id
        df_processed["_compliance_sensitivity_level"] = (
            classification.sensitivity_level.value
        )
        df_processed["_compliance_legal_basis"] = (
            classification.legal_basis_recommendation
        )
        df_processed["_compliance_retention_policy"] = (
            classification.retention_policy_recommendation
        )
        df_processed["_compliance_processed_at"] = datetime.now(timezone.utc)

        # Mask sensitive data if no consent (example)
        if ConsentType.BIOMETRIC_ACCESS in classification.consent_types_required:
            for col in classification.sensitive_data_columns:
                if "biometric" in col.lower():
                    # Check if we have consent - if not, mask the data
                    consent_status = context.get("consent_confirmed", False)
                    if not consent_status:
                        df_processed[col] = "MASKED_NO_CONSENT"

        return df_processed

    def _apply_retention_policies(
        self,
        df: pd.DataFrame,
        classification: DataClassificationResult,
        processing_id: str,
    ) -> Dict[str, Any]:
        """Apply appropriate retention policies to processed data"""

        retention_days = {
            "biometric_data_1year": 365,
            "security_logs_7years": 2555,
            "general_data_2years": 730,
            "visitor_data_90days": 90,
        }

        policy = classification.retention_policy_recommendation
        days = retention_days.get(policy, 730)

        # Calculate deletion date
        deletion_date = datetime.now(timezone.utc) + timedelta(days=days)

        # Store retention policy
        retention_record = {
            "processing_id": processing_id,
            "retention_policy": policy,
            "retention_days": days,
            "deletion_date": deletion_date,
            "data_sensitivity": classification.sensitivity_level.value,
            "applied_at": datetime.now(timezone.utc),
        }

        # Store in retention tracking table
        self._store_retention_policy(retention_record)

        return retention_record

    def _store_csv_with_compliance(
        self,
        df: pd.DataFrame,
        classification: DataClassificationResult,
        context: Dict[str, Any],
        processing_id: str,
        uploaded_by: str,
    ) -> Dict[str, Any]:
        """Store processed CSV with full compliance metadata"""

        # Create storage location based on sensitivity
        if classification.sensitivity_level == DataSensitivityLevel.SPECIAL_CATEGORY:
            storage_location = f"secure_storage/special_category/{processing_id}"
        elif classification.sensitivity_level == DataSensitivityLevel.CONFIDENTIAL:
            storage_location = f"secure_storage/confidential/{processing_id}"
        else:
            storage_location = f"standard_storage/{processing_id}"

        # Store main data
        df.to_parquet(f"{storage_location}/data.parquet", index=False)

        # Store compliance metadata
        compliance_metadata = {
            "processing_id": processing_id,
            "uploaded_by": uploaded_by,
            "upload_timestamp": datetime.now(timezone.utc).isoformat(),
            "classification": classification.__dict__,
            "context": context,
            "storage_location": storage_location,
            "row_count": len(df),
            "column_count": len(df.columns),
            "personal_data_columns": classification.personal_data_columns,
            "sensitive_data_columns": classification.sensitive_data_columns,
        }

        # Store metadata in database
        self._store_processing_metadata(compliance_metadata)

        return {"location": storage_location, "metadata": compliance_metadata}

    def get_user_csv_data_for_dsar(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all CSV data related to a user for DSAR requests"""

        try:
            # Find all CSV processing that included this user
            query_sql = """
                SELECT processing_id, storage_location, classification, upload_timestamp
                FROM csv_processing_metadata 
                WHERE personal_data_columns IS NOT NULL
                  AND created_at >= NOW() - INTERVAL '7 years'
                ORDER BY upload_timestamp DESC
            """

            df = execute_query(self.db, query_sql)
            user_csv_data = []

            for row in df.itertuples(index=False):
                processing_id = row.processing_id
                storage_location = row.storage_location

                # Load the CSV data
                try:
                    csv_df = pd.read_parquet(f"{storage_location}/data.parquet")

                    # Check if this user's data is in this CSV
                    user_data_found = self._extract_user_data_from_csv(csv_df, user_id)

                    if not user_data_found.empty:
                        user_csv_data.append(
                            {
                                "processing_id": processing_id,
                                "upload_timestamp": row.upload_timestamp,
                                "user_data": user_data_found.to_dict("records"),
                                "classification": row.classification,
                            }
                        )

                except Exception as e:
                    logger.error(f"Error reading CSV data for DSAR: {e}")
                    continue

            return user_csv_data

        except Exception as e:
            logger.error(f"Error getting user CSV data for DSAR: {e}")
            return []

    def delete_user_csv_data(self, user_id: str) -> bool:
        """Delete/anonymize user data from CSV files for erasure requests"""

        try:
            csv_data_list = self.get_user_csv_data_for_dsar(user_id)

            for csv_data in csv_data_list:
                processing_id = csv_data["processing_id"]

                # Get storage location
                storage_location = self._get_storage_location(processing_id)

                # Load CSV
                csv_df = pd.read_parquet(f"{storage_location}/data.parquet")

                # Anonymize user data
                anonymized_df = self._anonymize_user_data_in_csv(csv_df, user_id)

                # Save anonymized version
                anonymized_df.to_parquet(
                    f"{storage_location}/data.parquet", index=False
                )

                # Audit the anonymization
                self.audit_logger.log_data_deletion(
                    actor_user_id="system",
                    target_user_id=user_id,
                    data_types=["csv_data"],
                    retention_policy=f"erasure_request_{processing_id}",
                )

            return True

        except Exception as e:
            logger.error(f"Error deleting user CSV data: {e}")
            return False


# Integration with existing CSV upload workflow
def enhance_existing_csv_upload():
    """
    Example of how to enhance your existing CSV upload with compliance
    """

    # Your existing upload route enhanced:

    from flask import jsonify, request
    from flask_login import current_user, login_required

    @app.route("/api/upload/csv", methods=["POST"])
    @login_required
    def upload_csv_with_compliance():
        """Enhanced CSV upload with automatic compliance processing"""

        if "file" not in request.files:
            return jsonify({"error": "No file provided"}), 400

        file = request.files["file"]

        # Get upload context from request
        upload_context = {
            "processing_purpose": request.form.get("purpose", ""),
            "data_source": request.form.get("data_source", ""),
            "consent_confirmed": request.form.get("consent_confirmed") == "true",
            "dpo_approval": request.form.get("dpo_approval") == "true",
            "data_controller_upload": current_user.has_role("data_controller"),
        }

        # Save uploaded file
        file_path = save_uploaded_file(file)

        try:
            # Get compliance processor
            container = Container()
            compliance_processor = ComplianceCSVProcessor(
                db=container.get("database"),
                audit_logger=container.get("audit_logger"),
                consent_service=container.get("consent_service"),
                retention_service=container.get("data_retention_service"),
            )

            # Process with compliance
            result = compliance_processor.process_csv_with_compliance(
                file_path=file_path,
                upload_context=upload_context,
                uploaded_by=current_user.id,
            )

            if result["status"] == "denied":
                return (
                    jsonify(
                        {
                            "status": "denied",
                            "reason": result["reason"],
                            "required_consents": result.get("required_consents", []),
                            "classification": result.get("classification", {}),
                        }
                    ),
                    403,
                )

            elif result["status"] == "completed":
                return (
                    jsonify(
                        {
                            "status": "success",
                            "processing_id": result["processing_id"],
                            "rows_processed": result["rows_processed"],
                            "compliance_score": result["compliance_score"],
                            "classification": result["classification"],
                            "message": "CSV processed successfully with compliance verification",
                        }
                    ),
                    200,
                )

            else:  # error
                return (
                    jsonify(
                        {
                            "status": "error",
                            "error": result.get("error", "Unknown error"),
                        }
                    ),
                    500,
                )

        except Exception as e:
            logger.error(f"CSV upload failed: {e}")
            return jsonify({"error": "Upload processing failed"}), 500


# Enhanced frontend for CSV upload with compliance
CSV_UPLOAD_COMPLIANCE_UI = """
<!-- Enhanced CSV upload form with compliance features -->
<form id="csv-upload-form" enctype="multipart/form-data">
    <div class="upload-section">
        <h3>Upload CSV Data</h3>
        
        <div class="file-input">
            <input type="file" id="csv-file" name="file" accept=".csv" required>
            <label for="csv-file">Choose CSV File</label>
        </div>
        
        <!-- Compliance fields -->
        <div class="compliance-section">
            <h4>Data Processing Information</h4>
            
            <div class="field">
                <label for="purpose">Processing Purpose *</label>
                <select id="purpose" name="purpose" required>
                    <option value="">Select purpose...</option>
                    <option value="security_analysis">Security Analysis</option>
                    <option value="access_monitoring">Access Monitoring</option>
                    <option value="employee_analytics">Employee Analytics</option>
                    <option value="visitor_management">Visitor Management</option>
                    <option value="compliance_reporting">Compliance Reporting</option>
                </select>
            </div>
            
            <div class="field">
                <label for="data-source">Data Source</label>
                <input type="text" id="data-source" name="data_source" 
                       placeholder="e.g., Badge System Export, HR Database">
            </div>
            
            <div class="consent-section">
                <h5>Consent & Authorization</h5>
                
                <div class="checkbox-field">
                    <input type="checkbox" id="consent-confirmed" name="consent_confirmed">
                    <label for="consent-confirmed">
                        I confirm that appropriate consent has been obtained for processing 
                        any personal data in this file
                    </label>
                </div>
                
                <div class="checkbox-field">
                    <input type="checkbox" id="dpo-approval" name="dpo_approval">
                    <label for="dpo-approval">
                        This upload has been approved by the Data Protection Officer 
                        (required for sensitive data)
                    </label>
                </div>
                
                <div class="info-box">
                    <strong>Note:</strong> The system will automatically analyze your CSV for 
                    personal data and apply appropriate privacy protections.
                </div>
            </div>
        </div>
        
        <button type="submit" id="upload-btn">Upload & Process with Compliance Check</button>
    </div>
    
    <!-- Results section -->
    <div id="upload-results" style="display: none;">
        <h4>Upload Results</h4>
        <div id="results-content"></div>
    </div>
</form>

<script>
document.getElementById('csv-upload-form').onsubmit = function(e) {
    e.preventDefault();
    
    const formData = new FormData(this);
    const uploadBtn = document.getElementById('upload-btn');
    
    uploadBtn.textContent = 'Processing...';
    uploadBtn.disabled = true;
    
    fetch('/api/upload/csv', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        const resultsDiv = document.getElementById('results-content');
        
        if (data.status === 'success') {
            resultsDiv.innerHTML = `
                <div class="success">
                    <h5>✅ Upload Successful</h5>
                    <p><strong>Processing ID:</strong> ${data.processing_id}</p>
                    <p><strong>Rows Processed:</strong> ${data.rows_processed}</p>
                    <p><strong>Compliance Score:</strong> ${data.compliance_score}%</p>
                    <div class="classification">
                        <h6>Data Classification:</h6>
                        <p><strong>Sensitivity Level:</strong> ${data.classification.sensitivity_level}</p>
                        <p><strong>Personal Data Columns:</strong> ${data.classification.personal_data_columns.join(', ')}</p>
                        <p><strong>Legal Basis:</strong> ${data.classification.legal_basis_recommendation}</p>
                    </div>
                </div>
            `;
        } else if (data.status === 'denied') {
            resultsDiv.innerHTML = `
                <div class="error">
                    <h5>❌ Upload Denied</h5>
                    <p><strong>Reason:</strong> ${data.reason}</p>
                    ${data.required_consents ? `
                        <div class="required-consents">
                            <p><strong>Required Consents:</strong></p>
                            <ul>
                                ${data.required_consents.map(consent => `<li>${consent}</li>`).join('')}
                            </ul>
                        </div>
                    ` : ''}
                    <p>Please ensure all required consents are obtained and try again.</p>
                </div>
            `;
        } else {
            resultsDiv.innerHTML = `
                <div class="error">
                    <h5>❌ Upload Failed</h5>
                    <p>${data.error || 'Unknown error occurred'}</p>
                </div>
            `;
        }
        
        document.getElementById('upload-results').style.display = 'block';
        uploadBtn.textContent = 'Upload & Process with Compliance Check';
        uploadBtn.disabled = false;
    })
    .catch(error => {
        console.error('Upload error:', error);
        document.getElementById('results-content').innerHTML = `
            <div class="error">
                <h5>❌ Upload Failed</h5>
                <p>Network error or server unavailable</p>
            </div>
        `;
        document.getElementById('upload-results').style.display = 'block';
        uploadBtn.textContent = 'Upload & Process with Compliance Check';
        uploadBtn.disabled = false;
    });
};
</script>
"""
