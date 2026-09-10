
import json
from pathlib import Path

import numpy as np
from rank_bm25 import BM25Okapi

try:
    from qdrant_client import QdrantClient
except ImportError:
    QdrantClient = None


class HybridRetriever:
    """
    LegalMind hybrid retriever.

    Combines:
    - BM25 lexical retrieval
    - Qdrant dense vector retrieval
    - Reciprocal Rank Fusion (RRF)
    """

    def __init__(
        self,
        chunks_path,
        embeddings_path,
        qdrant_client,
        collection_name,
        embedding_model,
    ):
        self.chunks_path = Path(chunks_path)
        self.embeddings_path = Path(embeddings_path)
        self.qdrant = qdrant_client
        self.collection_name = collection_name
        self.embedding_model = embedding_model

        # Load existing Phase 1 chunks.
        with open(self.chunks_path, "r", encoding="utf-8") as f:
            self.chunks = json.load(f)

        # Load existing Phase 1 embeddings.
        self.embeddings = np.load(self.embeddings_path)

        if len(self.chunks) != len(self.embeddings):
            raise ValueError(
                "Chunk/embedding count mismatch: "
                f"{len(self.chunks)} chunks vs "
                f"{len(self.embeddings)} embeddings."
            )

        # Build BM25 over the same corpus.
        tokenized_chunks = [
            chunk["text"].lower().split()
            for chunk in self.chunks
        ]

        self.bm25 = BM25Okapi(tokenized_chunks)

        # Map Qdrant point IDs back to chunk indexes.
        self.point_to_chunk = {
            idx + 1: idx
            for idx in range(len(self.chunks))
        }

    def _bm25_search(self, query, limit):
        """Return BM25-ranked chunk indexes."""

        scores = self.bm25.get_scores(
            query.lower().split()
        )

        ranked_indices = np.argsort(scores)[::-1][:limit]

        return [
            (int(idx), float(scores[idx]))
            for idx in ranked_indices
        ]

    def _dense_search(self, query, limit):
        """Return Qdrant dense-ranked chunk indexes."""

        query_vector = self.embedding_model.encode(
            query,
            normalize_embeddings=True
        ).tolist()

        results = self.qdrant.query_points(
            collection_name=self.collection_name,
            query=query_vector,
            limit=limit,
            with_payload=True,
        ).points

        dense_results = []

        for result in results:
            chunk_id = result.payload.get("chunk_id")

            # Locate the corresponding chunk.
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

    @staticmethod
    def _rrf(ranked_lists, k=60):
        """
        Reciprocal Rank Fusion.

        score = sum(1 / (k + rank))
        """

        fusion_scores = {}

        for ranked_list in ranked_lists:

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
        Perform hybrid BM25 + dense retrieval.

        Returns top_k fused results.
        """

        bm25_results = self._bm25_search(
            query,
            retrieval_k
        )

        dense_results = self._dense_search(
            query,
            retrieval_k
        )

        fused = self._rrf(
            [
                bm25_results,
                dense_results,
            ]
        )

        results = []

        for chunk_index, fusion_score in fused[:top_k]:

            chunk = self.chunks[chunk_index]

            results.append(
                {
                    "chunk_id": chunk["chunk_id"],
                    "contract_id": chunk["contract_id"],
                    "clause_id": chunk["clause_id"],
                    "heading": chunk["heading"],
                    "filename": chunk.get("filename"),
                    "text": chunk["text"],
                    "hybrid_score": fusion_score,
                }
            )

        return results
