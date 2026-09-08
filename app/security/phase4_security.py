
import hashlib
import json
import re
import time
from pathlib import Path


class Phase4Redactor:
    PATTERNS = [
        (
            "email",
            re.compile(
                r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
            ),
            "[REDACTED_EMAIL]",
        ),
        (
            "cnic",
            re.compile(
                r"(?<!\d)\d{5}-\d{7}-\d(?!\d)"
            ),
            "[REDACTED_CNIC]",
        ),
        (
            "phone",
            re.compile(
                r"(?<![\d-])(?:\+92|0092|0)\s?(?:3\d{2})[\s-]?\d{7}(?!\d)"
            ),
            "[REDACTED_PHONE]",
        ),
        (
            "credit_card",
            re.compile(
                r"(?<!\d)(?:\d[ -]?){13,19}(?!\d)"
            ),
            "[REDACTED_PAYMENT]",
        ),
    ]

    def redact(self, text):
        redacted = str(text)
        matches = []

        for name, pattern, replacement in self.PATTERNS:
            redacted, count = pattern.subn(replacement, redacted)
            if count:
                matches.append(
                    {
                        "type": name,
                        "count": count,
                    }
                )

        return {
            "text": redacted,
            "redactions": matches,
            "redaction_count": sum(
                item["count"] for item in matches
            ),
        }


class Phase4RBAC:
    ROLE_PERMISSIONS = {
        "admin": {
            "read",
            "write",
            "review",
            "export",
            "delete",
        },
        "reviewer": {
            "read",
            "review",
            "export",
        },
        "analyst": {
            "read",
            "write",
        },
        "viewer": {
            "read",
        },
    }

    def authorize(self, role, permission):
        permissions = self.ROLE_PERMISSIONS.get(role, set())
        return permission in permissions

    def require(self, role, permission):
        if not self.authorize(role, permission):
            raise PermissionError(
                f"Role '{role}' is not authorized for '{permission}'."
            )
        return True


class Phase4RetentionPolicy:
    def __init__(self, retention_days=30):
        if retention_days < 1:
            raise ValueError("retention_days must be >= 1")
        self.retention_days = int(retention_days)

    def is_expired(self, created_at, now=None):
        now = now or time.time()
        return (
            now - float(created_at)
        ) >= self.retention_days * 86400

    def cleanup(self, root, now=None, dry_run=True):
        root = Path(root)
        now = now or time.time()

        if not root.exists():
            return {
                "root": str(root),
                "dry_run": dry_run,
                "eligible": [],
                "deleted": [],
            }

        eligible = []
        deleted = []

        for path in root.rglob("*"):
            if not path.is_file():
                continue

            if self.is_expired(path.stat().st_mtime, now=now):
                eligible.append(str(path))

                if not dry_run:
                    path.unlink()
                    deleted.append(str(path))

        return {
            "root": str(root),
            "dry_run": dry_run,
            "eligible": eligible,
            "deleted": deleted,
        }


class Phase4ImmutableAuditLog:
    def __init__(self):
        self.records = []

    def append(self, event, actor, metadata=None):
        previous_hash = (
            self.records[-1]["record_hash"]
            if self.records
            else "GENESIS"
        )

        record = {
            "sequence": len(self.records) + 1,
            "timestamp": time.time(),
            "event": event,
            "actor": actor,
            "metadata": metadata or {},
            "previous_hash": previous_hash,
        }

        payload = json.dumps(
            record,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")

        record["record_hash"] = hashlib.sha256(
            payload
        ).hexdigest()

        self.records.append(record)

        return record

    def verify(self):
        previous_hash = "GENESIS"

        for index, record in enumerate(self.records, start=1):
            if record["sequence"] != index:
                return False

            if record["previous_hash"] != previous_hash:
                return False

            body = {
                key: value
                for key, value in record.items()
                if key != "record_hash"
            }

            payload = json.dumps(
                body,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")

            expected_hash = hashlib.sha256(
                payload
            ).hexdigest()

            if record["record_hash"] != expected_hash:
                return False

            previous_hash = record["record_hash"]

        return True


class Phase4SecurityPolicy:
    def __init__(self):
        self.encryption_at_rest = {
            "status": "INFRASTRUCTURE_DEPENDENT",
            "application_control": False,
            "note": (
                "Application code does not claim disk encryption. "
                "Storage-level encryption must be provided by the "
                "deployment infrastructure."
            ),
        }

        self.encryption_in_transit = {
            "status": "REQUIRED",
            "https_required": True,
            "tls_required": True,
        }

        self.redaction = {
            "status": "IMPLEMENTED",
            "boundary": "before_external_third_party_calls",
        }

        self.retention = {
            "status": "IMPLEMENTED",
            "default_days": 30,
            "cleanup_mode": "dry_run_by_default",
        }

        self.rbac = {
            "status": "IMPLEMENTED",
            "roles": list(
                Phase4RBAC.ROLE_PERMISSIONS.keys()
            ),
        }

        self.immutable_audit = {
            "status": "IMPLEMENTED",
            "mechanism": "hash_chained_append_only_records",
        }

    def as_dict(self):
        return {
            "encryption_at_rest": self.encryption_at_rest,
            "encryption_in_transit": self.encryption_in_transit,
            "redaction": self.redaction,
            "retention": self.retention,
            "rbac": self.rbac,
            "immutable_audit": self.immutable_audit,
        }
