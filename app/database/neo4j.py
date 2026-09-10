
import os
try:
    from neo4j import GraphDatabase
except ImportError:
    GraphDatabase = None


class Neo4jDatabase:
    """
    LegalMind Neo4j database interface.

    Provides reusable access to the LegalMind
    knowledge graph.
    """

    def __init__(
        self,
        uri=None,
        username=None,
        password=None
       ):
        if GraphDatabase is None:
            raise ValueError(
                "neo4j package is not installed."
            )

        self.uri = uri or os.getenv(
            "NEO4J_URI",
            "bolt://127.0.0.1:7687"
        )

        self.username = username or os.getenv(
            "NEO4J_USER",
            "neo4j"
        )

        self.password = password or os.getenv(
            "NEO4J_PASSWORD"
        )

        if not self.password:
            raise ValueError(
                "NEO4J_PASSWORD is not configured."
            )

        self.driver = GraphDatabase.driver(
            self.uri,
            auth=(
                self.username,
                self.password
            )
        )

    def verify_connection(self):
        """
        Verify that Neo4j is reachable
        and authentication succeeds.
        """

        self.driver.verify_connectivity()
        return True

    def get_documents(self):
        """
        Return all documents in the knowledge graph.
        """

        query = """
        MATCH (d:Document)
        RETURN
            d.contract_id AS contract_id,
            d.document_name AS document
        ORDER BY d.contract_id
        """

        with self.driver.session() as session:
            return session.run(query).data()

    def get_contract_clauses(self, contract_id):
        """
        Return all clauses belonging to a contract.
        """

        query = """
        MATCH (d:Document)-[:HAS_CLAUSE]->(c:Clause)
        WHERE d.contract_id = $contract_id

        RETURN
            c.clause_id AS clause_id,
            c.heading AS heading
        ORDER BY c.clause_id
        """

        with self.driver.session() as session:
            return session.run(
                query,
                contract_id=contract_id
            ).data()

    def get_contract_risks(self, contract_id):
        """
        Return all risk findings associated
        with a contract.
        """

        query = """
        MATCH (d:Document)-[:HAS_CLAUSE]->(c:Clause)
              -[r:HAS_RISK]->(risk:RiskCategory)

        WHERE d.contract_id = $contract_id

        RETURN
            c.clause_id AS clause_id,
            c.heading AS heading,
            risk.name AS risk_category,
            r.risk_score AS risk_score,
            r.risk_level AS risk_level,
            r.matched_keywords AS matched_keywords,
            r.finding AS finding

        ORDER BY c.clause_id
        """

        with self.driver.session() as session:
            return session.run(
                query,
                contract_id=contract_id
            ).data()

    def get_high_risk_clauses(self, contract_id=None):
        """
        Return high-risk clauses.

        If contract_id is provided, restrict
        results to that contract.
        """

        if contract_id is None:

            query = """
            MATCH (d:Document)-[:HAS_CLAUSE]->(c:Clause)
                  -[r:HAS_RISK]->(risk:RiskCategory)

            WHERE r.risk_level = 'High'

            RETURN
                d.contract_id AS contract_id,
                d.document_name AS document,
                c.clause_id AS clause_id,
                c.heading AS heading,
                risk.name AS risk_category,
                r.risk_score AS risk_score

            ORDER BY d.contract_id, c.clause_id
            """

            params = {}

        else:

            query = """
            MATCH (d:Document)-[:HAS_CLAUSE]->(c:Clause)
                  -[r:HAS_RISK]->(risk:RiskCategory)

            WHERE
                d.contract_id = $contract_id
                AND r.risk_level = 'High'

            RETURN
                d.contract_id AS contract_id,
                d.document_name AS document,
                c.clause_id AS clause_id,
                c.heading AS heading,
                risk.name AS risk_category,
                r.risk_score AS risk_score

            ORDER BY c.clause_id
            """

            params = {
                "contract_id": contract_id
            }

        with self.driver.session() as session:
            return session.run(
                query,
                **params
            ).data()

    def get_risk_summary(self, contract_id):
        """
        Return a risk-level summary for one contract.
        """

        query = """
        MATCH (d:Document)-[:HAS_CLAUSE]->(c:Clause)
              -[r:HAS_RISK]->(risk:RiskCategory)

        WHERE d.contract_id = $contract_id

        RETURN
            count(r) AS total_risks,

            count(
                CASE
                    WHEN r.risk_level = 'Critical'
                    THEN 1
                END
            ) AS critical,

            count(
                CASE
                    WHEN r.risk_level = 'High'
                    THEN 1
                END
            ) AS high,

            count(
                CASE
                    WHEN r.risk_level = 'Moderate'
                    THEN 1
                END
            ) AS moderate
        """

        with self.driver.session() as session:
            return session.run(
                query,
                contract_id=contract_id
            ).single()

    def close(self):
        """
        Close the Neo4j driver.
        """

        self.driver.close()
