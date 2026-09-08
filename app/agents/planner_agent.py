class PlannerAgent:
    """
    LegalMind workflow planner.

    Captures intent and estimates document complexity,
    producing a deterministic execution plan for LangGraph.
    """

    COMPLEXITIES = {
        "SIMPLE",
        "MEDIUM",
        "COMPLEX",
    }

    def create_plan(self, document_id, metadata=None):
        metadata = metadata or {}

        page_count = metadata.get("page_count", 0)
        user_instruction = str(
            metadata.get("user_instruction", "")
        ).lower()

        try:
            page_count = int(page_count)
        except (TypeError, ValueError):
            page_count = 0

        complexity = self.estimate_complexity(
            page_count=page_count,
            user_instruction=user_instruction,
        )

        return {
            "document_id": document_id,
            "complexity": complexity,
            "intent": user_instruction,
            "execution_plan": self._build_execution_plan(
                complexity
            ),
        }

    def estimate_complexity(
        self,
        page_count=0,
        user_instruction="",
    ):
        keywords = (
            "litigation",
            "dispute",
            "compliance",
            "indemnity",
            "liability",
            "termination",
            "governing law",
            "regulatory",
            "multi-party",
            "redline",
        )

        keyword_hits = sum(
            1
            for keyword in keywords
            if keyword in user_instruction
        )

        if page_count >= 30 or keyword_hits >= 3:
            return "COMPLEX"

        if page_count >= 10 or keyword_hits >= 1:
            return "MEDIUM"

        return "SIMPLE"

    def _build_execution_plan(self, complexity):
        if complexity not in self.COMPLEXITIES:
            raise ValueError(
                f"Unsupported complexity: {complexity}"
            )

        plan = [
            "document",
            "clause_segmentation",
            "metadata",
            "chunking",
            "risk",
        ]

        if complexity in {"MEDIUM", "COMPLEX"}:
            plan.extend([
                "research",
                "reasoning",
                "critic",
                "explainability",
            ])

        if complexity == "COMPLEX":
            plan.append("hitl")

        plan.append("report")

        return plan
