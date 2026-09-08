from app.security.phase4_security import (
    Phase4Redactor,
    Phase4RetentionPolicy,
    Phase4SecurityPolicy,
)
from app.security.phase4_persistent_security import Phase4SecurityBoundary


class Phase4SecurityExecutionBoundary:
    def __init__(self, audit_path):
        self.redactor = Phase4Redactor()
        self.retention_policy = Phase4RetentionPolicy()
        self.policy = Phase4SecurityPolicy()
        self.boundary = Phase4SecurityBoundary(audit_path)

    def authorize(self, role, permission, actor, event, metadata=None):
        return self.boundary.authorize_and_audit(
            role=role,
            permission=permission,
            actor=actor,
            event=event,
            metadata=metadata,
        )

    def redact(self, text):
        return self.redactor.redact(text)

    def retention_status(self):
        return {
            "status": "IMPLEMENTED",
            "retention_days": self.retention_policy.retention_days,
            "cleanup_mode": "dry_run_by_default",
        }

    def security_status(self):
        return self.policy.as_dict()

    def audit_status(self):
        return {
            "records": len(self.boundary.audit.records()),
            "chain_valid": self.boundary.audit.verify(),
        }
