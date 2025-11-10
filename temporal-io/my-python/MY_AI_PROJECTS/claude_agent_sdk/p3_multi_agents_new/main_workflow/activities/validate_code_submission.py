"""Activity 1: Validate code submission (Deterministic)."""

import logging
from typing import Any, Dict, List

from temporalio import activity

from models import CodeSubmission, ProgrammingLanguage

logger = logging.getLogger(__name__)


@activity.defn
async def validate_code_submission(submission: CodeSubmission) -> Dict[str, Any]:
    """
    Activity 1: Validate code submission (Deterministic).

    - Validate file format
    - Check code length
    - Verify metadata
    """
    logger.info(f"Validating code submission: {submission.submission_id}")

    is_valid = True
    errors = []

    # Check language is supported
    if submission.language not in [lang.value for lang in ProgrammingLanguage]:
        errors.append(f"Unsupported language: {submission.language}")
        is_valid = False

    # Check code length (not empty, not too large)
    if len(submission.code) < 10:
        errors.append("Code too short (minimum 10 characters)")
        is_valid = False
    elif len(submission.code) > 100000:
        errors.append("Code too large (maximum 100,000 characters)")
        is_valid = False

    # Check description
    if not submission.description or len(submission.description) < 5:
        errors.append("Description too short (minimum 5 characters)")
        is_valid = False

    result = {"is_valid": is_valid, "errors": errors}

    logger.info(f"Validation result: {'valid' if is_valid else 'invalid'}")
    return result
