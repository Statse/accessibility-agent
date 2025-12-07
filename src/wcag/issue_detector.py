"""
WCAG Issue Detector

Implements detection logic for various WCAG violations based on NVDA output,
keyboard navigation patterns, and agent exploration data.
"""

import re
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field

from src.wcag.criteria_mapper import (
    WCAGCriterion,
    IssueSeverity,
    get_criterion,
    get_severity_for_criterion,
)
from src.correlation.models import CorrelatedEvent
from src.agent.memory import VisitedElement
from src.navigation.navigator import ElementType


class AccessibilityIssue(BaseModel):
    """Detected accessibility issue"""
    model_config = ConfigDict(use_enum_values=True)

    issue_id: str = Field(..., description="Unique issue identifier")
    criterion: WCAGCriterion = Field(..., description="Violated WCAG criterion")
    severity: IssueSeverity = Field(..., description="Issue severity")
    title: str = Field(..., description="Short issue title")
    description: str = Field(..., description="Detailed issue description")
    detected_at: datetime = Field(
        default_factory=datetime.now, description="When issue was detected"
    )

    # Evidence
    nvda_output: Optional[str] = Field(
        None, description="NVDA output at time of detection"
    )
    keyboard_sequence: Optional[list[str]] = Field(
        None, description="Keyboard actions leading to issue"
    )
    element_context: Optional[str] = Field(
        None, description="Context about the element (URL, page section, etc.)"
    )
    expected_behavior: Optional[str] = Field(
        None, description="What should have happened"
    )
    recommendation: Optional[str] = Field(
        None, description="How to fix this issue"
    )

    # Metadata
    page_url: Optional[str] = Field(None, description="URL where issue was found")
    timestamp_ms: Optional[float] = Field(
        None, description="Timestamp from correlation event"
    )

    def get_summary(self) -> str:
        """Get one-line summary of the issue"""
        return f"[{self.severity.upper()}] {self.criterion.criterion_id} - {self.title}"


class IssueDetector(ABC):
    """Base class for all WCAG issue detectors"""

    def __init__(self, criterion_id: str):
        """
        Initialize detector.

        Args:
            criterion_id: WCAG criterion ID (e.g., "1.1.1")
        """
        self.criterion_id = criterion_id
        self.criterion = get_criterion(criterion_id)
        if not self.criterion:
            raise ValueError(f"Unknown WCAG criterion: {criterion_id}")

        self.severity = get_severity_for_criterion(criterion_id)
        self.issues_found: list[AccessibilityIssue] = []

    @abstractmethod
    def detect(self, **kwargs) -> list[AccessibilityIssue]:
        """
        Detect violations of this WCAG criterion.

        Returns:
            List of detected issues (empty if none found)
        """
        pass

    def _create_issue(
        self,
        title: str,
        description: str,
        nvda_output: Optional[str] = None,
        keyboard_sequence: Optional[list[str]] = None,
        element_context: Optional[str] = None,
        expected_behavior: Optional[str] = None,
        recommendation: Optional[str] = None,
        page_url: Optional[str] = None,
    ) -> AccessibilityIssue:
        """Helper to create an AccessibilityIssue"""
        import uuid

        issue = AccessibilityIssue(
            issue_id=str(uuid.uuid4()),
            criterion=self.criterion,
            severity=self.severity,
            title=title,
            description=description,
            nvda_output=nvda_output,
            keyboard_sequence=keyboard_sequence,
            element_context=element_context,
            expected_behavior=expected_behavior,
            recommendation=recommendation,
            page_url=page_url,
        )
        self.issues_found.append(issue)
        return issue

    def get_all_issues(self) -> list[AccessibilityIssue]:
        """Get all issues found by this detector"""
        return self.issues_found

    def clear_issues(self):
        """Clear all detected issues"""
        self.issues_found.clear()


# ==============================================================================
# 1.1.1: Non-text Content (Missing Alt Text)
# ==============================================================================


