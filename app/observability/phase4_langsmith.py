import os
import time


class Phase4LangSmithInstrumentation:
    def __init__(self, project_name=None):
        self.project_name = (
            project_name
            or os.getenv("LANGSMITH_PROJECT")
            or os.getenv("LANGCHAIN_PROJECT")
            or "legalmind-phase4"
        )
        self.enabled = bool(
            os.getenv("LANGSMITH_API_KEY")
            or os.getenv("LANGCHAIN_API_KEY")
        )

    def start_run(self, run_name="legalmind_phase4_workflow", metadata=None):
        return {
            "run_name": run_name,
            "project_name": self.project_name,
            "enabled": self.enabled,
            "started_at": time.time(),
            "metadata": metadata or {},
        }

    def finish_run(
        self,
        run_state,
        status=None,
        cycles_used=None,
        retry_count=None,
        estimated_cost=None,
        override_action=None,
    ):
        finished_at = time.time()
        started_at = run_state.get("started_at", finished_at)

        return {
            "run_name": run_state.get("run_name"),
            "project_name": run_state.get("project_name"),
            "enabled": run_state.get("enabled", False),
            "status": status,
            "latency_seconds": round(finished_at - started_at, 6),
            "cycles_used": cycles_used,
            "retry_count": retry_count,
            "estimated_cost": estimated_cost,
            "override_action": override_action,
        }

    def record_override(self, action, reviewer_id=None):
        return {
            "project_name": self.project_name,
            "enabled": self.enabled,
            "override_action": action,
            "reviewer_id_present": bool(reviewer_id),
            "timestamp": time.time(),
        }
