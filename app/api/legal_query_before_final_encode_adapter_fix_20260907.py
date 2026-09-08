from pathlib import Path
from functools import lru_cache

from fastapi import APIRouter
from pydantic import BaseModel
from qdrant_client import QdrantClient

from app.embeddings.embedder import BGEEmbedder
from app.retrieval.hybrid_retriever import HybridRetriever


router = APIRouter(prefix="/api/legal-query", tags=["Legal Knowledge"])

ROOT = Path("/content/drive/MyDrive/legalmind")
PROCESSED = ROOT / "data/phase4_pakistan/processed"
QDRANT_PATH = ROOT / "data/qdrant_storage"

CORPORA = [
    (
        "contract_act_1872",
        "Contract Act, 1872",
        PROCESSED / "chunks/contract_act_1872_chunks.json",
        PROCESSED / "embeddings/contract_act_1872_embeddings.npy",
        "legalmind_pakistan_contract_act_1872",
    ),
    (
        "companies_act_2017",
        "Companies Act, 2017",
        PROCESSED / "chunks/companies_act_2017_chunks.json",
        PROCESSED / "embeddings/companies_act_2017_embeddings.npy",
        "legalmind_pakistan_companies_act_2017",
    ),
    (
        "companies_regulations_2024",
        "Companies Regulations, 2024",
        PROCESSED / "chunks/companies_regulations_2024_chunks.json",
        PROCESSED / "embeddings/companies_regulations_2024_embeddings.npy",
        "legalmind_pakistan_companies_regulations_2024",
    ),
]


class LegalQueryRequest(BaseModel):
    query: str
    language: str = "en"


@lru_cache(maxsize=1)
@lru_cache(maxsize=1)
def build_retrievers():
    client = QdrantClient(path=str(QDRANT_PATH))
    base_embedder = BGEEmbedder()

    class QueryEmbedder:
        def encode(self, texts, normalize_embeddings=True, **kwargs):
            if isinstance(texts, str):
                texts = [texts]
            return base_embedder.embed_texts(texts)

    embedder = QueryEmbedder()

    retrievers = []

    for corpus_name, title, chunks, embeddings, collection in CORPORA:
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

    for corpus_name, title, retriever in build_retrievers():
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

    evidence.sort(
        key=lambda item: item.get("retrieval_score") or 0.0,
        reverse=True,
    )

    return {
        "status": "COMPLETED",
        "query": query,
        "language": request.language,
        "answer": "LegalMind retrieved the most relevant Pakistani statutory provisions below. This result is evidence-grounded retrieval, not legal advice.",
        "evidence": evidence[:10],
        "evidence_count": len(evidence[:10]),
        "case_law": {
            "status": "NOT_CONFIGURED",
            "message": "Pakistani case-law provider is not configured.",
        },
        "disclaimer": "LegalMind provides AI-assisted legal information and does not provide legal advice.",
    }
