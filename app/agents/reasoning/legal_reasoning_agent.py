
class LegalReasoningAgent:
    """
    Legal Reasoning Agent for LegalMind Phase 2.

    Combines:
    - clause information
    - risk findings
    - Neo4j legal authorities
    - CourtListener evidence

    Produces a structured legal assessment,
    negotiation recommendations, and redline inputs.
    """

    def __init__(self):
        pass

    @staticmethod
    def _safe_text(value):
        if value is None:
            return ""

        return str(value).strip()

    def analyze_clause(
        self,
        clause,
        risk_findings=None,
        legal_authorities=None,
        case_law=None,
        contract_id=None,
        clause_id=None
    ):
        """
        Produce structured legal reasoning for one clause.
        """

        risk_findings = risk_findings or []
        legal_authorities = legal_authorities or []
        case_law = case_law or []

        heading = self._safe_text(
            clause.get("heading")
        )

        text = self._safe_text(
            clause.get("text")
        )

        risk_level = "Unknown"
        risk_score = None
        risk_category = None

        if risk_findings:
            finding = risk_findings[0]

            risk_level = finding.get(
                "risk_level",
                "Unknown"
            )

            risk_score = finding.get(
                "risk_score"
            )

            risk_category = finding.get(
                "risk_category"
            )

        assessment = self._build_assessment(
            heading=heading,
            text=text,
            risk_category=risk_category,
            risk_level=risk_level,
            risk_score=risk_score
        )

        recommendations = self._build_recommendations(
            risk_category=risk_category,
            risk_level=risk_level
        )

        evidence_summary = self._build_evidence_summary(
            legal_authorities,
            case_law
        )

        return {
            "clause_id": (
                clause.get("clause_id")
                or clause_id
            ),
            "contract_id": (
                clause.get("contract_id")
                or contract_id
            ),
            "clause_heading": heading,
            "clause_text": text,
            "risk": {
                "category": risk_category,
                "score": risk_score,
                "level": risk_level
            },
            "legal_assessment": assessment,
            "negotiation_recommendations": recommendations,
            "supporting_evidence": evidence_summary,
            "reasoning_status": "draft"
        }

    def _build_assessment(
        self,
        heading,
        text,
        risk_category,
        risk_level,
        risk_score
    ):
        if risk_category == "termination":

            return (
                "The clause contains termination or cancellation "
                "rights that may materially affect the parties' "
                "ability to end the agreement. The identified "
                f"risk level is {risk_level} "
                f"(score {risk_score}). "
                "The termination conditions, notice requirements, "
                "and triggering events should be reviewed carefully "
                "to determine whether the rights are balanced and "
                "sufficiently clear."
            )

        return (
            f"The clause is classified under the "
            f"{risk_category or 'unclassified'} category. "
            f"The current risk level is {risk_level} "
            f"with a score of {risk_score}. "
            "Further legal review should consider the wording, "
            "obligations imposed on each party, and applicable "
            "legal authorities."
        )

    def _build_recommendations(
        self,
        risk_category,
        risk_level
    ):
        recommendations = []

        if risk_category == "termination":

            recommendations.extend([
                "Review whether termination rights are reciprocal.",
                "Verify that notice periods are clearly defined.",
                "Identify all termination triggers and determine "
                "whether they are objectively measurable.",
                "Consider adding an appropriate cure period for "
                "remediable breaches.",
                "Confirm that termination consequences and "
                "post-termination obligations are clearly stated."
            ])

        if risk_level in ("High", "Critical"):

            recommendations.append(
                "Obtain human legal review before accepting the "
                "clause without modification."
            )

        if not recommendations:

            recommendations.append(
                "Review the clause against the applicable "
                "contractual and jurisdictional requirements."
            )

        return recommendations

    def _build_evidence_summary(
        self,
        legal_authorities,
        case_law
    ):
        """
        Normalize Neo4j authorities and CourtListener
        case-law evidence into a consistent structure.

        Handles both:
        - list[dict]
        - list[list[dict]]
        """

        # --------------------------------------------------
        # Flatten nested authority lists
        # --------------------------------------------------

        normalized_authorities = []

        def flatten_authorities(items):
            if not items:
                return

            for item in items:

                if isinstance(item, list):
                    flatten_authorities(item)

                elif isinstance(item, dict):
                    normalized_authorities.append(item)

        flatten_authorities(legal_authorities)

        # --------------------------------------------------
        # Build authority evidence
        # --------------------------------------------------

        authorities = []

        for authority in normalized_authorities:

            authorities.append({
                "source": "Neo4j",
                "type": "legal_authority",
                "contract_id": authority.get(
                    "contract_id"
                ),
                "clause_id": authority.get(
                    "clause_id"
                ),
                "statute_id": authority.get(
                    "statute_id"
                ),
                "title": authority.get(
                    "statute_title"
                ),
                "jurisdiction": authority.get(
                    "jurisdiction"
                ),
                "amending_act_id": authority.get(
                    "amending_act_id"
                ),
                "amending_act_title": authority.get(
                    "amending_act_title"
                )
            })

        # --------------------------------------------------
        # Normalize case-law evidence
        # --------------------------------------------------

        normalized_cases = []

        if case_law:
            for item in case_law:

                if isinstance(item, list):
                    normalized_cases.extend(item)

                elif isinstance(item, dict):
                    normalized_cases.append(item)

        cases = []

        for case in normalized_cases:

            cases.append({
                "source": case.get(
                    "source",
                    "CourtListener"
                ),
                "title": case.get(
                    "title"
                ),
                "citation": case.get(
                    "citation",
                    []
                ),
                "jurisdiction": case.get(
                    "jurisdiction"
                ),
                "url": case.get(
                    "url"
                ),
                "relevance_score": case.get(
                    "relevance_score"
                )
            })

        return {
            "legal_authorities": authorities,
            "case_law": cases
        }

    def process(
        self,
        research_result,
        risk_findings=None
    ):
        """
        Process a Research Agent result and produce
        a draft legal reasoning output.
        """

        clause = research_result.get(
            "clause",
            {}
        )

        legal_authorities = research_result.get(
            "graph_authorities",
            []
        )

        case_law = research_result.get(
            "ranked_case_law",
            []
        )

        return self.analyze_clause(
            clause=clause,
            risk_findings=risk_findings,
            legal_authorities=legal_authorities,
            case_law=case_law,
            contract_id=research_result.get(
                "contract_id"
            ),
            clause_id=research_result.get(
                "clause_id"
            )
        )
