import json
from pathlib import Path

import numpy as np
from rank_bm25 import BM25Okapi


class HybridRetriever:
    """
    LegalMind hybrid retriever.

    Combines:
    - BM25 lexical retrieval
    - Qdrant dense vector retrieval (optional)
    - Reciprocal Rank Fusion (RRF)
    """

    def __init__(
        self,
        chunks_path,
        embeddings_path=None,
        qdrant_client=None,
        collection_name=None,
        embedding_model=None,
    ):
        self.chunks_path = Path(chunks_path)
        self.qdrant = qdrant_client
        self.collection_name = collection_name
        self.embedding_model = embedding_model

        # Load existing Phase 1 chunks.
        with open(self.chunks_path, "r", encoding="utf-8") as f:
            self.chunks = json.load(f)

        # Load embeddings if available
        self.embeddings = None
        if embeddings_path and Path(embeddings_path).exists():
            try:
                self.embeddings = np.load(embeddings_path)
            except Exception:
                self.embeddings = None

        # Build BM25 over the corpus.
        tokenized_chunks = [
            chunk["text"].lower().split()
            for chunk in self.chunks
        ]

        self.bm25 = BM25Okapi(tokenized_chunks)

    def _bm25_search(self, query, limit):
        """Return BM25-ranked chunk indexes."""
        tokens = (query or "").lower().split()
        if not tokens:
            return [(i, 0.0) for i in range(min(limit, len(self.chunks)))]

        scores = self.bm25.get_scores(tokens)
        ranked_indices = np.argsort(scores)[::-1][:limit]

        return [
            (int(idx), float(scores[idx]))
            for idx in ranked_indices
        ]

    def _dense_search(self, query, limit):
        """Return Qdrant dense-ranked chunk indexes."""
        if not self.qdrant or not self.embedding_model:
            return []

        try:
            query_vector = self.embedding_model.encode(
                query,
                normalize_embeddings=True
            )
            if query_vector is None or len(query_vector) == 0:
                return []

            if hasattr(query_vector, "tolist"):
                query_vector = query_vector.tolist()
            elif not isinstance(query_vector, list):
                query_vector = list(query_vector)

            results = self.qdrant.query_points(
                collection_name=self.collection_name,
                query=query_vector,
                limit=limit,
                with_payload=True,
            ).points

            dense_results = []
            for result in results:
                chunk_id = result.payload.get("chunk_id")
                chunk_index = next(
                    (
                        i
                        for i, chunk in enumerate(self.chunks)
                        if chunk["chunk_id"] == chunk_id
                    ),
                    None,
                )

                if chunk_index is not None:
                    dense_results.append(
                        (chunk_index, float(result.score))
                    )

            return dense_results
        except Exception:
            return []

    @staticmethod
    def _rrf(ranked_lists, k=60):
        """
        Reciprocal Rank Fusion.
        score = sum(1 / (k + rank))
        """
        fusion_scores = {}

        for ranked_list in ranked_lists:
            if not ranked_list:
                continue

            for rank, (chunk_index, _) in enumerate(
                ranked_list,
                start=1
            ):
                fusion_scores[chunk_index] = (
                    fusion_scores.get(chunk_index, 0.0)
                    + 1.0 / (k + rank)
                )

        return sorted(
            fusion_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )

    def search(
        self,
        query,
        top_k=5,
        retrieval_k=10,
    ):
        """
        Perform BM25 + dense retrieval.
        Returns top_k fused results.
        """
        bm25_results = self._bm25_search(query, retrieval_k)
        dense_results = self._dense_search(query, retrieval_k)

        fused = self._rrf([bm25_results, dense_results])

        results = []
        for chunk_index, fusion_score in fused[:top_k]:
            if chunk_index < len(self.chunks):
                chunk = self.chunks[chunk_index]
                results.append(
                    {
                        "chunk_id": chunk.get("chunk_id"),
                        "contract_id": chunk.get("contract_id"),
                        "clause_id": chunk.get("clause_id"),
                        "heading": chunk.get("heading", ""),
                        "filename": chunk.get("filename", ""),
                        "text": chunk.get("text", ""),
                        "hybrid_score": fusion_score,
                    }
                )

        return results
