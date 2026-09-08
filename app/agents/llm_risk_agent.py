import json
import re


class LLMRiskAgent:
    def __init__(self, provider):
        self.provider = provider

    def _extract_json(self, text):
        text = text.strip()

        try:
            return json.loads(text)
        except Exception:
            pass

        match = re.search(r"\{.*\}", text, re.DOTALL)

        if not match:
            return None

        try:
            return json.loads(match.group(0))
        except Exception:
            return None

    def _needs_llm(self, clause, rule_findings):
        if rule_findings:
            return False

        text = str(clause.get("text", "")).lower()

        ambiguity_markers = [
            "without notice",
            "sole discretion",
            "unlimited",
            "waive",
            "waiver",
            "automatically",
            "penalty",
            "non-compete",
            "noncompete",
            "exclusive",
            "survive",
            "notwithstanding",
            "material breach",
            "injunction",
        ]

        return any(marker in text for marker in ambiguity_markers)

    def analyze_clause(self, clause, rule_findings=None):
        rule_findings = rule_findings or []

        if not self._needs_llm(clause, rule_findings):
            return None

        clause_id = clause.get("clause_id")
        heading = clause.get("heading", "")
        text = clause.get("text", "")

        prompt = f"""
You are a legal risk classification assistant.

Analyze ONLY the contract clause supplied below.
Do not cite laws or cases.
Do not invent legal authorities.
Return ONLY valid JSON with these fields:

{{
  "risk_category": "string",
  "risk_score": 1,
  "risk_level": "Low|Moderate|High|Critical",
  "finding": "one concise sentence",
  "reasoning": "one concise sentence"
}}

Risk score meanings:
1 = Low
2 = Moderate
3 = High
4 = Critical

Clause heading:
{heading}

Clause text:
{text}
"""

        try:
            raw = self.provider.generate(prompt)
            result = self._extract_json(raw)

            if not isinstance(result, dict):
                return None

            score = int(result.get("risk_score", 0))

            if score not in (1, 2, 3, 4):
                return None

            level_map = {
                1: "Low",
                2: "Moderate",
                3: "High",
                4: "Critical",
            }

            return {
                "clause_id": clause_id,
                "heading": heading,
                "risk_category": str(
                    result.get("risk_category", "general")
                ),
                "risk_score": score,
                "risk_level": level_map[score],
                "finding": str(result.get("finding", "")),
                "reasoning": str(result.get("reasoning", "")),
                "source": "llm",
            }

        except Exception:
            return None

    def analyze(self, clauses, rule_findings=None):
        rule_findings = rule_findings or []

        by_clause = {}

        for finding in rule_findings:
            by_clause.setdefault(
                finding.get("clause_id"),
                []
            ).append(finding)

        findings = []

        for clause in clauses:
            result = self.analyze_clause(
                clause,
                by_clause.get(clause.get("clause_id"), [])
            )

            if result is not None:
                findings.append(result)

        return findings
