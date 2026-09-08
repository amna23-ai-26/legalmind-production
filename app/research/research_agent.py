
class ResearchAgent:
    """
    LegalMind Research Agent.

    Combines:
    - Neo4j graph traversal
    - Qdrant/BM25 hybrid retrieval
    - CourtListener case-law retrieval
    - Evidence ranking and deduplication
    """

    def __init__(
        self,
        graph_service,
        hybrid_retriever,
        courtlistener_client,
        evidence_ranker
    ):
        self.graph_service = graph_service
        self.hybrid_retriever = hybrid_retriever
        self.courtlistener_client = courtlistener_client
        self.evidence_ranker = evidence_ranker

    def process(
        self,
        contract_id,
        clause_id,
        query,
        top_k=5
    ):
        # --------------------------------------------------
        # 1. Get clause from Neo4j
        # --------------------------------------------------

        clauses = self.graph_service.get_contract_clauses(
            contract_id
        )

        clause = None

        for item in clauses:
            if item.get("clause_id") == clause_id:
                clause = item
                break

        if clause is None:
            raise ValueError(
                f"Clause {clause_id} not found "
                f"for contract {contract_id}"
            )

        # --------------------------------------------------
        # 2. Graph authority traversal
        # --------------------------------------------------

        graph_authorities = []

        if hasattr(
            self.graph_service,
            "get_clause_legal_authorities"
        ):
            graph_authorities = (
                self.graph_service
                .get_clause_legal_authorities(
                    contract_id
                )
            )

            # Keep only authorities belonging to
            # the requested clause.
            if isinstance(graph_authorities, list):
                filtered_authorities = []

                for group in graph_authorities:
                    if isinstance(group, list):
                        for authority in group:
                            if (
                                isinstance(authority, dict)
                                and authority.get("clause_id")
                                == clause_id
                            ):
                                filtered_authorities.append(
                                    authority
                                )

                    elif isinstance(group, dict):
                        if (
                            group.get("clause_id")
                            == clause_id
                        ):
                            filtered_authorities.append(
                                group
                            )

                graph_authorities = (
                    filtered_authorities
                )

        # --------------------------------------------------
        # 3. CourtListener case-law retrieval
        # --------------------------------------------------

        case_law = []

        if hasattr(
            self.courtlistener_client,
            "search_opinions"
        ):
            case_law = (
                self.courtlistener_client
                .search_opinions_with_content(
                    query,
                    limit=top_k
                )
            )

        # --------------------------------------------------
        # 4. Normalize case-law evidence
        # --------------------------------------------------

        normalized_case_law = []

        for item in case_law:

            if not isinstance(item, dict):
                continue

            normalized_case_law.append({
                "source": "CourtListener",
                "corpus": "case_law",
                "title": item.get(
                    "title",
                    item.get("case_name")
                ),
                "jurisdiction": item.get(
                    "jurisdiction"
                ),
                "date": item.get(
                    "date",
                    item.get("date_filed")
                ),
                "citation": item.get(
                    "citation",
                    []
                ),
                "url": item.get(
                    "url",
                    item.get("absolute_url")
                ),
                "text": item.get("text"),
                "opinion_id": item.get("opinion_id"),
                "cluster_id": item.get("cluster_id"),
                "relevance_score": item.get(
                    "relevance_score",
                    item.get("score", 0.0)
                )
            })

        # --------------------------------------------------
        # 5. Combine evidence
        # --------------------------------------------------

        evidence = list(
            normalized_case_law
        )

        # --------------------------------------------------
        # 6. Add graph authorities as evidence
        # --------------------------------------------------

        for authority_group in (
            graph_authorities
            if isinstance(graph_authorities, list)
            else []
        ):

            if isinstance(
                authority_group,
                list
            ):
                authorities = authority_group
            else:
                authorities = [
                    authority_group
                ]

            for authority in authorities:

                if not isinstance(
                    authority,
                    dict
                ):
                    continue

                evidence.append({
                    "source": "Neo4j",
                    "corpus": "prototype_statutes",
                    "statute_id": authority.get(
                        "statute_id"
                    ),
                    "title": authority.get(
                        "statute_title"
                    ),
                    "jurisdiction": authority.get(
                        "jurisdiction"
                    ),
                    "relevance_score": 0.0
                })

        # --------------------------------------------------
        # 7. Rank and deduplicate
        # --------------------------------------------------

        ranked = self.evidence_ranker.process(
            evidence=evidence,
            query=query,
            top_k=top_k
        )

        # --------------------------------------------------
        # 8. Return structured research result
        # --------------------------------------------------

        return {
            "contract_id": contract_id,
            "clause_id": clause_id,
            "clause": clause,
            "clause_heading": clause.get(
                "heading"
            ),
            "query": query,
            "evidence_count": len(ranked),
            "graph_authorities": graph_authorities,
            "ranked_case_law": [
                item
                for item in ranked
                if item.get("source")
                == "CourtListener"
            ],
            "evidence": ranked
        }
