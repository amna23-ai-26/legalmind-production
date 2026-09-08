
class RedlineGenerator:
    """
    Generates structured insertion/deletion redline suggestions
    for High/Critical legal clauses.

    Phase 2 prototype:
    - Uses the exact clause text supplied by the pipeline.
    - Does not invent missing clause text.
    - Produces structured insertion/deletion pairs.
    """

    def __init__(self):
        pass

    def generate(
        self,
        reasoning_result
    ):
        """
        Generate a draft redline for a High/Critical clause.
        """

        risk = reasoning_result.get(
            "risk",
            {}
        )

        risk_level = risk.get(
            "level"
        )

        if risk_level not in (
            "High",
            "Critical"
        ):
            return {
                "status": "not_required",
                "reason": (
                    "Redline generation is only triggered "
                    "for High or Critical clauses."
                ),
                "clause_id": reasoning_result.get(
                    "clause_id"
                )
            }

        clause_text = reasoning_result.get(
            "clause_text",
            ""
        )

        category = risk.get(
            "category"
        )

        if category == "termination":
            return self._termination_redline(
                reasoning_result,
                clause_text
            )

        return self._generic_redline(
            reasoning_result,
            clause_text
        )

    def _termination_redline(
        self,
        reasoning_result,
        clause_text
    ):
        """
        Prototype termination redline.

        Because the available clause text may be truncated,
        only the visible termination language is targeted.
        """

        original_text = (
            "Either party may cancel this Agreement"
        )

        replacement_text = (
            "Either party may terminate this Agreement "
            "subject to the applicable notice, cure, and "
            "termination conditions set forth in this Agreement"
        )

        if original_text.lower() not in clause_text.lower():
            return {
                "status": "needs_review",
                "reason": (
                    "The expected termination phrase was not "
                    "found exactly in the supplied clause text."
                ),
                "clause_id": reasoning_result.get(
                    "clause_id"
                ),
                "deletions": [],
                "insertions": []
            }

        return {
            "status": "draft",
            "clause_id": reasoning_result.get(
                "clause_id"
            ),
            "contract_id": reasoning_result.get(
                "contract_id"
            ),
            "risk_level": reasoning_result.get(
                "risk",
                {}
            ).get(
                "level"
            ),
            "risk_category": "termination",

            "deletions": [
                {
                    "text": original_text,
                    "reason": (
                        "Replace broad cancellation wording with "
                        "more explicit termination language."
                    )
                }
            ],

            "insertions": [
                {
                    "text": replacement_text,
                    "reason": (
                        "Clarify that termination is subject to "
                        "defined notice, cure, and contractual "
                        "termination conditions."
                    )
                }
            ],

            "rationale": (
                "The clause has been classified as High risk. "
                "The proposed modification makes the termination "
                "mechanism more explicit while avoiding invention "
                "of specific notice periods or termination triggers "
                "that are not present in the available clause text."
            ),

            "requires_human_review": True
        }

    def _generic_redline(
        self,
        reasoning_result,
        clause_text
    ):
        """
        Generic fallback for other High/Critical clauses.
        """

        return {
            "status": "needs_review",
            "clause_id": reasoning_result.get(
                "clause_id"
            ),
            "contract_id": reasoning_result.get(
                "contract_id"
            ),
            "risk_level": reasoning_result.get(
                "risk",
                {}
            ).get(
                "level"
            ),
            "risk_category": reasoning_result.get(
                "risk",
                {}
            ).get(
                "category"
            ),
            "deletions": [],
            "insertions": [],
            "rationale": (
                "No category-specific redline template is "
                "currently implemented for this risk category."
            ),
            "requires_human_review": True
        }
