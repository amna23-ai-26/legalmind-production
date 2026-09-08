
class EvidenceRanker:
    """
    Ranks and deduplicates retrieved legal evidence.

    Evidence sources may include:
    - CourtListener case law
    - Neo4j legal authorities
    - Other future legal corpora
    """

    def __init__(self):
        pass

    @staticmethod
    def _normalize_text(value):
        if value is None:
            return ""

        return " ".join(
            str(value).lower().split()
        )

    def deduplicate(self, evidence):
        """
        Remove duplicate evidence records.

        Uses case_id when available; otherwise
        falls back to title + jurisdiction.
        """

        seen = set()
        unique = []

        for item in evidence:

            key = item.get("case_id")

            if not key:
                key = (
                    self._normalize_text(
                        item.get("title")
                    ),
                    self._normalize_text(
                        item.get("jurisdiction")
                    )
                )

            if key in seen:
                continue

            seen.add(key)
            unique.append(item)

        return unique

    def rank(self, evidence, query=None):
        """
        Rank evidence using available relevance signals.

        Current prototype scoring:
        1. Existing retrieval score
        2. Jurisdiction match
        3. Source quality
        """

        query_text = self._normalize_text(query)

        ranked = []

        for item in evidence:

            score = float(
                item.get(
                    "relevance_score",
                    item.get("score", 0.0)
                ) or 0.0
            )

            title = self._normalize_text(
                item.get("title")
            )

            # Basic lexical relevance.
            if query_text:
                query_terms = set(
                    query_text.split()
                )

                title_terms = set(
                    title.split()
                )

                overlap = (
                    query_terms & title_terms
                )

                score += 0.05 * len(overlap)

            # CourtListener is currently our
            # primary case-law source.
            if item.get("source") == "CourtListener":
                score += 0.05

            item = dict(item)
            item["relevance_score"] = round(
                score,
                6
            )

            ranked.append(item)

        ranked.sort(
            key=lambda x: x["relevance_score"],
            reverse=True
        )

        return ranked

    def process(
        self,
        evidence,
        query=None,
        top_k=5
    ):
        """
        Deduplicate, rank and return Top-K evidence.
        """

        unique = self.deduplicate(
            evidence
        )

        ranked = self.rank(
            unique,
            query=query
        )

        return ranked[:top_k]
