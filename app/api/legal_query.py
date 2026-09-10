from pathlib import Path
from functools import lru_cache
import logging

from fastapi import APIRouter
from pydantic import BaseModel

try:
    from qdrant_client import QdrantClient
except ImportError:
    QdrantClient = None

from app.config import get_data_dir
from app.retrieval.hybrid_retriever import HybridRetriever

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/legal-query", tags=["Legal Knowledge"])


class LegalQueryRequest(BaseModel):
    query: str
    language: str = "en"


def _get_corpora():
    data_dir = get_data_dir()
    processed = data_dir / "phase4_pakistan" / "processed"

    if not processed.exists():
        # Fallback to direct processed directory if present
        if (data_dir / "processed").exists():
            processed = data_dir / "processed"

    chunks_dir = processed / "chunks"
    embeddings_dir = processed / "embeddings"

    return [
        (
            "contract_act_1872",
            "Contract Act, 1872",
            chunks_dir / "contract_act_1872_chunks.json",
            embeddings_dir / "contract_act_1872_embeddings.npy",
            "legalmind_pakistan_contract_act_1872",
        ),
        (
            "companies_act_2017",
            "Companies Act, 2017",
            chunks_dir / "companies_act_2017_chunks.json",
            embeddings_dir / "companies_act_2017_embeddings.npy",
            "legalmind_pakistan_companies_act_2017",
        ),
        (
            "companies_regulations_2024",
            "Companies Regulations, 2024",
            chunks_dir / "companies_regulations_2024_chunks.json",
            embeddings_dir / "companies_regulations_2024_embeddings.npy",
            "legalmind_pakistan_companies_regulations_2024",
        ),
    ]


@lru_cache(maxsize=1)
def build_retrievers():
    data_dir = get_data_dir()
    client = None

    if QdrantClient is not None:
        try:
            qdrant_path = data_dir / "qdrant_storage"
            qdrant_path.mkdir(parents=True, exist_ok=True)
            client = QdrantClient(path=str(qdrant_path))
        except Exception as exc:
            logger.warning(f"Local Qdrant client initialization note: {exc}")
            client = None

    class SafeEmbedder:
        def __init__(self):
            self._real_embedder = None
            self._failed = False

        def _get_embedder(self):
            if self._real_embedder is None and not self._failed:
                try:
                    from app.embeddings.embedder import BGEEmbedder
                    self._real_embedder = BGEEmbedder()
                except Exception as exc:
                    logger.warning(f"BGEEmbedder not loaded ({exc}). Using BM25 fallback.")
                    self._failed = True
            return self._real_embedder

        def encode(self, texts, normalize_embeddings=True, **kwargs):
            embedder = self._get_embedder()
            if embedder is None:
                return [0.0] * 1024

            single = isinstance(texts, str)
            if single:
                texts = [texts]
            embeddings = embedder.embed_texts(texts)
            if normalize_embeddings:
                import numpy as np
                norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
                norms[norms == 0] = 1.0
                embeddings = embeddings / norms
            return embeddings[0] if single else embeddings

    embedder = SafeEmbedder()
    retrievers = []

    for corpus_name, title, chunks, embeddings, collection in _get_corpora():
        if chunks.exists() and embeddings.exists():
            try:
                retrievers.append(
                    (
                        corpus_name,
                        title,
                        HybridRetriever(
                            chunks_path=chunks,
                            embeddings_path=embeddings,
                            qdrant_client=client,
                            collection_name=collection,
                            embedding_model=embedder,
                        ),
                    )
                )
            except Exception as exc:
                logger.error(f"Failed to initialize retriever for {corpus_name}: {exc}")

    return retrievers


@router.post("")
def legal_query(request: LegalQueryRequest):
    query = request.query.strip()

    if not query:
        return {
            "status": "ERROR",
            "message": "Legal query is required.",
        }

    evidence = []
    active_retrievers = build_retrievers()

    for corpus_name, title, retriever in active_retrievers:
        try:
            results = retriever.search(
                query=query,
                top_k=5,
                retrieval_k=10,
            )

            for item in results:
                evidence.append(
                    {
                        "source": "PakistanStatute",
                        "corpus": corpus_name,
                        "title": title,
                        "jurisdiction": "Pakistan",
                        "section_id": item.get("clause_id"),
                        "heading": item.get("heading"),
                        "text": item.get("text", ""),
                        "retrieval_score": item.get("hybrid_score"),
                        "source_id": item.get("chunk_id"),
                    }
                )
        except Exception as exc:
            logger.warning(f"Error searching {corpus_name}: {exc}")

    evidence.sort(
        key=lambda item: item.get("retrieval_score") or 0.0,
        reverse=True,
    )

    top_evidence = evidence[:10]

    answer_text = (
        "LegalMind retrieved the most relevant Pakistani statutory provisions below based on your query. "
        "Review the statutory sections for authoritative legal context."
        if top_evidence
        else "No direct statutory matches found for your query. Try searching with specific commercial or statutory keywords."
    )

    return {
        "status": "COMPLETED",
        "query": query,
        "language": request.language,
        "answer": answer_text,
        "evidence": top_evidence,
        "evidence_count": len(top_evidence),
        "case_law": {
            "status": "NOT_CONFIGURED",
            "message": "Pakistani case-law provider is not configured.",
        },
        "disclaimer": "LegalMind provides AI-assisted legal intelligence and research support. It does not provide legal advice.",
    }
