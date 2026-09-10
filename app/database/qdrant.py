import os
from typing import Optional, List, Dict

try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import (
        VectorParams,
        Distance,
        PointStruct
    )
except ImportError:
    QdrantClient = None
    VectorParams = None
    Distance = None
    PointStruct = None


class QdrantDatabase:
    """
    LegalMind Qdrant vector database interface.
    """

    VECTOR_SIZE = 1024
    DEFAULT_COLLECTION = "legalmind_chunks"
    DEFAULT_PATH = "/content/drive/MyDrive/legalmind/data/qdrant_storage"

    def __init__(
        self,
        url: Optional[str] = None,
        api_key: Optional[str] = None,
        collection_name: str = DEFAULT_COLLECTION,
        path: Optional[str] = None
    ):
        if QdrantClient is None:
            raise ValueError("qdrant-client package is not installed.")

        self.url = url or os.getenv("QDRANT_URL")
        self.api_key = api_key or os.getenv("QDRANT_API_KEY")
        self.collection_name = collection_name

        if self.url:
            self.client = QdrantClient(
                url=self.url,
                api_key=self.api_key
            )
            self.mode = "cloud"
        else:
            self.path = path or self.DEFAULT_PATH
            os.makedirs(self.path, exist_ok=True)
            self.client = QdrantClient(path=self.path)
            self.mode = "persistent_local"

        self._ensure_collection()

    def _ensure_collection(self):
        collections = self.client.get_collections()
        existing = {c.name for c in collections.collections}

        if self.collection_name not in existing:
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=self.VECTOR_SIZE,
                    distance=Distance.COSINE
                )
            )

    def upsert_chunks(self, chunks: List[Dict], embeddings):
        if len(chunks) != len(embeddings):
            raise ValueError("Number of chunks must match number of embeddings.")

        points = []
        for index, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            chunk_id = chunk.get("chunk_id", index + 1)
            point_id = int(chunk_id)

            payload = {
                "chunk_id": chunk.get("chunk_id"),
                "clause_id": chunk.get("clause_id"),
                "contract_id": chunk.get("contract_id"),
                "heading": chunk.get("heading"),
                "text": chunk.get("text"),
                "word_count": chunk.get("word_count")
            }

            vector = (
                embedding.tolist()
                if hasattr(embedding, "tolist")
                else list(embedding)
            )

            points.append(
                PointStruct(
                    id=point_id,
                    vector=vector,
                    payload=payload
                )
            )

        self.client.upsert(
            collection_name=self.collection_name,
            points=points,
            wait=True
        )

        return len(points)

    def search(self, query_vector, limit=5):
        vector = (
            query_vector.tolist()
            if hasattr(query_vector, "tolist")
            else query_vector
        )

        results = self.client.query_points(
            collection_name=self.collection_name,
            query=vector,
            limit=limit,
            with_payload=True
        )

        output = []
        for result in results.points:
            item = dict(result.payload or {})
            item["score"] = float(result.score)
            item["point_id"] = result.id
            output.append(item)

        return output

    def count(self):
        result = self.client.count(
            collection_name=self.collection_name,
            exact=True
        )
        return result.count

    def collection_exists(self):
        collections = self.client.get_collections()
        return any(c.name == self.collection_name for c in collections.collections)
