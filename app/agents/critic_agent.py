
"""
LegalMind Phase 3 — Critic Agent.

The Critic Agent validates a LegalReasoningAgent draft against ONLY the
evidence retrieved by the ResearchAgent.

Design constraints:
- No external API calls.
- No new retrieval.
- No modification of ResearchAgent or LegalReasoningAgent.
- Citation validation is closed-world: only ResearchAgent evidence is valid.
- Logical/consistency checks are deterministic v1 checks.
"""

import re


class CriticAgent:
    """
    Phase 3 Critic Agent v1.

    Input:
        reasoning_result:
            Output produced by LegalReasoningAgent.process().

        research_result:
            Original output produced by ResearchAgent.process().

    The ResearchAgent result is the authoritative evidence boundary.
    The critic must NEVER retrieve additional evidence.
    """

    def __init__(self):
        self.version = "phase3-critic-v1"

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def process(self, reasoning_result, research_result):
        """
        Critique a legal reasoning draft against ResearchAgent evidence.

        Returns a structured result containing:
            - status
            - passed
            - citation_check
            - consistency_check
            - issues
            - verified_citations
            - unsupported_citations
            - evidence_count
            - critic_version
        """

        reasoning_result = reasoning_result or {}
        research_result = research_result or {}

        issues = []

        # --------------------------------------------------------------
        # Basic structure validation
        # --------------------------------------------------------------

        if not isinstance(reasoning_result, dict):
            return self._failure(
                "reasoning_result must be a dictionary"
            )

        if not isinstance(research_result, dict):
            return self._failure(
                "research_result must be a dictionary"
            )

        # --------------------------------------------------------------
        # Research evidence boundary
        # --------------------------------------------------------------

        retrieved_evidence = self._get_research_evidence(
            research_result
        )

        if not retrieved_evidence:
            issues.append({
                "type": "missing_research_evidence",
                "severity": "high",
                "message": (
                    "ResearchAgent returned no case-law evidence. "
                    "Citation verification cannot be established."
                )
            })

        # --------------------------------------------------------------
        # Citation verification
        # --------------------------------------------------------------

        citation_result = self._verify_citations(
            reasoning_result,
            retrieved_evidence
        )

        issues.extend(citation_result["issues"])

        # --------------------------------------------------------------
        # Logical / contradiction checks
        # --------------------------------------------------------------

        consistency_result = self._check_consistency(
            reasoning_result,
            research_result
        )

        issues.extend(consistency_result["issues"])

        # --------------------------------------------------------------
        # Overall status
        # --------------------------------------------------------------

        passed = len(issues) == 0

        status = "PASS" if passed else "FAIL"

        revision_instructions = (
            []
            if passed
            else self._build_revision_instructions(issues)
        )

        self_reflection = self._build_self_reflection(
            citation_result,
            consistency_result,
            issues
        )

        return {
            "critic_version": self.version,
            "status": status,
            "passed": passed,

            "citation_check": {
                "passed": citation_result["passed"],
                "retrieved_evidence_count": len(retrieved_evidence),
                "referenced_citation_count": len(
                    citation_result["referenced"]
                ),
                "verified_citations": citation_result["verified"],
                "unsupported_citations": citation_result["unsupported"],
            },

            "consistency_check": {
                "passed": consistency_result["passed"],
                "checks": consistency_result["checks"],
            },

            "issues": issues,

            "revision_instructions": revision_instructions,

            "self_reflection": self_reflection,

            # Explicitly record the evidence boundary.
            "evidence_boundary": {
                "source": "ResearchAgent",
                "external_retrieval_performed": False,
                "retrieved_case_count": len(retrieved_evidence),
            },
        }

    # ------------------------------------------------------------------
    # Research evidence extraction
    # ------------------------------------------------------------------

    def _get_research_evidence(self, research_result):
        """
        Extract ONLY evidence already retrieved by ResearchAgent.

        Phase 2 stores ranked CourtListener evidence under:
            research_result["ranked_case_law"]
        """

        evidence = research_result.get("ranked_case_law", [])

        if evidence is None:
            return []

        if not isinstance(evidence, list):
            return []

        normalized = []

        for item in evidence:

            # ResearchAgent may contain nested lists depending on the
            # evidence/ranking normalization already used in Phase 2.
            if isinstance(item, list):
                normalized.extend(item)
            elif isinstance(item, dict):
                normalized.append(item)

        return [
            item for item in normalized
            if isinstance(item, dict)
        ]

    # ------------------------------------------------------------------
    # Citation verification
    # ------------------------------------------------------------------

    def _verify_citations(self, reasoning_result, retrieved_evidence):
        """
        Verify reasoning citations against the ResearchAgent evidence set.

        IMPORTANT:
            This method performs NO retrieval and does NOT consult any
            external source.
        """

        supporting_evidence = reasoning_result.get(
            "supporting_evidence",
            {}
        )

        if not isinstance(supporting_evidence, dict):
            supporting_evidence = {}

        case_law = supporting_evidence.get(
            "case_law",
            []
        )

        if case_law is None:
            case_law = []

        if not isinstance(case_law, list):
            case_law = []

        referenced = []

        for item in case_law:

            if isinstance(item, list):
                for nested in item:
                    if isinstance(nested, dict):
                        referenced.append(nested)

            elif isinstance(item, dict):
                referenced.append(item)

        verified = []
        unsupported = []
        issues = []

        for citation in referenced:

            if self._citation_matches_retrieved(
                citation,
                retrieved_evidence
            ):
                verified.append(citation)
            else:
                unsupported.append(citation)

        if unsupported:
            issues.append({
                "type": "unsupported_citation",
                "severity": "high",
                "message": (
                    "One or more reasoning citations were not found "
                    "in the ResearchAgent retrieved evidence set."
                ),
                "count": len(unsupported),
            })

        # If reasoning contains a case-law section, every referenced
        # citation must be traceable to ResearchAgent evidence.
        passed = len(unsupported) == 0

        return {
            "passed": passed,
            "referenced": referenced,
            "verified": verified,
            "unsupported": unsupported,
            "issues": issues,
        }

    # ------------------------------------------------------------------
    # Citation matching
    # ------------------------------------------------------------------

    def _citation_matches_retrieved(
        self,
        citation,
        retrieved_evidence
    ):
        """
        Match a reasoning citation to a ResearchAgent result.

        Matching uses stable identifying fields when available:
            - citation
            - case_id / id
            - title
            - URL

        This is intentionally closed-world.
        """

        citation_keys = self._identity_values(citation)

        if not citation_keys:
            return False

        for evidence in retrieved_evidence:

            evidence_keys = self._identity_values(evidence)

            if not evidence_keys:
                continue

            if citation_keys.intersection(evidence_keys):
                return True

        return False

    def _identity_values(self, item):
        """
        Extract normalized identifying values from an evidence/citation dict.
        """

        if not isinstance(item, dict):
            return set()

        values = set()

        candidate_keys = [
            "id",
            "case_id",
            "citation",
            "title",
            "name",
            "url",
            "absolute_url",
            "cluster",
        ]

        for key in candidate_keys:

            value = item.get(key)

            if value is None:
                continue

            if isinstance(value, list):
                for v in value:
                    normalized = self._normalize_identifier(v)
                    if normalized:
                        values.add(normalized)
            else:
                normalized = self._normalize_identifier(value)

                if normalized:
                    values.add(normalized)

        return values

    def _normalize_identifier(self, value):
        """
        Normalize an identifier for safe equality matching.
        """

        if value is None:
            return ""

        if isinstance(value, dict):
            return ""

        value = str(value).strip().lower()

        value = re.sub(
            r"\s+",
            " ",
            value
        )

        return value

    # ------------------------------------------------------------------
    # Logical / contradiction checks
    # ------------------------------------------------------------------

    def _check_consistency(
        self,
        reasoning_result,
        research_result
    ):
        """
        Deterministic v1 logical-consistency checks.

        These checks intentionally do not attempt to replace a legal
        reasoning model. They identify obvious structural contradictions
        that can be safely detected without external retrieval.
        """

        checks = []
        issues = []

        assessment = self._text(
            reasoning_result.get("legal_assessment")
        )

        recommendations = reasoning_result.get(
            "negotiation_recommendations",
            []
        )

        if recommendations is None:
            recommendations = []

        if isinstance(recommendations, str):
            recommendation_text = recommendations
        elif isinstance(recommendations, list):
            recommendation_text = " ".join(
                self._text(x)
                for x in recommendations
            )
        else:
            recommendation_text = self._text(
                recommendations
            )

        # --------------------------------------------------------------
        # Check 1 — reasoning output exists
        # --------------------------------------------------------------

        has_assessment = bool(assessment.strip())

        checks.append({
            "name": "non_empty_legal_assessment",
            "passed": has_assessment,
        })

        if not has_assessment:
            issues.append({
                "type": "missing_legal_assessment",
                "severity": "high",
                "message": (
                    "Legal reasoning did not produce a legal assessment."
                )
            })

        # --------------------------------------------------------------
        # Check 2 — recommendations exist
        # --------------------------------------------------------------

        has_recommendations = bool(
            recommendation_text.strip()
        )

        checks.append({
            "name": "non_empty_recommendations",
            "passed": has_recommendations,
        })

        if not has_recommendations:
            issues.append({
                "type": "missing_recommendations",
                "severity": "medium",
                "message": (
                    "Legal reasoning did not produce negotiation "
                    "recommendations."
                )
            })

        # --------------------------------------------------------------
        # Check 3 — obvious self-contradictory language
        # --------------------------------------------------------------

        contradiction_pairs = [
            (
                r"\bhigh risk\b",
                r"\blow risk\b",
                "Reasoning contains both high-risk and low-risk conclusions."
            ),
            (
                r"\bhigh risk\b",
                r"\bno risk\b",
                "Reasoning contains both high-risk and no-risk conclusions."
            ),
            (
                r"\bnot enforceable\b",
                r"\benforceable\b",
                "Reasoning contains both enforceable and not-enforceable conclusions."
            ),
            (
                r"\bprohibited\b",
                r"\bpermitted\b",
                "Reasoning contains both prohibited and permitted conclusions."
            ),
            (
                r"\brequired\b",
                r"\bnot required\b",
                "Reasoning contains both required and not-required conclusions."
            ),
        ]

        combined_text = (
            assessment + " " + recommendation_text
        ).lower()

        detected_contradictions = []

        for left, right, message in contradiction_pairs:

            if (
                re.search(left, combined_text)
                and re.search(right, combined_text)
            ):
                detected_contradictions.append(message)

        checks.append({
            "name": "obvious_contradiction_scan",
            "passed": len(detected_contradictions) == 0,
            "detected": detected_contradictions,
        })

        for message in detected_contradictions:
            issues.append({
                "type": "logical_contradiction",
                "severity": "high",
                "message": message,
            })

        # --------------------------------------------------------------
        # Check 4 — research / reasoning clause identity
        # --------------------------------------------------------------

        reasoning_clause_id = reasoning_result.get(
            "clause_id"
        )

        research_clause_id = research_result.get(
            "clause_id"
        )

        clause_identity_ok = True

        if (
            reasoning_clause_id is not None
            and research_clause_id is not None
        ):
            clause_identity_ok = (
                str(reasoning_clause_id)
                == str(research_clause_id)
            )

        checks.append({
            "name": "research_reasoning_clause_alignment",
            "passed": clause_identity_ok,
        })

        if not clause_identity_ok:
            issues.append({
                "type": "clause_mismatch",
                "severity": "high",
                "message": (
                    "ResearchAgent and LegalReasoningAgent outputs "
                    "refer to different clause IDs."
                ),
                "research_clause_id": research_clause_id,
                "reasoning_clause_id": reasoning_clause_id,
            })

        return {
            "passed": len(issues) == 0,
            "checks": checks,
            "issues": issues,
        }

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _text(self, value):
        if value is None:
            return ""

        if isinstance(value, str):
            return value

        if isinstance(value, list):
            return " ".join(
                self._text(x)
                for x in value
            )

        if isinstance(value, dict):
            return " ".join(
                self._text(v)
                for v in value.values()
            )

        return str(value)


    def _build_revision_instructions(self, issues):
        """
        Convert Critic findings into actionable revision instructions.

        IMPORTANT:
            Instructions are derived ONLY from Critic findings.
            No external evidence or retrieval is introduced.
        """

        instructions = []

        for issue in issues:

            if not isinstance(issue, dict):
                continue

            issue_type = issue.get("type")

            if issue_type == "unsupported_citation":
                instructions.append({
                    "type": "citation_revision",
                    "priority": "high",
                    "instruction": (
                        "Remove or replace unsupported citations. "
                        "Every case-law citation must be traceable "
                        "to the exact ResearchAgent retrieved evidence set."
                    ),
                })

            elif issue_type == "missing_research_evidence":
                instructions.append({
                    "type": "evidence_revision",
                    "priority": "high",
                    "instruction": (
                        "Do not assert case-law support that cannot be "
                        "verified against the ResearchAgent evidence set."
                    ),
                })

            elif issue_type == "missing_legal_assessment":
                instructions.append({
                    "type": "reasoning_revision",
                    "priority": "high",
                    "instruction": (
                        "Provide a substantive legal assessment before "
                        "resubmitting the reasoning draft."
                    ),
                })

            elif issue_type == "missing_recommendations":
                instructions.append({
                    "type": "recommendation_revision",
                    "priority": "medium",
                    "instruction": (
                        "Provide clear negotiation recommendations "
                        "consistent with the legal assessment."
                    ),
                })

            elif issue_type == "logical_contradiction":
                instructions.append({
                    "type": "consistency_revision",
                    "priority": "high",
                    "instruction": (
                        "Resolve the detected logical contradiction. "
                        "The revised legal assessment and recommendations "
                        "must express one internally consistent conclusion."
                    ),
                })

            elif issue_type == "clause_mismatch":
                instructions.append({
                    "type": "alignment_revision",
                    "priority": "high",
                    "instruction": (
                        "Align the reasoning output with the exact clause "
                        "identified by the ResearchAgent result."
                    ),
                })

            elif issue_type == "invalid_input":
                instructions.append({
                    "type": "input_revision",
                    "priority": "high",
                    "instruction": (
                        "Return the required structured reasoning output "
                        "before requesting Critic review again."
                    ),
                })

            else:
                message = issue.get("message")

                instructions.append({
                    "type": "general_revision",
                    "priority": issue.get("severity", "medium"),
                    "instruction": (
                        str(message)
                        if message
                        else "Address the Critic finding before resubmission."
                    ),
                })

        return instructions


    def _build_self_reflection(
        self,
        citation_result,
        consistency_result,
        issues
    ):
        """
        Structured deterministic self-review of the Critic decision.

        This is intentionally not an additional retrieval or reasoning model.
        It summarizes whether the Critic's independent checks found anything
        requiring correction.
        """

        citation_passed = bool(
            citation_result.get("passed")
        )

        consistency_passed = bool(
            consistency_result.get("passed")
        )

        issue_count = len(issues)

        if issue_count == 0:
            conclusion = (
                "Critic review found no citation-support or "
                "logical-consistency issue within the closed-world "
                "ResearchAgent evidence boundary."
            )
        else:
            conclusion = (
                "Critic review identified findings that require "
                "correction before the reasoning draft can be accepted."
            )

        return {
            "performed": True,
            "method": "deterministic_internal_review",
            "citation_review_passed": citation_passed,
            "consistency_review_passed": consistency_passed,
            "issue_count": issue_count,
            "conclusion": conclusion,
        }

    def _failure(self, message):
        return {
            "critic_version": self.version,
            "status": "FAIL",
            "passed": False,
            "citation_check": {
                "passed": False,
                "retrieved_evidence_count": 0,
                "referenced_citation_count": 0,
                "verified_citations": [],
                "unsupported_citations": [],
            },
            "consistency_check": {
                "passed": False,
                "checks": [],
            },
            "issues": [
                {
                    "type": "invalid_input",
                    "severity": "high",
                    "message": message,
                }
            ],
            "revision_instructions": [
                {
                    "type": "input_revision",
                    "priority": "high",
                    "instruction": (
                        "Return the required structured reasoning output "
                        "before requesting Critic review again."
                    ),
                }
            ],
            "self_reflection": {
                "performed": True,
                "method": "deterministic_internal_review",
                "citation_review_passed": False,
                "consistency_review_passed": False,
                "issue_count": 1,
                "conclusion": (
                    "Critic input validation failed and the reasoning "
                    "draft must be corrected before resubmission."
                ),
            },
            "evidence_boundary": {
                "source": "ResearchAgent",
                "external_retrieval_performed": False,
                "retrieved_case_count": 0,
            },
        }
