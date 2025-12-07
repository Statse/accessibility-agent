"""
WCAG 2.1/2.2 Criteria Mapper

Defines all WCAG success criteria relevant to screen reader testing.
Each criterion includes: ID, name, level, version, description, and detection method.
"""

from enum import Enum
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class WCAGLevel(str, Enum):
    """WCAG conformance levels"""
    A = "A"
    AA = "AA"
    AAA = "AAA"


class WCAGVersion(str, Enum):
    """WCAG specification versions"""
    WCAG_2_0 = "2.0"
    WCAG_2_1 = "2.1"
    WCAG_2_2 = "2.2"


class IssueSeverity(str, Enum):
    """Issue severity classification"""
    CRITICAL = "critical"  # Blocking issues (keyboard traps, inaccessible forms)
    HIGH = "high"  # Major barriers (missing labels, unlabeled images)
    MEDIUM = "medium"  # Usability issues (poor link text, heading structure)
    LOW = "low"  # Minor issues (inconsistent labeling)


class WCAGCriterion(BaseModel):
    """WCAG success criterion definition"""
    model_config = ConfigDict(frozen=True, use_enum_values=True)

    criterion_id: str = Field(
        ..., description="WCAG criterion number (e.g., '1.1.1')"
    )
    name: str = Field(..., description="Criterion name")
    level: WCAGLevel = Field(..., description="Conformance level (A, AA, AAA)")
    version: WCAGVersion = Field(
        ..., description="WCAG version where criterion was introduced"
    )
    description: str = Field(..., description="What this criterion requires")
    detection_method: str = Field(
        ..., description="How screen reader testing can detect violations"
    )
    guideline: str = Field(..., description="Parent guideline number (e.g., '1.1')")
    principle: str = Field(
        ..., description="Parent principle (Perceivable, Operable, Understandable, Robust)"
    )

    def get_full_name(self) -> str:
        """Get formatted criterion name with ID"""
        return f"{self.criterion_id} {self.name} (Level {self.level})"


# WCAG 2.1/2.2 Success Criteria
# Organized by principle and guideline

# ==============================================================================
# Principle 1: Perceivable
# ==============================================================================

CRITERION_1_1_1 = WCAGCriterion(
    criterion_id="1.1.1",
    name="Non-text Content",
    level=WCAGLevel.A,
    version=WCAGVersion.WCAG_2_0,
    guideline="1.1",
    principle="Perceivable",
    description="All non-text content has a text alternative that serves the equivalent purpose",
    detection_method="NVDA announces 'unlabeled graphic' or is silent when encountering images",
)

CRITERION_1_3_1 = WCAGCriterion(
    criterion_id="1.3.1",
    name="Info and Relationships",
    level=WCAGLevel.A,
    version=WCAGVersion.WCAG_2_0,
    guideline="1.3",
    principle="Perceivable",
    description="Information, structure, and relationships can be programmatically determined",
    detection_method="Missing form labels, improper heading structure, incorrect ARIA roles",
)

CRITERION_1_4_3 = WCAGCriterion(
    criterion_id="1.4.3",
    name="Contrast (Minimum)",
    level=WCAGLevel.AA,
    version=WCAGVersion.WCAG_2_0,
    guideline="1.4",
    principle="Perceivable",
    description="Text has a contrast ratio of at least 4.5:1",
    detection_method="Not detectable via screen reader - requires visual analysis",
)

# ==============================================================================
# Principle 2: Operable
# ==============================================================================

CRITERION_2_1_1 = WCAGCriterion(
    criterion_id="2.1.1",
    name="Keyboard",
    level=WCAGLevel.A,
    version=WCAGVersion.WCAG_2_0,
    guideline="2.1",
    principle="Operable",
    description="All functionality is available from a keyboard",
    detection_method="Element not reachable by Tab or NVDA navigation shortcuts",
)

CRITERION_2_1_2 = WCAGCriterion(
    criterion_id="2.1.2",
    name="No Keyboard Trap",
    level=WCAGLevel.A,
    version=WCAGVersion.WCAG_2_0,
    guideline="2.1",
    principle="Operable",
    description="Keyboard focus can be moved away from a component using only keyboard",
    detection_method="Agent stuck in element, cannot Tab out (circular navigation detected)",
)

CRITERION_2_4_1 = WCAGCriterion(
    criterion_id="2.4.1",
    name="Bypass Blocks",
    level=WCAGLevel.A,
    version=WCAGVersion.WCAG_2_0,
    guideline="2.4",
    principle="Operable",
    description="A mechanism is available to bypass blocks of repeated content",
    detection_method="No skip link detected at page start (first Tab should be skip link)",
)

CRITERION_2_4_4 = WCAGCriterion(
    criterion_id="2.4.4",
    name="Link Purpose (In Context)",
    level=WCAGLevel.A,
    version=WCAGVersion.WCAG_2_0,
    guideline="2.4",
    principle="Operable",
    description="The purpose of each link can be determined from link text alone",
    detection_method="NVDA announces 'link' with no text or generic text like 'click here', 'read more'",
)

CRITERION_2_4_6 = WCAGCriterion(
    criterion_id="2.4.6",
    name="Headings and Labels",
    level=WCAGLevel.AA,
    version=WCAGVersion.WCAG_2_0,
    guideline="2.4",
    principle="Operable",
    description="Headings and labels describe topic or purpose",
    detection_method="Poor heading hierarchy (H1 → H4 without H2/H3), missing headings, generic labels",
)

CRITERION_2_4_7 = WCAGCriterion(
    criterion_id="2.4.7",
    name="Focus Visible",
    level=WCAGLevel.AA,
    version=WCAGVersion.WCAG_2_0,
    guideline="2.4",
    principle="Operable",
    description="Keyboard focus indicator is visible",
    detection_method="Not reliably detectable via screen reader - requires visual verification",
)

