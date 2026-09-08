
class RetrievalEvaluator:
    """
    Citation-groundedness evaluation harness for LegalMind Research Agent.

    Metrics:
    - Precision@K
    - Recall@K

    The evaluator compares retrieved evidence against a manually
    defined gold-standard evidence set.
    """

    def __init__(self):
        pass

    @staticmethod
    def _normalize(value):
        if value is None:
            return ""

        return " ".join(
            str(value).lower().split()
        )

    def _evidence_key(self, item):
        """
        Generate a stable identity for an evidence record.

        Priority:
        1. case_id
        2. citation
        3. title + jurisdiction
        4. statute_id
        5. generic title
        """

        if not isinstance(item, dict):
            return self._normalize(item)

        if item.get("case_id"):
            return (
                "case_id",
                self._normalize(item["case_id"])
            )

        citation = item.get("citation")

        if citation:
            if isinstance(citation, list):
                citation = " | ".join(
                    str(x) for x in citation
                )

            return (
                "citation",
                self._normalize(citation)
            )

        if item.get("statute_id"):
            return (
                "statute_id",
                self._normalize(item["statute_id"])
            )

        title = self._normalize(
            item.get("title")
        )

        jurisdiction = self._normalize(
            item.get("jurisdiction")
        )

        if title:
            return (
                "title",
                title,
                jurisdiction
            )

        return (
            "generic",
            str(item)
        )

    def precision_at_k(
        self,
        retrieved,
        gold,
        k=5
    ):
        """
        Precision@K =
        relevant retrieved items in top K / K
        """

        retrieved_top_k = retrieved[:k]

        gold_keys = {
            self._evidence_key(item)
            for item in gold
        }

        if not retrieved_top_k:
            return 0.0

        relevant = sum(
            1
            for item in retrieved_top_k
            if self._evidence_key(item) in gold_keys
        )

        return relevant / len(retrieved_top_k)

    def recall_at_k(
        self,
        retrieved,
        gold,
        k=10
    ):
        """
        Recall@K =
        relevant retrieved items in top K / total gold items
        """

        if not gold:
            return 0.0

        retrieved_top_k = retrieved[:k]

        gold_keys = {
            self._evidence_key(item)
            for item in gold
        }

        retrieved_keys = {
            self._evidence_key(item)
            for item in retrieved_top_k
        }

        relevant = len(
            gold_keys & retrieved_keys
        )

        return relevant / len(gold_keys)

    def evaluate(
        self,
        retrieved,
        gold,
        precision_k=5,
        recall_k=10
    ):
        """
        Calculate the required Phase 2 retrieval metrics.
        """

        precision = self.precision_at_k(
            retrieved,
            gold,
            k=precision_k
        )

        recall = self.recall_at_k(
            retrieved,
            gold,
            k=recall_k
        )

        return {
            "precision_at_5": round(
                precision,
                4
            ),
            "recall_at_10": round(
                recall,
                4
            ),
            "retrieved_count": len(
                retrieved
            ),
            "gold_count": len(
                gold
            )
        }

    def detailed_evaluation(
        self,
        retrieved,
        gold,
        precision_k=5,
        recall_k=10
    ):
        """
        Return metrics plus the exact matching evidence.
        """

        gold_keys = {
            self._evidence_key(item)
            for item in gold
        }

        retrieved_top_5 = retrieved[:precision_k]
        retrieved_top_10 = retrieved[:recall_k]

        precision_matches = [
            item
            for item in retrieved_top_5
            if self._evidence_key(item) in gold_keys
        ]

        recall_matches = [
            item
            for item in retrieved_top_10
            if self._evidence_key(item) in gold_keys
        ]

        metrics = self.evaluate(
            retrieved,
            gold,
            precision_k=precision_k,
            recall_k=recall_k
        )

        return {
            "metrics": metrics,
            "precision_matches": precision_matches,
            "recall_matches": recall_matches
        }
