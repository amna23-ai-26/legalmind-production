
import os
from typing import List, Dict, Optional

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct
)


class QdrantDatabase:
    """
    Qdrant vector database interface for LegalMind.

    Supports:
    - Local in-memory Qdrant for Colab/prototyping
    - Qdrant Cloud through QDRANT_URL and QDRANT_API_KEY
    """

    VECTOR_SIZE = 1024
    DEFAULT_COLLECTION = "legalmind_chunks"

    def __init__(
        self,
        url: Optional[str] = None,
        api_key: Optional[str] = None,
        collection_name: str = DEFAULT_COLLECTION
    ):
        self.url = url or os.getenv("QDRANT_URL")
        self.api_key = api_key or os.getenv("QDRANT_API_KEY")
        self.collection_name = collection_name

        # Use Qdrant Cloud when credentials are configured.
        if self.url:
            self.client = QdrantClient(
                url=self.url,
                api_key=self.api_key
            )
            self.mode = "cloud"

        # Otherwise use an in-memory Qdrant instance.
        else:
            self.client = QdrantClient(":memory:")
            self.mode = "memory"

        self._ensure_collection()

    def _ensure_collection(self):
        """
        Create the collection if it does not already exist.
        """

        collections = self.client.get_collections()

        existing = {
            collection.name
            for collection in collections.collections
        }

        if self.collection_name not in existing:
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=self.VECTOR_SIZE,
                    distance=Distance.COSINE
                )
            )

    def upsert_chunks(
        self,
        chunks: List[Dict],
        embeddings
    ):
        """
        Store hierarchical contract chunks and their embeddings.
        """

        if len(chunks) != len(embeddings):
            raise ValueError(
                "Number of chunks must match number of embeddings."
            )

        points = []

        for index, (chunk, embedding) in enumerate(
            zip(chunks, embeddings)
        ):

            chunk_id = chunk.get(
                "chunk_id",
                index + 1
            )

            # Qdrant point IDs must be positive integers
            # or UUIDs. Convert numeric IDs safely.
            point_id = int(chunk_id)

            payload = {
                "chunk_id": chunk.get("chunk_id"),
                "clause_id": chunk.get("clause_id"),
                "contract_id": chunk.get("contract_id"),
                "heading": chunk.get("heading"),
                "text": chunk.get("text"),
                "word_count": chunk.get("word_count")
            }

            points.append(
                PointStruct(
                    id=point_id,
                    vector=embedding.tolist(),
                    payload=payload
                )
            )

        self.client.upsert(
            collection_name=self.collection_name,
            points=points
        )

        return len(points)

    def search(
        self,
        query_vector,
        limit=5
    ):
        """
        Search the vector collection using a query embedding.
        """

        results = self.client.query_points(
            collection_name=self.collection_name,
            query=query_vector.tolist()
            if hasattr(query_vector, "tolist")
            else query_vector,
            limit=limit,
            with_payload=True
        )

        output = []

        for result in results.points:
            item = dict(
                result.payload or {}
            )

            item["score"] = float(
                result.score
            )

            output.append(item)

        return output

    def count(self):
        """
        Return the number of stored vectors.
        """

        result = self.client.count(
            collection_name=self.collection_name,
            exact=True
        )

        return result.count

    def collection_exists(self):
        """
        Check whether the configured collection exists.
        """

        collections = self.client.get_collections()

        return any(
            collection.name == self.collection_name
            for collection in collections.collections
        )
