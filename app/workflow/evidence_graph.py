
class EvidenceGraphBuilder:
    """
    Phase 3 Evidence Graph Builder v1.

    Reads the existing Neo4j knowledge graph and produces
    a structured evidence graph for ExplainabilityAgent.

    This component is READ-ONLY.
    It does not create, update, or delete Neo4j data.
    """

    def __init__(self, db):
        self.db = db

    def build(self, contract_id, clause_id):

        query = """
        MATCH (d:Document)-[:HAS_CLAUSE]->(c:Clause)
        WHERE d.contract_id = $contract_id
          AND c.clause_id = $clause_id

        OPTIONAL MATCH (c)-[r]->(target)

        RETURN
            d.contract_id AS contract_id,
            d.document_name AS document_name,
            c.clause_id AS clause_id,
            c.heading AS clause_heading,
            type(r) AS relationship,
            labels(target) AS target_labels,
            properties(target) AS target_properties
        ORDER BY relationship
        """

        with self.db.driver.session() as session:
            rows = session.run(
                query,
                contract_id=contract_id,
                clause_id=clause_id
            ).data()

        if not rows:
            return {
                "available": False,
                "contract_id": contract_id,
                "clause_id": clause_id,
                "nodes": [],
                "edges": []
            }

        nodes = []
        edges = []
        node_ids = set()

        document_id = f"document:{contract_id}"
        clause_node_id = f"clause:{clause_id}"

        first = rows[0]

        # ----------------------------------------------------
        # Document node
        # ----------------------------------------------------

        self._add_node(
            nodes,
            node_ids,
            {
                "id": document_id,
                "type": "Document",
                "label": (
                    first.get("document_name")
                    or f"Contract {contract_id}"
                ),
                "contract_id": contract_id
            }
        )

        # ----------------------------------------------------
        # Clause node
        # ----------------------------------------------------

        self._add_node(
            nodes,
            node_ids,
            {
                "id": clause_node_id,
                "type": "Clause",
                "label": (
                    first.get("clause_heading")
                    or f"Clause {clause_id}"
                ),
                "clause_id": clause_id,
                "contract_id": contract_id
            }
        )

        # Document -> Clause
        edges.append({
            "source": document_id,
            "target": clause_node_id,
            "type": "HAS_CLAUSE"
        })

        # ----------------------------------------------------
        # Clause outgoing relationships
        # ----------------------------------------------------

        for row in rows:

            relationship = row.get("relationship")

            if not relationship:
                continue

            target_labels = (
                row.get("target_labels")
                or []
            )

            target_properties = (
                row.get("target_properties")
                or {}
            )

            target_type = (
                target_labels[0]
                if target_labels
                else "Unknown"
            )

            target_name = (
                target_properties.get("name")
                or target_properties.get("title")
                or target_properties.get("statute_id")
                or target_properties.get("act_id")
                or target_type
            )

            target_id = self._target_id(
                target_type,
                target_properties,
                target_name
            )

            self._add_node(
                nodes,
                node_ids,
                {
                    "id": target_id,
                    "type": target_type,
                    "label": str(target_name),
                    "properties": target_properties
                }
            )

            edges.append({
                "source": clause_node_id,
                "target": target_id,
                "type": relationship
            })

        return {
            "available": True,
            "contract_id": contract_id,
            "clause_id": clause_id,
            "nodes": nodes,
            "edges": edges
        }

    def _target_id(
        self,
        target_type,
        properties,
        fallback_name
    ):
        identifier = (
            properties.get("name")
            or properties.get("statute_id")
            or properties.get("act_id")
            or fallback_name
        )

        return (
            f"{target_type.lower()}:{identifier}"
        )

    def _add_node(
        self,
        nodes,
        node_ids,
        node
    ):
        if node["id"] in node_ids:
            return

        nodes.append(node)
        node_ids.add(node["id"])
