from pathlib import Path
from functools import lru_cache
import logging

from fastapi import APIRouter
from pydantic import BaseModel

from app.config import get_data_dir
from app.retrieval.hybrid_retriever import HybridRetriever

logger = logging.getLogger(__name__)

# Line 11: Set prefix to /legal-query to match frontend POST /api/legal-query
router = APIRouter(prefix="/legal-query", tags=["Legal Knowledge"])


class LegalQueryRequest(BaseModel):
    query: str
    language: str = "en"


def _get_corpora():
    data_dir = get_data_dir()
    processed = data_dir / "phase4_pakistan" / "processed"

    if not processed.exists():
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
    retrievers = []

    for corpus_name, title, chunks, embeddings, collection in _get_corpora():
        if chunks.exists():
            try:
                retrievers.append(
                    (
                        corpus_name,
                        title,
                        HybridRetriever(
                            chunks_path=chunks,
                            embeddings_path=embeddings if embeddings.exists() else None,
                            qdrant_client=None,
                            collection_name=collection,
                            embedding_model=None,
                        ),
                    )
                )
            except Exception as exc:
                logger.error(f"Failed to initialize retriever for {corpus_name}: {exc}")

    return retrievers


@router.post("")
def legal_query(request: LegalQueryRequest):
    query = (request.query or "").strip()

    if not query:
        return {
            "status": "ERROR",
            "message": "Legal query is required.",
        }

    evidence = []
    try:
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
    except Exception as exc:
        logger.error(f"Error building retrievers: {exc}")

    evidence.sort(
        key=lambda item: item.get("retrieval_score") or 0.0,
        reverse=True,
    )

    top_evidence = evidence[:10]

    if not top_evidence:
        # Previously this silently swapped in a hardcoded Contract Act
        # Section 73 snippet for *every* query that found no evidence,
        # which is why every question produced the exact same answer.
        # That almost always meant no corpus was loaded at all (the
        # data/phase4_pakistan/processed directory is gitignored and not
        # shipped with the app), not that Section 73 was actually
        # relevant to the question. Say so honestly instead of
        # fabricating a match.
        active_retrievers = build_retrievers()
        if not active_retrievers:
            logger.warning(
                "No legal corpora are loaded (checked contract_act_1872, "
                "companies_act_2017, companies_regulations_2024 under "
                "%s). /api/legal-query cannot answer any query until "
                "processed chunk/embedding files are present.",
                get_data_dir() / "phase4_pakistan" / "processed",
            )
            answer_text = (
                "LegalMind could not answer this question because no Pakistani "
                "statutory corpus is currently loaded on the server. "
                "This is a server configuration issue, not a problem with your question — "
                "please contact an administrator to load the legal corpus data."
            )
        else:
            answer_text = (
                f'LegalMind searched the loaded Pakistani statutes for "{query}" '
                "and found no matching provisions. Try rephrasing your question, "
                "or note that it may fall outside the currently supported corpora "
                "(Contract Act 1872, Companies Act 2017, Companies Regulations 2024)."
            )

        return {
            "status": "COMPLETED",
            "query": query,
            "language": request.language,
            "answer": answer_text,
            "evidence": [],
            "evidence_count": 0,
            "case_law": {
                "status": "NOT_CONFIGURED",
                "message": "Pakistani case-law provider is not configured.",
            },
            "disclaimer": "LegalMind provides AI-assisted legal intelligence and research support. It does not provide legal advice.",
        }

    top_match = top_evidence[0]
    section_ref = f" Section {top_match['section_id']}" if top_match.get("section_id") else ""
    answer_text = (
        f'LegalMind found {len(top_evidence)} statutory provision(s) relevant to "{query}". '
        f"The closest match is {top_match['title']}{section_ref} "
        f'("{top_match["heading"]}"). Review the statutory sections below for full context.'
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
