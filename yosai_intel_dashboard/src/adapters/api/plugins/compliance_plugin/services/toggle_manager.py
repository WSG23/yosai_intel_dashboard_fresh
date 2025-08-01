# plugins/compliance_plugin/toggle_manager.py
"""
Compliance Toggle Manager - Granular control over when compliance applies
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Set

from yosai_intel_dashboard.src.core.rbac import require_role
from database.secure_exec import execute_command, execute_query
from plugins.common_callbacks import csv_pre_process_callback
from yosai_intel_dashboard.src.services.data_processing.file_processor import FileProcessor

logger = logging.getLogger(__name__)


class ComplianceScope(Enum):
    """Scope of compliance requirements"""

    GLOBAL = "global"  # All processing
    DATA_SOURCE = "data_source"  # Specific data sources
    PROCESSING_PURPOSE = "purpose"  # Specific purposes
    USER_TYPE = "user_type"  # Employee vs visitor vs external
    DATA_TYPE = "data_type"  # Biometric vs access logs vs analytics
    JURISDICTION = "jurisdiction"  # EU vs Japan vs internal
    CLIENT = "client"  # Specific client data


class BypassReason(Enum):
    """Valid reasons for bypassing compliance"""

    CLIENT_HANDLED = "client_handled"  # Client already handled compliance
    INTERNAL_DATA = "internal_data"  # Internal operational data
    ANONYMIZED_DATA = "anonymized_data"  # Data already anonymized
    LEGAL_BASIS_CONTRACT = (
        "legal_basis_contract"  # Employment contract covers processing
    )
    EMERGENCY_PROCESSING = "emergency_processing"  # Emergency/security situation
    DEVELOPMENT_TESTING = "development_testing"  # Development/test environment
    REGULATORY_EXEMPTION = "regulatory_exemption"  # Specific regulatory exemption
    CONSENT_NOT_REQUIRED = "consent_not_required"  # Processing doesn't require consent


@dataclass
class ComplianceToggle:
    """Individual compliance toggle configuration"""

    id: str
    scope: ComplianceScope
    scope_value: str  # e.g., "client_abc", "security_monitoring", "biometric_data"
    enabled: bool
    bypass_reason: Optional[BypassReason] = None
    description: str = ""
    created_by: str = ""
    created_at: datetime = None
    expires_at: Optional[datetime] = None
    conditions: Dict[str, Any] = None  # Additional conditions

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc)
        if self.conditions is None:
            self.conditions = {}

    def is_active(self) -> bool:
        """Check if toggle is currently active"""
        if self.expires_at and datetime.now(timezone.utc) > self.expires_at:
            return False
        return True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "scope": self.scope.value,
            "scope_value": self.scope_value,
            "enabled": self.enabled,
            "bypass_reason": self.bypass_reason.value if self.bypass_reason else None,
            "description": self.description,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "conditions": self.conditions,
            "is_active": self.is_active(),
        }


class ComplianceToggleManager:
    """Manages compliance toggles and bypass conditions"""

    def __init__(self, db, audit_logger):
        self.db = db
        self.audit_logger = audit_logger
        self.toggles: Dict[str, ComplianceToggle] = {}
        self._load_toggles()

    def should_apply_compliance(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Determine if compliance should be applied for given context

        Args:
            context: Processing context with keys like:
                - data_source: "client_abc_export"
                - processing_purpose: "security_monitoring"
                - data_types: ["access_logs", "biometric_data"]
                - user_type: "employee"
                - jurisdiction: "EU"
                - client_id: "client_abc"
                - uploaded_by: "admin_user"

        Returns:
            Dict with compliance decision and reasoning
        """

        # Default to compliance enabled
        result = {
            "compliance_required": True,
            "bypassed_scopes": [],
            "active_toggles": [],
            "bypass_reasons": [],
            "warnings": [],
            "audit_info": {},
        }

        # Check each toggle to see if it applies to this context
        for toggle in self.toggles.values():
            if not toggle.is_active():
                continue

            if self._toggle_matches_context(toggle, context):
                result["active_toggles"].append(toggle.to_dict())

                if not toggle.enabled:
                    # This scope has compliance disabled
                    result["bypassed_scopes"].append(
                        {
                            "scope": toggle.scope.value,
                            "scope_value": toggle.scope_value,
                            "bypass_reason": (
                                toggle.bypass_reason.value
                                if toggle.bypass_reason
                                else "not_specified"
                            ),
                        }
                    )

                    if toggle.bypass_reason:
                        result["bypass_reasons"].append(toggle.bypass_reason.value)

        # Determine final compliance requirement
        if result["bypassed_scopes"]:
            # Check if any bypass covers the entire processing
            global_bypass = any(
                scope["scope"] == "global"
                or (
                    scope["scope"] == "client"
                    and scope["scope_value"] == context.get("client_id")
                )
                or (
                    scope["scope"] == "data_source"
                    and scope["scope_value"] == context.get("data_source")
                )
                for scope in result["bypassed_scopes"]
            )

            if global_bypass:
                result["compliance_required"] = False
            else:
                # Partial bypass - some aspects may still require compliance
                result["compliance_required"] = self._determine_partial_compliance(
                    context, result["bypassed_scopes"]
                )

        # Add warnings for risky bypasses
        self._add_bypass_warnings(result, context)

        # Audit the compliance decision
        self.audit_logger.log_action(
            actor_user_id=context.get("uploaded_by", "system"),
            action_type="COMPLIANCE_DECISION",
            resource_type="compliance_toggle",
            description=f"Compliance {'bypassed' if not result['compliance_required'] else 'required'} for {context.get('processing_purpose', 'unknown')}",
            legal_basis="compliance_management",
            metadata={
                "context": context,
                "decision": result,
                "active_toggles": len(result["active_toggles"]),
                "bypassed_scopes": len(result["bypassed_scopes"]),
            },
        )

        return result

    def create_toggle(
        self,
        scope: ComplianceScope,
        scope_value: str,
        enabled: bool,
        bypass_reason: Optional[BypassReason],
        description: str,
        created_by: str,
        expires_at: Optional[datetime] = None,
        conditions: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Create a new compliance toggle"""

        toggle_id = f"{scope.value}_{scope_value}_{int(datetime.now().timestamp())}"

        toggle = ComplianceToggle(
            id=toggle_id,
            scope=scope,
            scope_value=scope_value,
            enabled=enabled,
            bypass_reason=bypass_reason,
            description=description,
            created_by=created_by,
            expires_at=expires_at,
            conditions=conditions or {},
        )

        # Store in database
        self._store_toggle(toggle)

        # Add to in-memory cache
        self.toggles[toggle_id] = toggle

        # Audit toggle creation
        self.audit_logger.log_action(
            actor_user_id=created_by,
            action_type="COMPLIANCE_TOGGLE_CREATED",
            resource_type="compliance_toggle",
            resource_id=toggle_id,
            description=f"Created compliance toggle: {scope.value}={scope_value}, enabled={enabled}",
            legal_basis="compliance_management",
            metadata=toggle.to_dict(),
        )

        logger.info(f"Created compliance toggle: {toggle_id}")
        return toggle_id

    def update_toggle(
        self,
        toggle_id: str,
        enabled: Optional[bool] = None,
        bypass_reason: Optional[BypassReason] = None,
        description: Optional[str] = None,
        expires_at: Optional[datetime] = None,
        updated_by: str = "system",
    ) -> bool:
        """Update an existing compliance toggle"""

        if toggle_id not in self.toggles:
            logger.warning(f"Toggle {toggle_id} not found")
            return False

        toggle = self.toggles[toggle_id]
        old_state = toggle.to_dict()

        # Update fields
        if enabled is not None:
            toggle.enabled = enabled
        if bypass_reason is not None:
            toggle.bypass_reason = bypass_reason
        if description is not None:
            toggle.description = description
        if expires_at is not None:
            toggle.expires_at = expires_at

        # Store changes
        self._store_toggle(toggle)

        # Audit the update
        self.audit_logger.log_action(
            actor_user_id=updated_by,
            action_type="COMPLIANCE_TOGGLE_UPDATED",
            resource_type="compliance_toggle",
            resource_id=toggle_id,
            description=f"Updated compliance toggle: {toggle_id}",
            legal_basis="compliance_management",
            metadata={
                "old_state": old_state,
                "new_state": toggle.to_dict(),
                "updated_by": updated_by,
            },
        )

        return True

    def delete_toggle(self, toggle_id: str, deleted_by: str = "system") -> bool:
        """Delete a compliance toggle"""

        if toggle_id not in self.toggles:
            return False

        toggle = self.toggles[toggle_id]

        # Remove from database
        delete_sql = "DELETE FROM compliance_toggles WHERE toggle_id = %s"
        execute_command(self.db, delete_sql, (toggle_id,))

        # Remove from cache
        del self.toggles[toggle_id]

        # Audit deletion
        self.audit_logger.log_action(
            actor_user_id=deleted_by,
            action_type="COMPLIANCE_TOGGLE_DELETED",
            resource_type="compliance_toggle",
            resource_id=toggle_id,
            description=f"Deleted compliance toggle: {toggle_id}",
            legal_basis="compliance_management",
            metadata=toggle.to_dict(),
        )

        return True

    def get_toggle(self, toggle_id: str) -> Optional[ComplianceToggle]:
        """Get a specific toggle"""
        return self.toggles.get(toggle_id)

    def list_toggles(
        self, scope: Optional[ComplianceScope] = None, active_only: bool = True
    ) -> List[ComplianceToggle]:
        """List compliance toggles"""

        toggles = list(self.toggles.values())

        if scope:
            toggles = [t for t in toggles if t.scope == scope]

        if active_only:
            toggles = [t for t in toggles if t.is_active()]

        return sorted(toggles, key=lambda t: t.created_at, reverse=True)

    def create_client_bypass(
        self,
        client_id: str,
        bypass_reason: BypassReason,
        description: str,
        created_by: str,
        expires_at: Optional[datetime] = None,
    ) -> str:
        """Convenience method to create client-specific bypass"""

        return self.create_toggle(
            scope=ComplianceScope.CLIENT,
            scope_value=client_id,
            enabled=False,  # Disable compliance for this client
            bypass_reason=bypass_reason,
            description=f"Client bypass: {description}",
            created_by=created_by,
            expires_at=expires_at,
        )

    def create_purpose_bypass(
        self,
        purpose: str,
        bypass_reason: BypassReason,
        description: str,
        created_by: str,
        data_types: Optional[List[str]] = None,
    ) -> str:
        """Convenience method to create purpose-specific bypass"""

        conditions = {}
        if data_types:
            conditions["data_types"] = data_types

        return self.create_toggle(
            scope=ComplianceScope.PROCESSING_PURPOSE,
            scope_value=purpose,
            enabled=False,
            bypass_reason=bypass_reason,
            description=f"Purpose bypass: {description}",
            created_by=created_by,
            conditions=conditions,
        )

    def _toggle_matches_context(
        self, toggle: ComplianceToggle, context: Dict[str, Any]
    ) -> bool:
        """Check if a toggle applies to the given context"""

        if toggle.scope == ComplianceScope.GLOBAL:
            return True

        elif toggle.scope == ComplianceScope.CLIENT:
            return context.get("client_id") == toggle.scope_value

        elif toggle.scope == ComplianceScope.DATA_SOURCE:
            return context.get("data_source") == toggle.scope_value

        elif toggle.scope == ComplianceScope.PROCESSING_PURPOSE:
            return context.get("processing_purpose") == toggle.scope_value

        elif toggle.scope == ComplianceScope.USER_TYPE:
            return context.get("user_type") == toggle.scope_value

        elif toggle.scope == ComplianceScope.DATA_TYPE:
            context_data_types = context.get("data_types", [])
            return toggle.scope_value in context_data_types

        elif toggle.scope == ComplianceScope.JURISDICTION:
            return context.get("jurisdiction") == toggle.scope_value

        # Check additional conditions
        if toggle.conditions:
            for condition_key, condition_value in toggle.conditions.items():
                if condition_key == "data_types":
                    context_data_types = set(context.get("data_types", []))
                    required_data_types = set(condition_value)
                    if not required_data_types.intersection(context_data_types):
                        return False
                elif context.get(condition_key) != condition_value:
                    return False

        return False

    def _determine_partial_compliance(
        self, context: Dict[str, Any], bypassed_scopes: List[Dict[str, Any]]
    ) -> bool:
        """Determine if compliance is required when some scopes are bypassed"""

        # If biometric data is present and not bypassed, compliance is required
        data_types = context.get("data_types", [])
        biometric_bypassed = any(
            scope["scope"] == "data_type"
            and scope["scope_value"] in ["biometric_data", "facial_recognition"]
            for scope in bypassed_scopes
        )

        if any("biometric" in dt for dt in data_types) and not biometric_bypassed:
            return True

        # If processing purpose requires consent and not bypassed
        purpose = context.get("processing_purpose", "")
        purpose_bypassed = any(
            scope["scope"] == "purpose" and scope["scope_value"] == purpose
            for scope in bypassed_scopes
        )

        consent_required_purposes = [
            "behavioral_analysis",
            "location_tracking",
            "marketing_analytics",
        ]
        if purpose in consent_required_purposes and not purpose_bypassed:
            return True

        # Default to no compliance required if other aspects are bypassed
        return False

    def _add_bypass_warnings(
        self, result: Dict[str, Any], context: Dict[str, Any]
    ) -> None:
        """Add warnings for potentially risky bypasses"""

        warnings = []

        # Warn about biometric data bypasses
        if any("biometric" in str(scope) for scope in result["bypassed_scopes"]):
            data_types = context.get("data_types", [])
            if any("biometric" in dt for dt in data_types):
                warnings.append(
                    "WARNING: Biometric data processing bypassed compliance checks"
                )

        # Warn about client bypasses without proper reason
        client_bypasses = [
            s for s in result["bypassed_scopes"] if s["scope"] == "client"
        ]
        for bypass in client_bypasses:
            if bypass["bypass_reason"] == "not_specified":
                warnings.append(
                    f"WARNING: Client {bypass['scope_value']} bypass has no specified reason"
                )

        # Warn about global bypasses
        if any(scope["scope"] == "global" for scope in result["bypassed_scopes"]):
            warnings.append("WARNING: Global compliance bypass is active")

        result["warnings"] = warnings

    def _load_toggles(self) -> None:
        """Load toggles from database"""
        try:
            query_sql = """
                SELECT toggle_id, scope, scope_value, enabled, bypass_reason,
                       description, created_by, created_at, expires_at, conditions
                FROM compliance_toggles
                WHERE (expires_at IS NULL OR expires_at > NOW())
                ORDER BY created_at DESC
            """

            df = execute_query(self.db, query_sql)

            for row in df.itertuples(index=False):
                toggle = ComplianceToggle(
                    id=row.toggle_id,
                    scope=ComplianceScope(row.scope),
                    scope_value=row.scope_value,
                    enabled=row.enabled,
                    bypass_reason=(
                        BypassReason(row.bypass_reason) if row.bypass_reason else None
                    ),
                    description=row.description or "",
                    created_by=row.created_by,
                    created_at=row.created_at,
                    expires_at=row.expires_at,
                    conditions=(json.loads(row.conditions) if row.conditions else {}),
                )

                self.toggles[toggle.id] = toggle

            logger.info(f"Loaded {len(self.toggles)} compliance toggles")

        except Exception as e:
            logger.error(f"Failed to load compliance toggles: {e}")
            self.toggles = {}

    def _store_toggle(self, toggle: ComplianceToggle) -> None:
        """Store toggle in database"""
        import json

        upsert_sql = """
            INSERT INTO compliance_toggles 
            (toggle_id, scope, scope_value, enabled, bypass_reason, description,
             created_by, created_at, expires_at, conditions)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (toggle_id) DO UPDATE SET
                enabled = EXCLUDED.enabled,
                bypass_reason = EXCLUDED.bypass_reason,
                description = EXCLUDED.description,
                expires_at = EXCLUDED.expires_at,
                conditions = EXCLUDED.conditions,
                updated_at = NOW()
        """

        execute_command(
            self.db,
            upsert_sql,
            (
                toggle.id,
                toggle.scope.value,
                toggle.scope_value,
                toggle.enabled,
                toggle.bypass_reason.value if toggle.bypass_reason else None,
                toggle.description,
                toggle.created_by,
                toggle.created_at,
                toggle.expires_at,
                json.dumps(toggle.conditions),
            ),
        )


# Enhanced Compliance Plugin with Toggle Support
# =============================================================================


# plugins/compliance_plugin/plugin.py (Enhanced)
class CompliancePlugin(BasePlugin):
    """Enhanced compliance plugin with toggle system"""

    def __init__(self):
        super().__init__()
        self.toggle_manager: Optional[ComplianceToggleManager] = None

    def initialize(self, container: Container, config: Dict[str, Any]) -> bool:
        """Initialize plugin with toggle manager"""

        # Initialize base components
        success = super().initialize(container, config)
        if not success:
            return False

        # Initialize toggle manager
        if self.services and self.services.audit_logger:
            self.toggle_manager = ComplianceToggleManager(
                db=container.get("database"), audit_logger=self.services.audit_logger
            )

            # Register toggle manager with container
            container.register("compliance_toggle_manager", self.toggle_manager)

        return True

    def _hook_csv_pre_process(self, **kwargs) -> Dict[str, Any]:
        """Enhanced CSV pre-processing with toggle support"""

        if not self.toggle_manager:
            return {"status": "proceed"}

        # Build context for toggle decision
        context = {
            "data_source": kwargs.get("upload_context", {}).get("data_source", ""),
            "processing_purpose": kwargs.get("upload_context", {}).get(
                "processing_purpose", ""
            ),
            "client_id": kwargs.get("upload_context", {}).get("client_id", ""),
            "user_type": kwargs.get("upload_context", {}).get("user_type", "employee"),
            "jurisdiction": kwargs.get("upload_context", {}).get("jurisdiction", "EU"),
            "uploaded_by": kwargs.get("uploaded_by", "unknown"),
            "data_types": [],  # Will be determined by CSV analysis
        }

        # Check if compliance should be applied
        toggle_decision = self.toggle_manager.should_apply_compliance(context)

        if not toggle_decision["compliance_required"]:
            # Compliance bypassed
            return {
                "status": "proceed",
                "compliance_bypassed": True,
                "bypass_reasons": toggle_decision["bypass_reasons"],
                "bypassed_scopes": toggle_decision["bypassed_scopes"],
                "warnings": toggle_decision["warnings"],
            }

        # Proceed with normal compliance checking
        if self.services and self.services.csv_processor:
            result = csv_pre_process_callback(
                self.services,
                kwargs.get("file_path"),
                kwargs.get("upload_context"),
                kwargs.get("uploaded_by"),
            )

            # Add toggle information to result
            result["toggle_decision"] = toggle_decision
            return result

        return {"status": "proceed"}


# Enhanced CSV Processing Route with Toggle Support
# =============================================================================


def create_enhanced_csv_upload_with_toggles():
    """Enhanced CSV upload route with compliance toggle support"""

    @app.route("/api/upload/csv", methods=["POST"])
    @login_required
    def upload_csv_with_toggle_support():
        """CSV upload with granular compliance control"""

        if "file" not in request.files:
            return jsonify({"error": "No file provided"}), 400

        file = request.files["file"]
        file_path = save_uploaded_file(file)

        # Enhanced upload context with toggle-relevant information
        upload_context = {
            "processing_purpose": request.form.get("purpose", ""),
            "data_source": request.form.get("data_source", ""),
            "client_id": request.form.get("client_id", ""),  # NEW: Client identifier
            "user_type": request.form.get("user_type", "employee"),  # NEW: User type
            "jurisdiction": request.form.get("jurisdiction", "EU"),
            "consent_confirmed": request.form.get("consent_confirmed") == "true",
            "compliance_bypass_reason": request.form.get(
                "bypass_reason", ""
            ),  # NEW: Manual bypass
            "dpo_approval": request.form.get("dpo_approval") == "true",
        }

        try:
            # Call compliance hook (now toggle-aware)
            pre_result = call_plugin_hook(
                "csv_upload_pre_process",
                file_path=file_path,
                upload_context=upload_context,
                uploaded_by=current_user.id,
            )

            # Handle compliance bypass
            if pre_result.get("compliance_bypassed"):
                logger.info(
                    f"Compliance bypassed for upload by {current_user.id}: {pre_result.get('bypass_reasons')}"
                )

                # Process CSV without compliance checks
                df = FileProcessor.read_large_csv(file_path)
                processing_id = str(uuid4())
                processed_data = process_csv_data(df)  # Your existing processing
                store_csv_results(processing_id, processed_data)

                return jsonify(
                    {
                        "status": "success",
                        "processing_id": processing_id,
                        "rows_processed": len(processed_data),
                        "compliance_status": "bypassed",
                        "bypass_reasons": pre_result.get("bypass_reasons", []),
                        "warnings": pre_result.get("warnings", []),
                        "message": "CSV processed with compliance bypass",
                    }
                )

            # Handle compliance denial
            elif pre_result.get("status") == "block":
                return (
                    jsonify(
                        {
                            "status": "denied",
                            "reason": pre_result.get("reason"),
                            "required_consents": pre_result.get(
                                "required_consents", []
                            ),
                            "classification": pre_result.get("classification", {}),
                        }
                    ),
                    403,
                )

            # Normal compliance processing
            else:
                df = FileProcessor.read_large_csv(file_path)
                processing_id = str(uuid4())
                processed_data = process_csv_data(df)
                store_csv_results(processing_id, processed_data)

                # Post-processing hook
                call_plugin_hook(
                    "csv_upload_post_process",
                    processing_id=processing_id,
                    compliance_metadata=pre_result.get("compliance_metadata", {}),
                    processed_data=processed_data,
                )

                return jsonify(
                    {
                        "status": "success",
                        "processing_id": processing_id,
                        "rows_processed": len(processed_data),
                        "compliance_status": "applied",
                        "classification": pre_result.get("classification", {}),
                        "toggle_info": pre_result.get("toggle_decision", {}),
                        "message": "CSV processed with full compliance verification",
                    }
                )

        except Exception as e:
            logger.error(f"CSV upload failed: {e}")
            return jsonify({"error": "Upload processing failed"}), 500


# Compliance Toggle Management API
# =============================================================================


def create_toggle_management_api():
    """API endpoints for managing compliance toggles"""

    @app.route("/api/v1/compliance/toggles", methods=["GET"])
    @login_required
    @require_role("admin")
    def list_compliance_toggles():
        """List all compliance toggles"""

        container = Container()
        toggle_manager = container.get("compliance_toggle_manager")

        if not toggle_manager:
            return jsonify({"error": "Toggle manager not available"}), 503

        scope_filter = request.args.get("scope")
        active_only = request.args.get("active_only", "true").lower() == "true"

        scope_enum = None
        if scope_filter:
            try:
                scope_enum = ComplianceScope(scope_filter)
            except ValueError:
                return jsonify({"error": f"Invalid scope: {scope_filter}"}), 400

        toggles = toggle_manager.list_toggles(scope=scope_enum, active_only=active_only)

        return jsonify(
            {
                "toggles": [toggle.to_dict() for toggle in toggles],
                "total_count": len(toggles),
            }
        )

    @app.route("/api/v1/compliance/toggles", methods=["POST"])
    @login_required
    @require_role("admin")
    def create_compliance_toggle():
        """Create a new compliance toggle"""

        data = request.get_json()

        required_fields = ["scope", "scope_value", "enabled"]
        if not all(field in data for field in required_fields):
            return jsonify({"error": "Missing required fields"}), 400

        try:
            scope = ComplianceScope(data["scope"])
            bypass_reason = (
                BypassReason(data["bypass_reason"])
                if data.get("bypass_reason")
                else None
            )

            container = Container()
            toggle_manager = container.get("compliance_toggle_manager")

            expires_at = None
            if data.get("expires_at"):
                expires_at = datetime.fromisoformat(
                    data["expires_at"].replace("Z", "+00:00")
                )

            toggle_id = toggle_manager.create_toggle(
                scope=scope,
                scope_value=data["scope_value"],
                enabled=data["enabled"],
                bypass_reason=bypass_reason,
                description=data.get("description", ""),
                created_by=current_user.id,
                expires_at=expires_at,
                conditions=data.get("conditions", {}),
            )

            return (
                jsonify(
                    {
                        "toggle_id": toggle_id,
                        "message": "Compliance toggle created successfully",
                    }
                ),
                201,
            )

        except ValueError as e:
            return jsonify({"error": f"Invalid enum value: {e}"}), 400
        except Exception as e:
            logger.error(f"Failed to create toggle: {e}")
            return jsonify({"error": "Failed to create toggle"}), 500

    @app.route("/api/v1/compliance/toggles/<toggle_id>", methods=["PUT"])
    @login_required
    @require_role("admin")
    def update_compliance_toggle(toggle_id: str):
        """Update a compliance toggle"""

        data = request.get_json()

        container = Container()
        toggle_manager = container.get("compliance_toggle_manager")

        try:
            bypass_reason = None
            if data.get("bypass_reason"):
                bypass_reason = BypassReason(data["bypass_reason"])

            expires_at = None
            if data.get("expires_at"):
                expires_at = datetime.fromisoformat(
                    data["expires_at"].replace("Z", "+00:00")
                )

            success = toggle_manager.update_toggle(
                toggle_id=toggle_id,
                enabled=data.get("enabled"),
                bypass_reason=bypass_reason,
                description=data.get("description"),
                expires_at=expires_at,
                updated_by=current_user.id,
            )

            if success:
                return jsonify({"message": "Toggle updated successfully"})
            else:
                return jsonify({"error": "Toggle not found"}), 404

        except Exception as e:
            logger.error(f"Failed to update toggle: {e}")
            return jsonify({"error": "Failed to update toggle"}), 500

    @app.route("/api/v1/compliance/toggles/<toggle_id>", methods=["DELETE"])
    @login_required
    @require_role("admin")
    def delete_compliance_toggle(toggle_id: str):
        """Delete a compliance toggle"""

        container = Container()
        toggle_manager = container.get("compliance_toggle_manager")

        success = toggle_manager.delete_toggle(toggle_id, current_user.id)

        if success:
            return jsonify({"message": "Toggle deleted successfully"})
        else:
            return jsonify({"error": "Toggle not found"}), 404


# Enhanced Frontend with Toggle Management
# =============================================================================

COMPLIANCE_TOGGLE_UI = """
<!-- Compliance Toggle Management Interface -->
<div class="compliance-toggles-section">
    <h3>Compliance Toggle Management</h3>
    
    <!-- Quick Actions -->
    <div class="quick-actions">
        <button id="create-client-bypass" class="btn btn-warning">
            Create Client Bypass
        </button>
        <button id="create-purpose-bypass" class="btn btn-warning">
            Create Purpose Bypass
        </button>
        <button id="emergency-bypass" class="btn btn-danger">
            Emergency Global Bypass
        </button>
    </div>
    
    <!-- Toggle List -->
    <div class="toggles-list">
        <table id="toggles-table">
            <thead>
                <tr>
                    <th>Scope</th>
                    <th>Value</th>
                    <th>Status</th>
                    <th>Bypass Reason</th>
                    <th>Created By</th>
                    <th>Expires</th>
                    <th>Actions</th>
                </tr>
            </thead>
            <tbody id="toggles-tbody">
                <!-- Populated by JavaScript -->
            </tbody>
        </table>
    </div>
</div>

<!-- Enhanced CSV Upload Form with Client/Purpose Selection -->
<form id="csv-upload-form-enhanced" enctype="multipart/form-data">
    <div class="upload-section">
        <h3>Upload CSV Data with Compliance Control</h3>
        
        <div class="file-input">
            <input type="file" id="csv-file" name="file" accept=".csv" required>
            <label for="csv-file">Choose CSV File</label>
        </div>
        
        <!-- Client Information -->
        <div class="client-section">
            <h4>Client & Data Source Information</h4>
            
            <div class="field">
                <label for="client-id">Client ID</label>
                <select id="client-id" name="client_id">
                    <option value="">Select client...</option>
                    <option value="client_abc">Client ABC (Compliance Handled)</option>
                    <option value="client_xyz">Client XYZ (Requires Compliance)</option>
                    <option value="internal">Internal Data</option>
                </select>
            </div>
            
            <div class="field">
                <label for="data-source">Data Source</label>
                <input type="text" id="data-source" name="data_source" 
                       placeholder="e.g., Badge System Export, HR Database">
            </div>
            
            <div class="field">
                <label for="user-type">User Type</label>
                <select id="user-type" name="user_type">
                    <option value="employee">Employee</option>
                    <option value="visitor">Visitor</option>
                    <option value="contractor">Contractor</option>
                    <option value="external">External</option>
                </select>
            </div>
        </div>
        
        <!-- Processing Information -->
        <div class="processing-section">
            <h4>Processing Information</h4>
            
            <div class="field">
                <label for="purpose">Processing Purpose *</label>
                <select id="purpose" name="processing_purpose" required>
                    <option value="">Select purpose...</option>
                    <option value="security_monitoring">Security Monitoring</option>
                    <option value="access_control">Access Control</option>
                    <option value="behavioral_analysis">Behavioral Analysis</option>
                    <option value="compliance_reporting">Compliance Reporting</option>
                    <option value="internal_operations">Internal Operations</option>
                </select>
            </div>
            
            <div class="field">
                <label for="jurisdiction">Jurisdiction</label>
                <select id="jurisdiction" name="jurisdiction">
                    <option value="EU">European Union (GDPR)</option>
                    <option value="JP">Japan (APPI)</option>
                    <option value="US">United States</option>
                    <option value="internal">Internal Only</option>
                </select>
            </div>
        </div>
        
        <!-- Compliance Override -->
        <div class="override-section">
            <h4>Compliance Override (Admin Only)</h4>
            
            <div class="field">
                <label for="bypass-reason">Bypass Reason</label>
                <select id="bypass-reason" name="bypass_reason">
                    <option value="">No bypass</option>
                    <option value="client_handled">Client Already Handled Compliance</option>
                    <option value="internal_data">Internal Operational Data</option>
                    <option value="anonymized_data">Data Already Anonymized</option>
                    <option value="emergency_processing">Emergency/Security Situation</option>
                    <option value="development_testing">Development/Testing</option>
                </select>
            </div>
            
            <div class="checkbox-field">
                <input type="checkbox" id="consent-confirmed" name="consent_confirmed">
                <label for="consent-confirmed">
                    Consent confirmed for all personal data processing
                </label>
            </div>
        </div>
        
        <button type="submit" id="upload-btn">Upload with Smart Compliance</button>
    </div>
    
    <!-- Results with toggle information -->
    <div id="upload-results" style="display: none;">
        <h4>Upload Results</h4>
        <div id="results-content"></div>
    </div>
</form>

<script>
// Enhanced upload handling with toggle awareness
document.getElementById('csv-upload-form-enhanced').onsubmit = function(e) {
    e.preventDefault();
    
    const formData = new FormData(this);
    const uploadBtn = document.getElementById('upload-btn');
    
    uploadBtn.textContent = 'Processing with Smart Compliance...';
    uploadBtn.disabled = true;
    
    fetch('/api/upload/csv', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        const resultsDiv = document.getElementById('results-content');
        
        if (data.status === 'success') {
            let complianceStatus = '';
            
            if (data.compliance_status === 'bypassed') {
                complianceStatus = `
                    <div class="compliance-bypassed">
                        <h6>⚠️ Compliance Bypassed</h6>
                        <p><strong>Reasons:</strong> ${data.bypass_reasons.join(', ')}</p>
                        ${data.warnings.length > 0 ? `
                            <div class="warnings">
                                <strong>Warnings:</strong>
                                <ul>${data.warnings.map(w => `<li>${w}</li>`).join('')}</ul>
                            </div>
                        ` : ''}
                    </div>
                `;
            } else {
                complianceStatus = `
                    <div class="compliance-applied">
                        <h6>✅ Full Compliance Applied</h6>
                        <p><strong>Classification:</strong> ${data.classification.sensitivity_level}</p>
                        <p><strong>Legal Basis:</strong> ${data.classification.legal_basis_recommendation}</p>
                    </div>
                `;
            }
            
            resultsDiv.innerHTML = `
                <div class="success">
                    <h5>✅ Upload Successful</h5>
                    <p><strong>Processing ID:</strong> ${data.processing_id}</p>
                    <p><strong>Rows Processed:</strong> ${data.rows_processed}</p>
                    ${complianceStatus}
                </div>
            `;
        } else if (data.status === 'denied') {
            resultsDiv.innerHTML = `
                <div class="error">
                    <h5>❌ Upload Denied</h5>
                    <p><strong>Reason:</strong> ${data.reason}</p>
                    <p>Please ensure compliance requirements are met or request appropriate bypass.</p>
                </div>
            `;
        }
        
        document.getElementById('upload-results').style.display = 'block';
        uploadBtn.textContent = 'Upload with Smart Compliance';
        uploadBtn.disabled = false;
    });
};

