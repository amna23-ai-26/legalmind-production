class ExplainabilityAgent:
    """
    Phase 3 Explainability Agent v1.

    Produces recommendation-level evidence mapping,
    confidence components, self-consistency, and reasoning paths.
    """

    def __init__(self):
        self.version = "phase3-explainability-v1"

    def process(
        self,
        reasoning_result,
        research_result,
        critic_result,
        reasoning_samples=None,
        evidence_graph=None,
    ):
        if not isinstance(reasoning_result, dict):
            return self._failure(
                "reasoning_result must be a dictionary"
            )

        if not isinstance(research_result, dict):
            return self._failure(
                "research_result must be a dictionary"
            )

        if not isinstance(critic_result, dict):
            return self._failure(
                "critic_result must be a dictionary"
            )

        recommendations = self._get_recommendations(
            reasoning_result
        )

        evidence = self._get_evidence(
            reasoning_result,
            research_result
        )

        retrieval_similarity = self._retrieval_similarity(
            evidence
        )

        critic_score = self._critic_score(
            critic_result
        )

        consistency = self._self_consistency(
            reasoning_samples
        )

        confidence = self._confidence_score(
            retrieval_similarity,
            critic_score,
            consistency["score"]
        )

        recommendation_explanations = []

        for recommendation in recommendations:
            recommendation_explanations.append({
                "recommendation": recommendation,
                "supporting_evidence": evidence,
                "retrieval_similarity": retrieval_similarity,
                "critic_outcome": critic_result.get(
                    "status"
                ),
                "confidence_score": confidence,
            })

        return {
            "explainability_version": self.version,
            "contract_id": research_result.get(
                "contract_id"
            ),
            "clause_id": research_result.get(
                "clause_id"
            ),
            "recommendations": recommendation_explanations,
            "confidence": {
                "score": confidence,
                "retrieval_similarity": retrieval_similarity,
                "critic_score": critic_score,
                "self_consistency": consistency,
            },
            "reasoning_path": {
                "clause_id": research_result.get(
                    "clause_id"
                ),
                "evidence_sources": self._evidence_sources(
                    evidence
                ),
                "recommendation_count": len(
                    recommendations
                ),
            },
            "evidence_graph": (
                evidence_graph
                if isinstance(evidence_graph, dict)
                else {
                    "available": False,
                    "nodes": [],
                    "edges": [],
                }
            ),
        }

    def _get_recommendations(self, reasoning_result):
        recommendations = reasoning_result.get(
            "negotiation_recommendations",
            []
        )

        if recommendations is None:
            return []

        if isinstance(recommendations, str):
            return [recommendations]

        if not isinstance(recommendations, list):
            return []

        return [
            str(item).strip()
            for item in recommendations
            if str(item).strip()
        ]

    def _get_evidence(self, reasoning_result, research_result):
        supporting = reasoning_result.get(
            "supporting_evidence",
            {}
        )

        if not isinstance(supporting, dict):
            supporting = {}

        evidence = []

        for key in (
            "legal_authorities",
            "case_law",
        ):
            items = supporting.get(key, [])

            if not isinstance(items, list):
                continue

            for item in items:
                if isinstance(item, dict):
                    evidence.append(item)

        if evidence:
            return evidence

        fallback = research_result.get(
            "evidence",
            []
        )

        if not isinstance(fallback, list):
            return []

        return [
            item for item in fallback
            if isinstance(item, dict)
        ]

    def _retrieval_similarity(self, evidence):
        scores = []

        for item in evidence:
            value = item.get(
                "relevance_score"
            )

            if value is None:
                value = item.get("score")

            if value is None:
                continue

            try:
                score = float(value)
            except (TypeError, ValueError):
                continue

            if 0.0 <= score <= 1.0:
                scores.append(score)

        if not scores:
            return 0.0

        return sum(scores) / len(scores)

    def _critic_score(self, critic_result):
        status = str(
            critic_result.get("status", "")
        ).upper()

        if status == "PASS":
            return 1.0

        if status == "FAIL":
            return 0.0

        return 0.0

    def _self_consistency(self, reasoning_samples):
        if not isinstance(reasoning_samples, list):
            return {
                "n": 0,
                "score": 0.0,
                "passed": False,
            }

        samples = [
            item
            for item in reasoning_samples
            if isinstance(item, dict)
        ]

        if len(samples) != 3:
            return {
                "n": len(samples),
                "score": 0.0,
                "passed": False,
            }

        signatures = [
            self._reasoning_signature(item)
            for item in samples
        ]

        matching = 0

        for i in range(len(signatures)):
            for j in range(i + 1, len(signatures)):
                if signatures[i] == signatures[j]:
                    matching += 1

        score = matching / 3.0

        return {
            "n": 3,
            "score": score,
            "passed": score == 1.0,
        }

    def _reasoning_signature(self, reasoning_result):
        recommendations = self._get_recommendations(
            reasoning_result
        )

        assessment = reasoning_result.get(
            "legal_assessment",
            ""
        )

        return (
            str(assessment).strip().lower(),
            tuple(
                item.lower()
                for item in recommendations
            ),
        )

    def _confidence_score(
        self,
        retrieval_similarity,
        critic_score,
        self_consistency_score,
    ):
        score = (
            retrieval_similarity
            + critic_score
            + self_consistency_score
        ) / 3.0

        return round(
            max(0.0, min(1.0, score)),
            4
        )

    def _evidence_sources(self, evidence):
        sources = []

        for item in evidence:
            source = item.get("source")

            if source and source not in sources:
                sources.append(source)

        return sources

    def _failure(self, message):
        return {
            "explainability_version": self.version,
            "status": "FAIL",
            "error": message,
            "confidence": {
                "score": 0.0,
                "retrieval_similarity": 0.0,
                "critic_score": 0.0,
                "self_consistency": {
                    "n": 0,
                    "score": 0.0,
                    "passed": False,
                },
            },
        }
