from pathlib import Path
import json


class PakistanEvidenceAdapter:
    def __init__(self, hybrid_retriever, corpus_name, title):
        self.hybrid_retriever = hybrid_retriever
        self.corpus_name = corpus_name
        self.title = title

    def retrieve(self, query, top_k=5, retrieval_k=10):
        results = self.hybrid_retriever.search(
            query=query,
            top_k=top_k,
            retrieval_k=retrieval_k
        )

        evidence = []

        for rank, item in enumerate(results, 1):
            metadata = item.get("metadata") or item

            section_id = (
                metadata.get("section_id")
                or metadata.get("clause_id")
                or metadata.get("section")
                or metadata.get("clause")
                or metadata.get("id")
            )

            heading = (
                metadata.get("heading")
                or metadata.get("section_heading")
                or metadata.get("clause_heading")
                or item.get("heading")
            )

            evidence.append({
                "source": "PakistanStatute",
                "corpus": "pakistan_statutes",
                "statute_id": self.corpus_name,
                "title": self.title,
                "jurisdiction": "Pakistan",
                "section_id": section_id,
                "heading": heading,
                "text": item.get("text", ""),
                "retrieval_rank": rank,
                "retrieval_score": item.get("hybrid_score"),
                "source_id": (
                    metadata.get("chunk_id")
                    or item.get("chunk_id")
                    or section_id
                )
            })

        return evidence

    def build_research_result(
        self,
        contract_id,
        clause_id,
        clause,
        query,
        top_k=5,
        retrieval_k=10
    ):
        evidence = self.retrieve(
            query=query,
            top_k=top_k,
            retrieval_k=retrieval_k
        )

        return {
            "contract_id": contract_id,
            "clause_id": clause_id,
            "clause": clause,
            "clause_heading": clause.get("heading") if isinstance(clause, dict) else None,
            "query": query,
            "evidence_count": len(evidence),
            "graph_authorities": evidence,
            "ranked_case_law": [],
            "evidence": evidence
        }