class MissingAltTextDetector(IssueDetector):
    """Detects images without alt text (WCAG 1.1.1)"""

    def __init__(self):
        super().__init__("1.1.1")

    def detect(
        self,
        nvda_output: str,
        element_context: Optional[str] = None,
        keyboard_sequence: Optional[list[str]] = None,
        page_url: Optional[str] = None,
    ) -> list[AccessibilityIssue]:
        """
        Detect missing alt text on images.

        Detection patterns:
        - NVDA announces "unlabeled graphic"
        - NVDA announces "graphic" with no descriptive text
        - NVDA is silent when encountering an image (requires correlation timeout)
        """
        issues = []
        nvda_lower = nvda_output.lower()

        # Pattern 1: Explicitly unlabeled
        if "unlabeled graphic" in nvda_lower or "unlabelled graphic" in nvda_lower:
            issues.append(
                self._create_issue(
                    title="Image missing alt text (unlabeled graphic)",
                    description="NVDA announced 'unlabeled graphic', indicating the image has no alt attribute or empty alt text.",
                    nvda_output=nvda_output,
                    keyboard_sequence=keyboard_sequence,
                    element_context=element_context,
                    expected_behavior="Image should have descriptive alt text that conveys its purpose",
                    recommendation="Add alt attribute with descriptive text. For decorative images, use alt=\"\"",
                    page_url=page_url,
                )
            )

        # Pattern 2: Generic "graphic" with no description
        elif re.search(r"\bgraphic\b", nvda_lower) and not re.search(
            r"\bgraphic\s+\w+", nvda_lower
        ):
            # "graphic" alone is suspicious, but could be intentional
            # Only flag if it seems to be the only content
            if len(nvda_output.strip().split()) <= 2:
                issues.append(
                    self._create_issue(
                        title="Image with insufficient alt text",
                        description="NVDA announced 'graphic' with minimal or no descriptive text.",
                        nvda_output=nvda_output,
                        keyboard_sequence=keyboard_sequence,
                        element_context=element_context,
                        expected_behavior="Image should have descriptive alt text",
                        recommendation="Ensure alt text describes the image content and purpose",
                        page_url=page_url,
                    )
                )

        return issues

    def detect_from_correlation(
        self, event: CorrelatedEvent, page_url: Optional[str] = None
    ) -> list[AccessibilityIssue]:
        """Detect missing alt text from a correlated event"""
        if not event.output:
            # Timeout with no NVDA output could indicate missing alt text
            # But we need more context to be sure (could be other issues)
            return []

        return self.detect(
            nvda_output=event.output.text,
            keyboard_sequence=[event.action.key],
            page_url=page_url,
        )


# ==============================================================================
# 3.3.2 / 1.3.1: Labels or Instructions (Missing Form Labels)
# ==============================================================================


class MissingFormLabelDetector(IssueDetector):
    """Detects form fields without labels (WCAG 3.3.2, 1.3.1)"""

    def __init__(self):
        super().__init__("3.3.2")

    def detect(
        self,
        nvda_output: str,
        element_context: Optional[str] = None,
        keyboard_sequence: Optional[list[str]] = None,
        page_url: Optional[str] = None,
    ) -> list[AccessibilityIssue]:
        """
        Detect missing form labels.

        Detection patterns:
        - NVDA announces "edit" with no label
        - NVDA announces "edit unlabeled"
        - NVDA announces form field types without descriptive labels
        """
        issues = []
        nvda_lower = nvda_output.lower()

        # Pattern 1: Explicit "unlabeled"
        if "unlabeled" in nvda_lower or "unlabelled" in nvda_lower:
            if any(
                field_type in nvda_lower
                for field_type in ["edit", "combo box", "checkbox", "radio"]
            ):
                issues.append(
                    self._create_issue(
                        title="Form field missing label",
                        description=f"NVDA announced unlabeled form field: '{nvda_output}'",
                        nvda_output=nvda_output,
                        keyboard_sequence=keyboard_sequence,
                        element_context=element_context,
                        expected_behavior="Form field should have an associated label describing its purpose",
                        recommendation="Add <label> element or aria-label attribute to form field",
                        page_url=page_url,
                    )
                )

        # Pattern 2: Generic field type only (e.g., "edit" alone)
        elif re.match(r"^\s*(edit|combo box|combobox)\s*$", nvda_lower):
            issues.append(
                self._create_issue(
                    title="Form field with missing or generic label",
                    description=f"NVDA announced only field type with no descriptive label: '{nvda_output}'",
                    nvda_output=nvda_output,
                    keyboard_sequence=keyboard_sequence,
                    element_context=element_context,
                    expected_behavior="Form field should have descriptive label",
                    recommendation="Add label that describes what input is expected",
                    page_url=page_url,
                )
            )

        return issues

    def detect_from_correlation(
        self, event: CorrelatedEvent, page_url: Optional[str] = None
    ) -> list[AccessibilityIssue]:
        """Detect missing form labels from a correlated event"""
        if not event.output:
            return []

        return self.detect(
            nvda_output=event.output.text,
            keyboard_sequence=[event.action.key],
            page_url=page_url,
        )


