
class LegalMindGraphService:
    """
    Service layer for querying the LegalMind Neo4j knowledge graph.

    This class provides a clean interface between the LegalMind
    application/agents and the Neo4j database module.
    """

    def __init__(self, db):
        self.db = db

    # --------------------------------------------------------
    # Document queries
    # --------------------------------------------------------

    def get_documents(self):
        """Return all documents/contracts."""
        return self.db.get_documents()

    # --------------------------------------------------------
    # Clause queries
    # --------------------------------------------------------

    def get_contract_clauses(self, contract_id):
        """Return all clauses belonging to a contract."""
        return self.db.get_contract_clauses(contract_id)

    # --------------------------------------------------------
    # Risk queries
    # --------------------------------------------------------

    def get_contract_risks(self, contract_id):
        """Return all risk findings for a contract."""
        return self.db.get_contract_risks(contract_id)

    def get_high_risk_clauses(self, contract_id):
        """Return high and critical risk findings."""
        return self.db.get_high_risk_clauses(contract_id)

    def get_risk_summary(self, contract_id):
        """Return risk counts for a contract."""
        return self.db.get_risk_summary(contract_id)

    # --------------------------------------------------------
    # Legal authority / multi-hop queries
    # --------------------------------------------------------

    def get_clause_legal_authorities(self, contract_id):
        """
        Traverse the legal-authority graph:

        Clause
            -> RELATED_TO_STATUTE
        Statute
            -> AMENDED_BY
        AmendingAct

        Returns all available authority chains for a contract.

        The method safely returns an empty list when the legal
        authority corpus has not yet been populated.
        """

        query = """
        MATCH (d:Document)-[:HAS_CLAUSE]->(c:Clause)
              -[:RELATED_TO_STATUTE]->(s:Statute)
        OPTIONAL MATCH (s)-[:AMENDED_BY]->(a:AmendingAct)

        WHERE d.contract_id = $contract_id

        RETURN
            d.contract_id AS contract_id,
            c.clause_id AS clause_id,
            c.heading AS clause_heading,
            s.statute_id AS statute_id,
            s.title AS statute_title,
            s.jurisdiction AS jurisdiction,
            a.act_id AS amending_act_id,
            a.title AS amending_act_title

        ORDER BY c.clause_id, s.statute_id
        """

        with self.db.driver.session() as session:
            return session.run(
                query,
                contract_id=contract_id
            ).data()

    # --------------------------------------------------------
    # Combined contract overview
    # --------------------------------------------------------

    def get_contract_overview(self, contract_id):
        """
        Return a complete overview of a contract:
        clauses, risks, high-risk clauses, risk summary,
        and available legal-authority connections.
        """

        return {
            "contract_id": contract_id,
            "clauses": self.get_contract_clauses(contract_id),
            "risks": self.get_contract_risks(contract_id),
            "high_risk_clauses": self.get_high_risk_clauses(contract_id),
            "risk_summary": self.get_risk_summary(contract_id),
            "legal_authorities": self.get_clause_legal_authorities(
                contract_id
            )
        }
