
class HITLTrigger:
    """
    Phase 3 Human-in-the-Loop trigger v1.

    Pauses workflow when the document risk score exceeds
    the configured threshold.

    Read-only with respect to existing risk findings.
    """

    def __init__(self, threshold=3):
        if threshold != 3:
            raise ValueError(
                "Phase 3 HITL threshold must be 3."
            )

        self.threshold = threshold

    def evaluate(self, risk_findings):
        if not isinstance(risk_findings, list):
            return {
                "status": "FAIL",
                "paused": False,
                "hitl_required": False,
                "document_risk_score": 0,
                "threshold": self.threshold,
                "reason": (
                    "risk_findings must be a list"
                ),
            }

        risk_scores = [
            item.get("risk_score")
            for item in risk_findings
            if isinstance(item, dict)
            and isinstance(
                item.get("risk_score"),
                (int, float)
            )
        ]

        document_risk_score = (
            max(risk_scores)
            if risk_scores
            else 0
        )

        hitl_required = (
            document_risk_score > self.threshold
        )

        return {
            "status": (
                "PAUSED"
                if hitl_required
                else "CONTINUE"
            ),
            "paused": hitl_required,
            "hitl_required": hitl_required,
            "document_risk_score": document_risk_score,
            "threshold": self.threshold,
            "reason": (
                "Document risk score exceeds HITL threshold."
                if hitl_required
                else "Document risk score is within threshold."
            ),
        }