CRITERION_2_5_3 = WCAGCriterion(
    criterion_id="2.5.3",
    name="Label in Name",
    level=WCAGLevel.A,
    version=WCAGVersion.WCAG_2_1,
    guideline="2.5",
    principle="Operable",
    description="Accessible name contains visible label text",
    detection_method="NVDA announces different text than visible label (requires visual comparison)",
)

# ==============================================================================
# Principle 3: Understandable
# ==============================================================================

CRITERION_3_2_4 = WCAGCriterion(
    criterion_id="3.2.4",
    name="Consistent Identification",
    level=WCAGLevel.AA,
    version=WCAGVersion.WCAG_2_0,
    guideline="3.2",
    principle="Understandable",
    description="Components with same functionality are identified consistently",
    detection_method="Same element type announced differently across pages",
)

CRITERION_3_3_2 = WCAGCriterion(
    criterion_id="3.3.2",
    name="Labels or Instructions",
    level=WCAGLevel.A,
    version=WCAGVersion.WCAG_2_0,
    guideline="3.3",
    principle="Understandable",
    description="Labels or instructions are provided when content requires user input",
    detection_method="NVDA announces 'edit' or form field with no label or context",
)

CRITERION_3_3_3 = WCAGCriterion(
    criterion_id="3.3.3",
    name="Error Suggestion",
    level=WCAGLevel.AA,
    version=WCAGVersion.WCAG_2_0,
    guideline="3.3",
    principle="Understandable",
    description="Error suggestions are provided when input errors are detected",
    detection_method="Form error announced with no recovery instructions",
)

# ==============================================================================
# Principle 4: Robust
# ==============================================================================

CRITERION_4_1_2 = WCAGCriterion(
    criterion_id="4.1.2",
    name="Name, Role, Value",
    level=WCAGLevel.A,
    version=WCAGVersion.WCAG_2_0,
    guideline="4.1",
    principle="Robust",
    description="Name and role can be programmatically determined for UI components",
    detection_method="NVDA cannot determine element role, announces generic 'clickable' or is silent",
)

CRITERION_4_1_3 = WCAGCriterion(
    criterion_id="4.1.3",
    name="Status Messages",
    level=WCAGLevel.AA,
    version=WCAGVersion.WCAG_2_1,
    guideline="4.1",
    principle="Robust",
    description="Status messages can be programmatically determined",
    detection_method="Dynamic content changes not announced by NVDA (requires live region monitoring)",
)


# ==============================================================================
# Criteria Registry
# ==============================================================================

ALL_CRITERIA: dict[str, WCAGCriterion] = {
    "1.1.1": CRITERION_1_1_1,
    "1.3.1": CRITERION_1_3_1,
    "1.4.3": CRITERION_1_4_3,
    "2.1.1": CRITERION_2_1_1,
    "2.1.2": CRITERION_2_1_2,
    "2.4.1": CRITERION_2_4_1,
    "2.4.4": CRITERION_2_4_4,
    "2.4.6": CRITERION_2_4_6,
    "2.4.7": CRITERION_2_4_7,
    "2.5.3": CRITERION_2_5_3,
    "3.2.4": CRITERION_3_2_4,
    "3.3.2": CRITERION_3_3_2,
    "3.3.3": CRITERION_3_3_3,
    "4.1.2": CRITERION_4_1_2,
    "4.1.3": CRITERION_4_1_3,
}


def get_criterion(criterion_id: str) -> Optional[WCAGCriterion]:
    """Get WCAG criterion by ID"""
    return ALL_CRITERIA.get(criterion_id)


def get_criteria_by_level(level: WCAGLevel) -> list[WCAGCriterion]:
    """Get all criteria for a specific conformance level"""
    return [c for c in ALL_CRITERIA.values() if c.level == level]


def get_criteria_by_principle(principle: str) -> list[WCAGCriterion]:
    """Get all criteria for a specific principle"""
    return [c for c in ALL_CRITERIA.values() if c.principle == principle]


def get_testable_criteria() -> list[WCAGCriterion]:
    """
    Get criteria that can be tested via screen reader.

    Excludes criteria that require visual verification (e.g., contrast, focus visible).
    """
    excluded_ids = {
        "1.4.3",  # Contrast - requires visual analysis
        "2.4.7",  # Focus Visible - requires visual verification
        "2.5.3",  # Label in Name - requires visual comparison
        "4.1.3",  # Status Messages - complex, requires live region monitoring
    }
    return [c for c in ALL_CRITERIA.values() if c.criterion_id not in excluded_ids]


def get_severity_for_criterion(criterion_id: str) -> IssueSeverity:
    """
    Map WCAG criterion to issue severity.

    Severity is based on:
    - WCAG level (A is more critical than AA)
    - Impact on functionality (blocking vs. usability)
    - Commonality of the issue
    """
    # Critical: Complete blockers
    if criterion_id in ["2.1.2"]:  # Keyboard trap
        return IssueSeverity.CRITICAL

    # High: Major accessibility barriers
    if criterion_id in [
        "1.1.1",  # Missing alt text
        "2.1.1",  # Keyboard accessibility
        "3.3.2",  # Missing form labels
        "4.1.2",  # Missing name/role/value
    ]:
        return IssueSeverity.HIGH

    # Medium: Usability issues
    if criterion_id in [
        "1.3.1",  # Info and relationships
        "2.4.1",  # Skip links
        "2.4.4",  # Link purpose
        "2.4.6",  # Headings and labels
        "3.3.3",  # Error suggestions
    ]:
        return IssueSeverity.MEDIUM

    # Low: Minor issues
    return IssueSeverity.LOW
