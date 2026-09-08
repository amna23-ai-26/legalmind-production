
import json
from pathlib import Path

from app.database.neo4j import Neo4jDatabase


class LegalMindGraphPopulator:
    """
    Populates the Neo4j knowledge graph from validated
    LegalMind Phase 1 checkpoint outputs.
    """

    def __init__(self, db=None):
        self.db = db or Neo4jDatabase()

        self.base_path = (
            Path("/content/drive/MyDrive/legalmind")
            / "data"
            / "processed"
            / "phase1_checkpoint"
        )

        self.clauses_file = (
            self.base_path / "segmented_clauses_5_contracts.json"
        )

        self.metadata_file = (
            self.base_path / "metadata_5_contracts.json"
        )

        self.risks_file = (
            self.base_path / "risk_analysis_5_contracts.json"
        )

        self.classification_file = (
            Path("/content/drive/MyDrive/legalmind")
            / "data"
            / "processed"
            / "cuad_classification_baseline.json"
        )

    @staticmethod
    def _load_json(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def populate_documents(self):
        """
        Create/merge Document nodes using Phase 1 metadata.
        """

        metadata = self._load_json(self.metadata_file)

        query = """
        UNWIND $documents AS doc

        MERGE (d:Document {
            contract_id: doc.contract_id
        })

        SET
            d.document_name = doc.document_name,
            d.file_name = doc.file_name,
            d.agreement_date = doc.agreement_date,
            d.effective_date = doc.effective_date,
            d.contract_type = doc.contract_type,
            d.governing_law = doc.governing_law,
            d.parties = doc.parties
        """

        documents = []

        for item in metadata:
            meta = item.get("metadata", {})

            documents.append({
                "contract_id": item["contract_id"],
                "document_name": meta.get(
                    "document_name",
                    item.get("filename", f"Contract_{item['contract_id']}")
                ),
                "file_name": item.get(
                    "filename",
                    item.get("file_name")
                ),
                "agreement_date": meta.get("agreement_date"),
                "effective_date": meta.get("effective_date"),
                "contract_type": meta.get("contract_type"),
                "governing_law": meta.get("governing_law"),
                "parties": meta.get("parties", [])
            })

        with self.db.driver.session() as session:
            session.run(query, documents=documents).consume()

        return len(documents)

    def populate_clauses(self):
        """
        Create/merge Clause nodes and HAS_CLAUSE relationships.
        """

        segmented = self._load_json(self.clauses_file)

        query = """
        UNWIND $clauses AS item

        MATCH (d:Document {
            contract_id: item.contract_id
        })

        MERGE (c:Clause {
            contract_id: item.contract_id,
            clause_id: item.clause_id
        })

        SET
            c.heading = item.heading,
            c.text = item.text,
            c.character_count = item.character_count,
            c.word_count = item.word_count

        MERGE (d)-[:HAS_CLAUSE]->(c)
        """

        rows = []

        for contract in segmented:
            contract_id = contract["contract_id"]

            for clause in contract.get("clauses", []):
                rows.append({
                    "contract_id": contract_id,
                    "clause_id": clause["clause_id"],
                    "heading": clause.get("heading"),
                    "text": clause.get("text"),
                    "character_count": clause.get(
                        "character_count"
                    ),
                    "word_count": clause.get(
                        "word_count"
                    )
                })

        with self.db.driver.session() as session:
            session.run(query, clauses=rows).consume()

        return len(rows)

    def populate_risks(self):
        """
        Create/merge RiskCategory nodes and HAS_RISK relationships.
        """

        risk_data = self._load_json(self.risks_file)

        query = """
        UNWIND $findings AS finding

        MATCH (c:Clause {
            contract_id: finding.contract_id,
            clause_id: finding.clause_id
        })

        MERGE (risk:RiskCategory {
            name: finding.risk_category
        })

        MERGE (c)-[r:HAS_RISK {
            risk_category: finding.risk_category
        }]->(risk)

        SET
            r.risk_score = finding.risk_score,
            r.risk_level = finding.risk_level,
            r.matched_keywords = finding.matched_keywords,
            r.finding = finding.finding
        """

        findings = []

        for contract in risk_data:
            contract_id = contract["contract_id"]

            for finding in contract.get("findings", []):
                findings.append({
                    "contract_id": contract_id,
                    "clause_id": finding["clause_id"],
                    "risk_category": finding["risk_category"],
                    "risk_score": finding["risk_score"],
                    "risk_level": finding["risk_level"],
                    "matched_keywords": finding.get(
                        "matched_keywords",
                        []
                    ),
                    "finding": finding.get("finding")
                })

        with self.db.driver.session() as session:
            session.run(query, findings=findings).consume()

        return len(findings)

    def populate_clause_types(self):
        """
        Create ClauseType nodes and attach available
        Contract 1 classification predictions.

        The classification checkpoint contains predictions
        for 41 clauses, corresponding to Contract 1.
        """

        classification = self._load_json(
            self.classification_file
        )

        query = """
        UNWIND $predictions AS prediction

        MATCH (c:Clause {
            contract_id: 1,
            clause_id: prediction.clause_id
        })

        MERGE (ct:ClauseType {
            name: prediction.category
        })

        MERGE (c)-[r:HAS_TYPE]->(ct)

        SET r.score = prediction.score
        """

        predictions = []

        for item in classification:
            for prediction in item.get("predictions", []):
                predictions.append({
                    "clause_id": item["clause_id"],
                    "category": prediction["category"],
                    "score": prediction["score"]
                })

        with self.db.driver.session() as session:
            session.run(
                query,
                predictions=predictions
            ).consume()

        return len(predictions)

    def populate_all(self):
        """
        Populate the complete currently available
        Phase 1 → Neo4j graph.
        """

        documents = self.populate_documents()
        clauses = self.populate_clauses()
        risks = self.populate_risks()
        clause_types = self.populate_clause_types()

        return {
            "documents": documents,
            "clauses": clauses,
            "risk_findings": risks,
            "clause_type_predictions": clause_types
        }
