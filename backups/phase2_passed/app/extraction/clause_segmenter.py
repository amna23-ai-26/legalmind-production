
import re


def clean_text(text: str) -> str:
    text = text.replace("\xa0", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n\n", text)
    return text.strip()


def is_numbered_heading(line: str) -> bool:
    """
    Accept only standalone legal section numbers:
    1.
    2.
    2.1
    2.2
    3.12
    """

    line = line.strip()

    return bool(
        re.fullmatch(
            r"\d+(?:\.\d+)*\.?",
            line
        )
    )


def is_clear_text_heading(line: str) -> bool:
    """
    Recognize only strong legal headings.
    """

    line = line.strip()

    if not line:
        return False

    # Heading must be reasonably short
    if len(line) > 70:
        return False

    # Must end with period
    if not line.endswith("."):
        return False

    words = line.rstrip(".").split()

    if len(words) > 7:
        return False

    # Must start with uppercase letter
    if not re.match(r"^[A-Z]", line):
        return False

    # Reject obvious sentence fragments
    rejected_starts = (
        "and ",
        "or ",
        "but ",
        "if ",
        "unless ",
        "when ",
        "where ",
        "that ",
        "which ",
        "this ",
        "the ",
        "a ",
        "an ",
        "to ",
        "of ",
        "for ",
        "in ",
        "on ",
        "at ",
        "by ",
        "as ",
    )

    lower = line.lower()

    if lower.startswith(rejected_starts):
        return False

    # Reject lines containing quotation fragments
    if '"' in line or "“" in line or "”" in line:
        return False

    # Reject obvious sentence-like fragments
    if line.count(",") > 1:
        return False

    return True


def is_heading(line: str) -> bool:

    return (
        is_numbered_heading(line)
        or is_clear_text_heading(line)
    )


def segment_clauses(text: str):

    text = clean_text(text)

    lines = text.splitlines()

    heading_positions = []

    for i, line in enumerate(lines):

        line = line.strip()

        if is_heading(line):
            heading_positions.append(i)

    clauses = []

    for i, start in enumerate(heading_positions):

        if i + 1 < len(heading_positions):
            end = heading_positions[i + 1]
        else:
            end = len(lines)

        section_lines = []

        for line in lines[start:end]:

            line = line.strip()

            if line:
                section_lines.append(line)

        if not section_lines:
            continue

        clause_text = "\n".join(section_lines)

        # Ignore very small fragments
        if len(clause_text.split()) < 30:
            continue

        clauses.append({
            "clause_id": len(clauses) + 1,
            "heading": section_lines[0],
            "text": clause_text,
            "character_count": len(clause_text),
            "word_count": len(clause_text.split())
        })

    return clauses