# ==============================================================================
# 2.1.2: No Keyboard Trap
# ==============================================================================


class KeyboardTrapDetector(IssueDetector):
    """Detects keyboard traps (WCAG 2.1.2)"""

    def __init__(self):
        super().__init__("2.1.2")

    def detect(
        self,
        visited_elements: list[VisitedElement],
        current_element: VisitedElement,
        circular_threshold: int = 5,
        page_url: Optional[str] = None,
    ) -> list[AccessibilityIssue]:
        """
        Detect keyboard traps by analyzing circular navigation patterns.

        Args:
            visited_elements: List of recently visited elements
            current_element: Current element
            circular_threshold: How many times to see same element before flagging
            page_url: URL of the page

        Returns:
            List of issues found
        """
        issues = []

        # Count occurrences of current element in recent history
        if len(visited_elements) < circular_threshold:
            return issues

        current_hash = current_element.element_id
        recent_window = visited_elements[-circular_threshold * 2 :]

        # Count how many times we've seen this element
        occurrences = sum(
            1 for elem in recent_window if elem.element_id == current_hash
        )

        # If we've seen it multiple times in a short window, likely a trap
        if occurrences >= circular_threshold:
            # Build keyboard sequence from recent actions
            keyboard_sequence = [elem.key_used for elem in recent_window[-10:]]

            issues.append(
                self._create_issue(
                    title="Keyboard trap detected",
                    description=f"Agent is stuck in circular navigation. Element '{current_element.nvda_text}' "
                    f"has been visited {occurrences} times in recent navigation.",
                    nvda_output=current_element.nvda_text,
                    keyboard_sequence=keyboard_sequence,
                    element_context=f"Element repeated {occurrences} times",
                    expected_behavior="User should be able to navigate away from element using only keyboard",
                    recommendation="Ensure all interactive elements have proper keyboard navigation. "
                    "Check for JavaScript that captures keyboard events without allowing escape.",
                    page_url=page_url,
                )
            )

        return issues


# ==============================================================================
# 2.4.1: Bypass Blocks (Skip Links)
# ==============================================================================


class MissingSkipLinkDetector(IssueDetector):
    """Detects missing skip navigation links (WCAG 2.4.1)"""

    def __init__(self):
        super().__init__("2.4.1")

    def detect(
        self,
        first_interactive_elements: list[VisitedElement],
        page_url: Optional[str] = None,
    ) -> list[AccessibilityIssue]:
        """
        Detect missing skip links.

        Args:
            first_interactive_elements: First 5-10 interactive elements on page
            page_url: URL of the page

        Returns:
            List of issues found
        """
        issues = []

        # Check if any of the first few elements are skip links
        has_skip_link = any(
            self._is_skip_link(elem.nvda_text) for elem in first_interactive_elements[:5]
        )

        if not has_skip_link:
            issues.append(
                self._create_issue(
                    title="Missing skip navigation link",
                    description="No skip link found at the beginning of the page. Users must Tab through "
                    "all navigation items to reach main content.",
                    nvda_output=", ".join(
                        elem.nvda_text for elem in first_interactive_elements[:3]
                    ),
                    keyboard_sequence=["Tab"] * min(5, len(first_interactive_elements)),
                    element_context="First 5 interactive elements checked",
                    expected_behavior="Page should have a skip link as first or second interactive element",
                    recommendation="Add a skip navigation link (e.g., 'Skip to main content') as first focusable element",
                    page_url=page_url,
                )
            )

        return issues

    def _is_skip_link(self, nvda_text: str) -> bool:
        """Check if NVDA text indicates a skip link"""
        skip_patterns = [
            "skip",
            "jump to",
            "skip to main",
            "skip navigation",
            "skip to content",
        ]
        text_lower = nvda_text.lower()
        return any(pattern in text_lower for pattern in skip_patterns)


