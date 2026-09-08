
import os
import re


def _clean(value):
    if value is None:
        return None

    value = re.sub(r"\s+", " ", str(value)).strip()
    return value if value else None


def extract_parties(text):
    """
    Extract contracting parties from common agreement language.
    """

    parties = []

    # Specifically handle:
    # "by and between PARTY A ... and PARTY B ..."
    pattern = re.search(
        r"(?:by\s+and\s+between|between)\s+"
        r"(.+?)"
        r"(?:\s+\(referred to as.*?\))?"
        r"\s+and\s+"
        r"(.+?)"
        r"(?:\s+\(referred to as.*?\))?"
        r"\s*,?\s*(?:a corporation|an? corporation|"
        r"WHEREAS|Accordingly|agree)",
        text,
        re.IGNORECASE | re.DOTALL
    )

    if pattern:
        party1 = _clean(pattern.group(1))
        party2 = _clean(pattern.group(2))

        if party1:
            parties.append(party1)

        if party2:
            parties.append(party2)

    # Fallback: capture names from "between X and Y"
    if len(parties) < 2:

        pattern = re.search(
            r"(?:by\s+and\s+between|between)\s+"
            r"([A-Z][A-Z0-9&.,' -]{2,})"
            r"\s+and\s+"
            r"([A-Z][A-Z0-9&.,' -]{2,})",
            text
        )

        if pattern:
            parties = [
                _clean(pattern.group(1)),
                _clean(pattern.group(2))
            ]

    return parties


def extract_agreement_date(text):
    patterns = [
        r"entered\s+(?:into\s+)?(?:this\s+)?"
        r"(?:on\s+)?(?:the\s+)?"
        r"(\d{1,2}(?:st|nd|rd|th)?\s+day\s+of\s+\w+\s+\d{4})",

        r"entered\s+(?:into\s+)?(?:on\s+)?"
        r"(\w+\s+\d{1,2},\s+\d{4})",

        r"dated\s+(?:as\s+of\s+)?"
        r"(\w+\s+\d{1,2},\s+\d{4})"
    ]

    for pattern in patterns:
        match = re.search(
            pattern,
            text,
            re.IGNORECASE
        )

        if match:
            return _clean(match.group(1))

    return None


def extract_effective_date(text):
    patterns = [
        r"effective\s+(?:date|as\s+of)\s*[:\-]?\s*"
        r"(\w+\s+\d{1,2},\s+\d{4})",

        r"effective\s+(?:date|as\s+of)\s*[:\-]?\s*"
        r"(\d{1,2}/\d{1,2}/\d{2,4})"
    ]

    for pattern in patterns:
        match = re.search(
            pattern,
            text,
            re.IGNORECASE
        )

        if match:
            return _clean(match.group(1))

    return None


def extract_contract_type(text):
    first_part = text[:3000].lower()

    contract_types = [
        "affiliate agreement",
        "confidentiality agreement",
        "non-disclosure agreement",
        "nda",
        "employment agreement",
        "license agreement",
        "licensing agreement",
        "service agreement",
        "services agreement",
        "purchase agreement",
        "asset purchase agreement",
        "stock purchase agreement",
        "merger agreement",
        "distribution agreement",
        "marketing agreement",
        "development agreement",
        "consulting agreement",
        "lease agreement",
        "partnership agreement",
        "joint venture agreement"
    ]

    for contract_type in contract_types:
        if contract_type in first_part:
            return contract_type.title()

    return None


def extract_governing_law(text):
    """
    Extract governing law while rejecting incomplete matches.
    """

    patterns = [
        r"governed\s+by\s+(?:the\s+)?laws?\s+of\s+"
        r"(?:the\s+)?(?:State\s+of\s+)?"
        r"([A-Za-z][A-Za-z .'-]{2,40})",

        r"laws?\s+of\s+(?:the\s+)?"
        r"(?:State\s+of\s+)?"
        r"([A-Za-z][A-Za-z .'-]{2,40})"
    ]

    stop_words = {
        "the",
        "a",
        "an",
        "and",
        "or",
        "without",
        "regard",
        "conflict",
        "principles",
        "law",
        "laws"
    }

    for pattern in patterns:

        matches = re.finditer(
            pattern,
            text,
            re.IGNORECASE
        )

        for match in matches:

            value = _clean(match.group(1))

            if not value:
                continue

            words = value.split()

            # Reject clearly incomplete results such as "U"
            if len(value) < 3:
                continue

            if len(words) == 1 and words[0].lower() in stop_words:
                continue

            return value

    return None


def extract_metadata(text, document_name=None):

    if not text:
        return {
            "document_name": document_name,
            "parties": [],
            "agreement_date": None,
            "effective_date": None,
            "contract_type": None,
            "governing_law": None
        }

    return {
        "document_name": (
            os.path.basename(document_name)
            if document_name
            else None
        ),
        "parties": extract_parties(text),
        "agreement_date": extract_agreement_date(text),
        "effective_date": extract_effective_date(text),
        "contract_type": extract_contract_type(text),
        "governing_law": extract_governing_law(text)
    }