// Toggle management functions
function loadComplianceToggles() {
    fetch('/api/v1/compliance/toggles')
    .then(response => response.json())
    .then(data => {
        const tbody = document.getElementById('toggles-tbody');
        tbody.innerHTML = data.toggles.map(toggle => `
            <tr>
                <td>${toggle.scope}</td>
                <td>${toggle.scope_value}</td>
                <td>
                    <span class="status ${toggle.enabled ? 'enabled' : 'disabled'}">
                        ${toggle.enabled ? 'Enabled' : 'Bypassed'}
                    </span>
                </td>
                <td>${toggle.bypass_reason || 'N/A'}</td>
                <td>${toggle.created_by}</td>
                <td>${toggle.expires_at ? new Date(toggle.expires_at).toLocaleDateString() : 'Never'}</td>
                <td>
                    <button onclick="editToggle('${toggle.id}')" class="btn-sm">Edit</button>
                    <button onclick="deleteToggle('${toggle.id}')" class="btn-sm btn-danger">Delete</button>
                </td>
            </tr>
        `).join('');
    });
}

// Quick client bypass creation
document.getElementById('create-client-bypass').onclick = function() {
    const clientId = prompt('Enter Client ID:');
    const description = prompt('Enter bypass description:');
    
    if (clientId && description) {
        fetch('/api/v1/compliance/toggles', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                scope: 'client',
                scope_value: clientId,
                enabled: false,
                bypass_reason: 'client_handled',
                description: description
            })
        }).then(() => {
            alert('Client bypass created');
            loadComplianceToggles();
        });
    }
};

// Load toggles on page load
document.addEventListener('DOMContentLoaded', loadComplianceToggles);
</script>
"""


# Database Schema for Toggle System
# =============================================================================

COMPLIANCE_TOGGLE_SCHEMA_SQL = """
-- Compliance Toggle Management Tables

CREATE TABLE IF NOT EXISTS compliance_toggles (
    toggle_id VARCHAR(100) PRIMARY KEY,
    scope VARCHAR(20) NOT NULL,
    scope_value VARCHAR(100) NOT NULL,
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    bypass_reason VARCHAR(30),
    description TEXT,
    created_by VARCHAR(50) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE,
    conditions JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_compliance_toggles_scope ON compliance_toggles(scope, scope_value);
CREATE INDEX IF NOT EXISTS idx_compliance_toggles_active ON compliance_toggles(enabled, expires_at);
CREATE INDEX IF NOT EXISTS idx_compliance_toggles_created_by ON compliance_toggles(created_by);

-- Trigger for updating updated_at
CREATE OR REPLACE FUNCTION update_compliance_toggle_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_compliance_toggle_updated_at
    BEFORE UPDATE ON compliance_toggles
    FOR EACH ROW
    EXECUTE FUNCTION update_compliance_toggle_updated_at();
"""
