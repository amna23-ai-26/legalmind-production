from typing import Any, Dict, List, Optional


class ResearchIntegrationAdapter:
    def __init__(
        self,
        hybrid_retriever,
        evidence_ranker,
        courtlistener_client=None,
        graph_service=None,
        corpus="prototype_statutes",
        jurisdiction="Pakistan",
    ):
        self.hybrid_retriever = hybrid_retriever
        self.evidence_ranker = evidence_ranker
        self.courtlistener_client = courtlistener_client
        self.graph_service = graph_service
        self.corpus = corpus
        self.jurisdiction = jurisdiction

    def _chunk_evidence(self, index, score, retrieval_method):
        chunk = self.hybrid_retriever.chunks[index]

        return {
            "chunk_id": chunk.get("chunk_id"),
            "contract_id": chunk.get("contract_id"),
            "clause_id": chunk.get("clause_id"),
            "title": chunk.get("heading"),
            "heading": chunk.get("heading"),
            "filename": chunk.get("filename"),
            "text": chunk.get("text"),
            "score": float(score),
            "relevance_score": float(score),
            "retrieval_method": retrieval_method,
            "jurisdiction": self.jurisdiction,
            "corpus": self.corpus,
        }

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        retrieval_k: int = 10,
        courtlistener_results: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:

        bm25_raw = self.hybrid_retriever._bm25_search(
            query,
            retrieval_k,
        )

        dense_raw = self.hybrid_retriever._dense_search(
            query,
            retrieval_k,
        )

        bm25_results = [
            self._chunk_evidence(index, score, "BM25")
            for index, score in bm25_raw
        ]

        dense_results = [
            self._chunk_evidence(index, score, "Dense")
            for index, score in dense_raw
        ]

        ranked = self.evidence_ranker.process(
            bm25_results=bm25_results,
            dense_results=dense_results,
            courtlistener_results=courtlistener_results or [],
        )

        return {
            "query": query,
            "corpus": self.corpus,
            "jurisdiction": self.jurisdiction,
            "evidence_count": len(ranked),
            "evidence": ranked[:top_k],
            "bm25_count": len(bm25_results),
            "dense_count": len(dense_results),
            "courtlistener_count": len(courtlistener_results or []),
        }
