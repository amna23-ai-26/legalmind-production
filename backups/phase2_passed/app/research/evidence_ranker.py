
class EvidenceRanker:
    """
    Normalizes, deduplicates, tags, and ranks LegalMind evidence.
    """

    def __init__(self):
        pass

    @staticmethod
    def normalize_bm25(results):
        """
        Convert BM25 results into a common evidence format.
        """

        evidence = []

        for item in results:

            evidence.append({
                "source": "LegalMind",
                "corpus": "contract",
                "retrieval_method": "BM25",
                "jurisdiction": None,
                "contract_id": item.get("contract_id"),
                "clause_id": item.get("clause_id"),
                "title": item.get("heading"),
                "text": item.get("text"),
                "score": float(item.get("score", 0.0))
            })

        return evidence

    @staticmethod
    def normalize_dense(results):
        """
        Convert dense retrieval results into common format.
        """

        evidence = []

        for item in results:

            evidence.append({
                "source": "LegalMind",
                "corpus": "contract",
                "retrieval_method": "Dense",
                "jurisdiction": None,
                "contract_id": item.get("contract_id"),
                "clause_id": item.get("clause_id"),
                "title": item.get("heading"),
                "text": item.get("text"),
                "score": float(item.get("score", 0.0))
            })

        return evidence

    @staticmethod
    def normalize_courtlistener(results):
        """
        Convert CourtListener results into common evidence format.
        """

        evidence = []

        for item in results:

            evidence.append({
                "source": "CourtListener",
                "corpus": "case_law",
                "retrieval_method": "CourtListener",
                "jurisdiction": item.get("jurisdiction"),
                "contract_id": None,
                "clause_id": None,
                "title": item.get("case_name"),
                "text": item.get("text") or item.get("snippet"),
                "score": 0.0,
                "date_filed": item.get("date_filed"),
                "citation": item.get("citation"),
                "source_id": item.get("source_id"),
                "url": item.get("absolute_url")
            })

        return evidence

    @staticmethod
    def deduplicate(evidence):
        """
        Remove duplicate evidence records.
        """

        seen = set()
        unique = []

        for item in evidence:

            key = (
                item.get("source"),
                item.get("source_id"),
                item.get("contract_id"),
                item.get("clause_id"),
                item.get("title"),
                item.get("text")
            )

            if key in seen:
                continue

            seen.add(key)
            unique.append(item)

        return unique

    @staticmethod
    def rank(evidence):
        """
        Rank normalized evidence by retrieval score.
        """

        return sorted(
            evidence,
            key=lambda x: x.get("score", 0.0),
            reverse=True
        )

    def process(
        self,
        bm25_results=None,
        dense_results=None,
        courtlistener_results=None
    ):
        """
        Complete evidence-processing pipeline.
        """

        evidence = []

        if bm25_results:
            evidence.extend(
                self.normalize_bm25(bm25_results)
            )

        if dense_results:
            evidence.extend(
                self.normalize_dense(dense_results)
            )

        if courtlistener_results:
            evidence.extend(
                self.normalize_courtlistener(
                    courtlistener_results
                )
            )

        evidence = self.deduplicate(evidence)

        return self.rank(evidence)
