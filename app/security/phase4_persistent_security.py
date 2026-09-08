
from pathlib import Path
import hashlib
import json
import time


class Phase4PersistentAuditLog:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def _load(self):
        if not self.path.exists():
            return []
        return json.loads(
            self.path.read_text(encoding="utf-8")
        )

    def append(self, event, actor, metadata=None):
        records = self._load()

        previous_hash = (
            records[-1]["record_hash"]
            if records
            else "GENESIS"
        )

        record = {
            "audit_id": len(records) + 1,
            "timestamp": time.time(),
            "event": str(event),
            "actor": str(actor),
            "metadata": metadata or {},
            "previous_hash": previous_hash,
        }

        payload = json.dumps(
            record,
            sort_keys=True,
            separators=(",", ":"),
        )

        record["record_hash"] = hashlib.sha256(
            payload.encode("utf-8")
        ).hexdigest()

        records.append(record)

        self.path.write_text(
            json.dumps(records, indent=2),
            encoding="utf-8",
        )

        return record

    def verify(self):
        records = self._load()
        previous_hash = "GENESIS"

        for record in records:
            if record["previous_hash"] != previous_hash:
                return False

            payload = {
                key: value
                for key, value in record.items()
                if key != "record_hash"
            }

            serialized = json.dumps(
                payload,
                sort_keys=True,
                separators=(",", ":"),
            )

            expected_hash = hashlib.sha256(
                serialized.encode("utf-8")
            ).hexdigest()

            if record["record_hash"] != expected_hash:
                return False

            previous_hash = record["record_hash"]

        return True

    def records(self):
        return self._load()


class Phase4RBACGate:
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
            "review",
        },
        "viewer": {
            "read",
        },
    }

    def authorize(self, role, permission):
        permissions = self.ROLE_PERMISSIONS.get(
            str(role),
            set(),
        )
        return str(permission) in permissions

    def require(self, role, permission):
        if not self.authorize(role, permission):
            raise PermissionError(
                f"Role '{role}' is not authorized "
                f"for '{permission}'."
            )
        return True


class Phase4SecurityBoundary:
    def __init__(self, audit_path):
        self.audit = Phase4PersistentAuditLog(
            audit_path
        )
        self.rbac = Phase4RBACGate()

    def authorize_and_audit(
        self,
        role,
        permission,
        actor,
        event,
        metadata=None,
    ):
        self.rbac.require(role, permission)

        return self.audit.append(
            event=event,
            actor=actor,
            metadata={
                "role": role,
                "permission": permission,
                **(metadata or {}),
            },
        )