# ==============================================================================
# 2.4.6: Headings and Labels (Poor Heading Structure)
# ==============================================================================


class HeadingStructureDetector(IssueDetector):
    """Detects poor heading hierarchy (WCAG 2.4.6)"""

    def __init__(self):
        super().__init__("2.4.6")

    def detect(
        self, headings: list[VisitedElement], page_url: Optional[str] = None
    ) -> list[AccessibilityIssue]:
        """
        Detect heading structure issues.

        Args:
            headings: List of headings found during exploration
            page_url: URL of the page

        Returns:
            List of issues found
        """
        issues = []

        if not headings:
            issues.append(
                self._create_issue(
                    title="No headings found on page",
                    description="Page has no headings, making it difficult for screen reader users to navigate and understand page structure.",
                    expected_behavior="Page should have logical heading structure (H1 for title, H2 for sections, etc.)",
                    recommendation="Add semantic heading elements (<h1>, <h2>, etc.) to structure content",
                    page_url=page_url,
                )
            )
            return issues

        # Extract heading levels from NVDA output
        heading_levels = self._extract_heading_levels(headings)

        # Check for missing H1
        if 1 not in heading_levels:
            issues.append(
                self._create_issue(
                    title="Missing H1 heading",
                    description="Page has no H1 heading. Every page should have exactly one H1 as the main title.",
                    nvda_output=", ".join(h.nvda_text for h in headings[:3]),
                    keyboard_sequence=["H"] * len(headings),
                    expected_behavior="Page should have one H1 heading as main title",
                    recommendation="Add an H1 element for the page title",
                    page_url=page_url,
                )
            )

        # Check for skipped heading levels
        if heading_levels:
            sorted_levels = sorted(heading_levels)
            for i in range(len(sorted_levels) - 1):
                current = sorted_levels[i]
                next_level = sorted_levels[i + 1]
                if next_level - current > 1:
                    issues.append(
                        self._create_issue(
                            title=f"Skipped heading level: H{current} → H{next_level}",
                            description=f"Heading hierarchy jumps from H{current} to H{next_level}, "
                            f"skipping H{current + 1}. This breaks logical document structure.",
                            nvda_output=", ".join(h.nvda_text for h in headings),
                            keyboard_sequence=["H"] * len(headings),
                            expected_behavior="Headings should not skip levels (e.g., H1 → H2 → H3)",
                            recommendation=f"Add H{current + 1} heading(s) or adjust hierarchy",
                            page_url=page_url,
                        )
                    )

        return issues

    def _extract_heading_levels(self, headings: list[VisitedElement]) -> list[int]:
        """Extract heading levels from NVDA output"""
        levels = []
        for heading in headings:
            # NVDA typically announces headings as "heading level 1", "heading level 2", etc.
            match = re.search(r"heading\s+level\s+(\d+)", heading.nvda_text.lower())
            if match:
                levels.append(int(match.group(1)))
            # Alternative format: "h1", "h2", etc.
            else:
                match = re.search(r"\bh(\d+)\b", heading.nvda_text.lower())
                if match:
                    levels.append(int(match.group(1)))

        return levels


# ==============================================================================
# 2.4.4: Link Purpose (Insufficient Link Text)
# ==============================================================================


