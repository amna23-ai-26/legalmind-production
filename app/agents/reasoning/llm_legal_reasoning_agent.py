import json
import re


class LLMReasoningAgent:
    """
    Additive LLM reasoning layer.

    Uses only supplied clause, risk, and research evidence.
    Does not perform independent legal research.
    """

    def __init__(self, provider):
        self.provider = provider

    def _extract_json(self, text):
        text = str(text).strip()

        try:
            return json.loads(text)
        except Exception:
            pass

        match = re.search(r"\\{.*\\}", text, re.DOTALL)

        if not match:
            match = re.search(r"\{.*\}", text, re.DOTALL)

        if not match:
            return None

        try:
            return json.loads(match.group(0))
        except Exception:
            return None

    @staticmethod
    def _safe(value):
        if value is None:
            return ""
        return str(value).strip()

    def _evidence_text(self, research_result):
        authorities = research_result.get(
            "graph_authorities",
            []
        )

        cases = research_result.get(
            "ranked_case_law",
            []
        )

        return {
            "legal_authorities": authorities,
            "case_law": cases
        }

    def analyze(self, research_result, risk_findings=None):
        risk_findings = risk_findings or []

        clause = research_result.get("clause", {})

        heading = self._safe(clause.get("heading"))
        text = self._safe(clause.get("text"))

        evidence = self._evidence_text(research_result)

        prompt = f"""
You are the LegalMind legal reasoning assistant.

Produce a cautious legal assessment using ONLY the supplied
contract clause, risk findings, and retrieved evidence.

Do NOT invent statutes, cases, citations, URLs, legal rules,
facts, or authorities.

If the supplied evidence is insufficient, explicitly say so.

Return ONLY valid JSON:

{{
  "legal_assessment": "concise assessment",
  "key_issues": ["issue 1"],
  "negotiation_recommendations": ["recommendation 1"],
  "redline_recommendation": "concise suggested change or empty string",
  "evidence_basis": ["basis 1"],
  "confidence": 0.0
}}

Confidence must be a number from 0.0 to 1.0.

CLAUSE HEADING:
{heading}

CLAUSE TEXT:
{text}

RISK FINDINGS:
{json.dumps(risk_findings, ensure_ascii=False)}

RETRIEVED LEGAL EVIDENCE:
{json.dumps(evidence, ensure_ascii=False)}
"""

        try:
            raw = self.provider.generate(prompt)
            result = self._extract_json(raw)

            if not isinstance(result, dict):
                return None

            confidence = float(result.get("confidence", 0.0))
            confidence = max(0.0, min(1.0, confidence))

            issues = result.get("key_issues", [])
            recommendations = result.get(
                "negotiation_recommendations",
                []
            )
            evidence_basis = result.get(
                "evidence_basis",
                []
            )

            if not isinstance(issues, list):
                issues = [str(issues)]

            if not isinstance(recommendations, list):
                recommendations = [str(recommendations)]

            if not isinstance(evidence_basis, list):
                evidence_basis = [str(evidence_basis)]

            return {
                "legal_assessment": self._safe(
                    result.get("legal_assessment")
                ),
                "key_issues": [
                    self._safe(item) for item in issues
                ],
                "negotiation_recommendations": [
                    self._safe(item)
                    for item in recommendations
                ],
                "redline_recommendation": (
                    result.get("redline_recommendation")
                    if isinstance(result.get("redline_recommendation"), str)
                    else json.dumps(
                        result.get("redline_recommendation"),
                        ensure_ascii=False,
                    )
                    if result.get("redline_recommendation") is not None
                    else ""
                ),
                "evidence_basis": [
                    self._safe(item)
                    for item in evidence_basis
                ],
                "confidence": confidence,
                "source": "llm",
            }

        except Exception:
            return None
