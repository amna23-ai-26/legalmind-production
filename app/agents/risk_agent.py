
# LegalMind Rule-Based Risk Agent

RISK_RULES = {
    "confidentiality": {
        "keywords": ["confidential", "confidentiality", "trade secret"],
        "score": 3
    },
    "exclusivity": {
        "keywords": ["exclusive", "sole"],
        "score": 3
    },
    "governing_law": {
        "keywords": ["governing law", "jurisdiction", "laws of"],
        "score": 3
    },
    "indemnification": {
        "keywords": ["indemnify"],
        "score": 4
    },
    "intellectual_property": {
        "keywords": [
            "copyright",
            "intellectual property",
            "patent",
            "trademark"
        ],
        "score": 3
    },
    "liability": {
        "keywords": ["damages", "liability", "liable"],
        "score": 4
    },
    "payment": {
        "keywords": ["fees", "payment", "price"],
        "score": 2
    },
    "renewal": {
        "keywords": ["renew", "renewal", "successive"],
        "score": 3
    },
    "termination": {
        "keywords": [
            "cancel",
            "cancellation",
            "terminate",
            "termination"
        ],
        "score": 3
    }
}


def get_risk_level(score):
    if score >= 4:
        return "Critical"
    elif score >= 3:
        return "High"
    elif score >= 2:
        return "Moderate"
    return "Low"


def analyze_risks(clauses):

    findings = []

    for clause in clauses:

        clause_id = clause.get("clause_id")
        heading = clause.get("heading", "")
        text = clause.get("text", "")

        if not text:
            continue

        text_lower = text.lower()

        for category, rule in RISK_RULES.items():

            matched_keywords = []

            for keyword in rule["keywords"]:
                if keyword.lower() in text_lower:
                    matched_keywords.append(keyword)

            if matched_keywords:

                score = rule["score"]

                findings.append({
                    "clause_id": clause_id,
                    "heading": heading,
                    "risk_category": category,
                    "risk_score": score,
                    "risk_level": get_risk_level(score),
                    "matched_keywords": matched_keywords,
                    "finding": (
                        f"Clause contains language related to {category}."
                    )
                })

    return findings