class InsufficientLinkTextDetector(IssueDetector):
    """Detects poor link text (WCAG 2.4.4)"""

    def __init__(self):
        super().__init__("2.4.4")
        self.poor_link_texts = {
            "click here",
            "read more",
            "more",
            "link",
            "here",
            "click",
            "learn more",
            "continue",
            "go",
        }

    def detect(
        self,
        nvda_output: str,
        element_context: Optional[str] = None,
        keyboard_sequence: Optional[list[str]] = None,
        page_url: Optional[str] = None,
    ) -> list[AccessibilityIssue]:
        """
        Detect insufficient link text.

        Detection patterns:
        - NVDA announces "link" with no text
        - NVDA announces link with generic text like "click here"
        """
        issues = []
        nvda_lower = nvda_output.lower()

        # Must be a link
        if "link" not in nvda_lower:
            return issues

        # Pattern 1: Link with no text
        if re.match(r"^\s*link\s*$", nvda_lower):
            issues.append(
                self._create_issue(
                    title="Link missing text",
                    description="NVDA announced 'link' with no descriptive text.",
                    nvda_output=nvda_output,
                    keyboard_sequence=keyboard_sequence,
                    element_context=element_context,
                    expected_behavior="Link should have descriptive text indicating its purpose/destination",
                    recommendation="Add descriptive text to link or use aria-label",
                    page_url=page_url,
                )
            )

        # Pattern 2: Generic link text
        else:
            # Extract link text (remove "link" from announcement)
            link_text = re.sub(r"\blink\b", "", nvda_lower).strip()
            if link_text in self.poor_link_texts:
                issues.append(
                    self._create_issue(
                        title=f"Generic link text: '{link_text}'",
                        description=f"Link uses generic text '{link_text}' which doesn't describe the destination.",
                        nvda_output=nvda_output,
                        keyboard_sequence=keyboard_sequence,
                        element_context=element_context,
                        expected_behavior="Link text should describe where the link goes",
                        recommendation=f"Replace '{link_text}' with descriptive text about the destination",
                        page_url=page_url,
                    )
                )

        return issues

    def detect_from_correlation(
        self, event: CorrelatedEvent, page_url: Optional[str] = None
    ) -> list[AccessibilityIssue]:
        """Detect insufficient link text from a correlated event"""
        if not event.output:
            return []

        return self.detect(
            nvda_output=event.output.text,
            keyboard_sequence=[event.action.key],
            page_url=page_url,
        )


# ==============================================================================
# 4.1.2: Name, Role, Value (Incomplete ARIA)
# ==============================================================================


class IncompleteARIADetector(IssueDetector):
    """Detects incomplete ARIA usage (WCAG 4.1.2)"""

    def __init__(self):
        super().__init__("4.1.2")

    def detect(
        self,
        nvda_output: str,
        element_context: Optional[str] = None,
        keyboard_sequence: Optional[list[str]] = None,
        page_url: Optional[str] = None,
    ) -> list[AccessibilityIssue]:
        """
        Detect incomplete ARIA usage.

        Detection patterns:
        - NVDA announces "clickable" (generic role, no semantic meaning)
        - NVDA cannot determine element role
        - NVDA is silent on interactive element
        """
        issues = []
        nvda_lower = nvda_output.lower()

        # Pattern 1: Generic "clickable"
        if "clickable" in nvda_lower and "button" not in nvda_lower:
            issues.append(
                self._create_issue(
                    title="Generic 'clickable' role instead of semantic button",
                    description="NVDA announced 'clickable' instead of 'button'. Element lacks proper ARIA role.",
                    nvda_output=nvda_output,
                    keyboard_sequence=keyboard_sequence,
                    element_context=element_context,
                    expected_behavior="Interactive elements should have semantic roles (button, link, etc.)",
                    recommendation="Use <button> element or add role='button' with proper ARIA attributes",
                    page_url=page_url,
                )
            )

        # Pattern 2: Unknown/unclear role
        elif re.search(r"\bunknown\b|\bunidentified\b", nvda_lower):
            issues.append(
                self._create_issue(
                    title="Element with unknown/unclear role",
                    description=f"NVDA could not determine element role: '{nvda_output}'",
                    nvda_output=nvda_output,
                    keyboard_sequence=keyboard_sequence,
                    element_context=element_context,
                    expected_behavior="All UI components should have programmatically determinable roles",
                    recommendation="Add appropriate ARIA role or use semantic HTML elements",
                    page_url=page_url,
                )
            )

        return issues

    def detect_from_correlation(
        self, event: CorrelatedEvent, page_url: Optional[str] = None
    ) -> list[AccessibilityIssue]:
        """Detect incomplete ARIA from a correlated event"""
        # Check for timeout (no NVDA output on interactive element)
        if not event.output:
            issues = []
            issues.append(
                self._create_issue(
                    title="No NVDA output on interactive element",
                    description="NVDA was silent when navigating to this element, indicating it may lack proper name/role/value.",
                    keyboard_sequence=[event.action.key],
                    expected_behavior="NVDA should announce element name and role",
                    recommendation="Ensure element has accessible name (aria-label, alt, or text content) and proper role",
                    page_url=page_url,
                )
            )
            return issues

        return self.detect(
            nvda_output=event.output.text,
            keyboard_sequence=[event.action.key],
            page_url=page_url,
        )
