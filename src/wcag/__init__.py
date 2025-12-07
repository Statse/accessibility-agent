"""
WCAG Validation Module

Provides WCAG 2.1/2.2 compliance validation for accessibility testing.
Integrates with screen reader output and agent exploration data.
"""

from src.wcag.criteria_mapper import (
    WCAGLevel,
    WCAGVersion,
    IssueSeverity,
    WCAGCriterion,
    get_criterion,
    get_criteria_by_level,
    get_criteria_by_principle,
    get_testable_criteria,
    get_severity_for_criterion,
    ALL_CRITERIA,
)

from src.wcag.issue_detector import (
    AccessibilityIssue,
    IssueDetector,
    MissingAltTextDetector,
    MissingFormLabelDetector,
    KeyboardTrapDetector,
    MissingSkipLinkDetector,
    HeadingStructureDetector,
    InsufficientLinkTextDetector,
    IncompleteARIADetector,
)

from src.wcag.validator import (
    ValidationReport,
    WCAGValidator,
)

__all__ = [
    # Enums
    "WCAGLevel",
    "WCAGVersion",
    "IssueSeverity",
    # Models
    "WCAGCriterion",
    "AccessibilityIssue",
    "ValidationReport",
    # Detectors
    "IssueDetector",
    "MissingAltTextDetector",
    "MissingFormLabelDetector",
    "KeyboardTrapDetector",
    "MissingSkipLinkDetector",
    "HeadingStructureDetector",
    "InsufficientLinkTextDetector",
    "IncompleteARIADetector",
    # Validator
    "WCAGValidator",
    # Functions
    "get_criterion",
    "get_criteria_by_level",
    "get_criteria_by_principle",
    "get_testable_criteria",
    "get_severity_for_criterion",
    # Constants
    "ALL_CRITERIA",
]
