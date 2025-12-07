"""
WCAG Validator

Orchestrates all issue detectors to perform comprehensive WCAG 2.1/2.2 validation.
Integrates with agent exploration data, correlation events, and NVDA output.
"""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

from src.wcag.issue_detector import (
    AccessibilityIssue,
    MissingAltTextDetector,
    MissingFormLabelDetector,
    KeyboardTrapDetector,
    MissingSkipLinkDetector,
    HeadingStructureDetector,
    InsufficientLinkTextDetector,
    IncompleteARIADetector,
)
from src.wcag.criteria_mapper import WCAGLevel, IssueSeverity, get_testable_criteria
from src.correlation.models import CorrelatedEvent
from src.agent.memory import VisitedElement, AgentMemory
from src.navigation.navigator import ElementType


class ValidationReport(BaseModel):
    """Complete WCAG validation report"""
    model_config = ConfigDict(use_enum_values=True)

    page_url: str = Field(..., description="URL of validated page")
    validation_date: datetime = Field(
        default_factory=datetime.now, description="When validation was performed"
    )
    total_issues: int = Field(0, description="Total issues found")
    issues_by_severity: dict[str, int] = Field(
        default_factory=dict, description="Count by severity"
    )
    issues_by_criterion: dict[str, int] = Field(
        default_factory=dict, description="Count by WCAG criterion"
    )
    issues: list[AccessibilityIssue] = Field(
        default_factory=list, description="All detected issues"
    )

    # Validation metadata
    elements_explored: int = Field(0, description="Number of elements explored")
    headings_found: int = Field(0, description="Number of headings found")
    links_found: int = Field(0, description="Number of links found")
    forms_found: int = Field(0, description="Number of form fields found")
    duration_seconds: Optional[float] = Field(
        None, description="Validation duration in seconds"
    )

    def get_summary(self) -> str:
        """Get text summary of validation results"""
        lines = [
            f"WCAG Validation Report: {self.page_url}",
            f"Date: {self.validation_date.strftime('%Y-%m-%d %H:%M:%S')}",
            f"",
            f"Total Issues Found: {self.total_issues}",
        ]

        if self.issues_by_severity:
            lines.append("")
            lines.append("Issues by Severity:")
            for severity in ["critical", "high", "medium", "low"]:
                count = self.issues_by_severity.get(severity, 0)
                if count > 0:
                    lines.append(f"  {severity.upper()}: {count}")

        if self.issues_by_criterion:
            lines.append("")
            lines.append("Issues by WCAG Criterion:")
            for criterion_id in sorted(self.issues_by_criterion.keys()):
                count = self.issues_by_criterion[criterion_id]
                lines.append(f"  {criterion_id}: {count}")

        lines.append("")
        lines.append(f"Elements Explored: {self.elements_explored}")
        lines.append(f"Headings: {self.headings_found}")
        lines.append(f"Links: {self.links_found}")
        lines.append(f"Forms: {self.forms_found}")

        if self.duration_seconds:
            lines.append(f"Duration: {self.duration_seconds:.2f}s")

        return "\n".join(lines)

    def get_critical_issues(self) -> list[AccessibilityIssue]:
        """Get only critical severity issues"""
        return [i for i in self.issues if i.severity == IssueSeverity.CRITICAL]

    def get_high_issues(self) -> list[AccessibilityIssue]:
        """Get only high severity issues"""
        return [i for i in self.issues if i.severity == IssueSeverity.HIGH]

    def get_issues_by_criterion(self, criterion_id: str) -> list[AccessibilityIssue]:
        """Get issues for a specific WCAG criterion"""
        return [i for i in self.issues if i.criterion.criterion_id == criterion_id]


class WCAGValidator:
    """
    Main WCAG validator that orchestrates all detectors.

    Analyzes agent exploration data and correlation events to detect
    accessibility violations.
    """

    def __init__(self, page_url: str):
        """
        Initialize validator.

        Args:
            page_url: URL of page being validated
        """
        self.page_url = page_url
        self.start_time: Optional[datetime] = None

        # Initialize all detectors
        self.detectors = {
            "1.1.1": MissingAltTextDetector(),
            "3.3.2": MissingFormLabelDetector(),
            "2.1.2": KeyboardTrapDetector(),
            "2.4.1": MissingSkipLinkDetector(),
            "2.4.6": HeadingStructureDetector(),
            "2.4.4": InsufficientLinkTextDetector(),
            "4.1.2": IncompleteARIADetector(),
        }

        self.all_issues: list[AccessibilityIssue] = []

    def validate(
        self,
        agent_memory: AgentMemory,
        correlation_events: list[CorrelatedEvent],
    ) -> ValidationReport:
        """
        Perform complete WCAG validation.

        Args:
            agent_memory: Agent memory with visited elements
            correlation_events: All correlation events from exploration

        Returns:
            Validation report with all detected issues
        """
        self.start_time = datetime.now()
        self.all_issues.clear()

        # Get exploration data
        visited_elements = agent_memory.get_all_elements()
        headings = self._filter_by_type(visited_elements, "heading")
        links = self._filter_by_type(visited_elements, "link")
        forms = self._filter_by_type(visited_elements, "edit", "combo box", "checkbox")

        # Run all detectors
        self._detect_missing_alt_text(correlation_events)
        self._detect_missing_form_labels(correlation_events)
        self._detect_keyboard_traps(visited_elements)
        self._detect_missing_skip_links(visited_elements)
        self._detect_heading_structure(headings)
        self._detect_insufficient_link_text(correlation_events)
        self._detect_incomplete_aria(correlation_events)

        # Build report
        duration = (datetime.now() - self.start_time).total_seconds()

        report = ValidationReport(
            page_url=self.page_url,
            total_issues=len(self.all_issues),
            issues=self.all_issues,
            elements_explored=len(visited_elements),
            headings_found=len(headings),
            links_found=len(links),
            forms_found=len(forms),
            duration_seconds=duration,
        )

        # Calculate statistics
        report.issues_by_severity = self._count_by_severity(self.all_issues)
        report.issues_by_criterion = self._count_by_criterion(self.all_issues)

        return report

    def _detect_missing_alt_text(self, events: list[CorrelatedEvent]):
        """Detect missing alt text from correlation events"""
        detector = self.detectors["1.1.1"]
        for event in events:
            issues = detector.detect_from_correlation(event, self.page_url)
            self.all_issues.extend(issues)

    def _detect_missing_form_labels(self, events: list[CorrelatedEvent]):
        """Detect missing form labels from correlation events"""
        detector = self.detectors["3.3.2"]
        for event in events:
            issues = detector.detect_from_correlation(event, self.page_url)
            self.all_issues.extend(issues)

    def _detect_keyboard_traps(self, visited_elements: list[VisitedElement]):
        """Detect keyboard traps from visited elements"""
        detector = self.detectors["2.1.2"]

        # Check each element for circular navigation
        for i, element in enumerate(visited_elements):
            if i < 5:  # Need some history to detect trap
                continue

            recent_history = visited_elements[max(0, i - 20) : i]
            issues = detector.detect(
                visited_elements=recent_history,
                current_element=element,
                circular_threshold=5,
                page_url=self.page_url,
            )
            self.all_issues.extend(issues)

    def _detect_missing_skip_links(self, visited_elements: list[VisitedElement]):
        """Detect missing skip links"""
        detector = self.detectors["2.4.1"]

        # Get first 10 interactive elements
        first_elements = visited_elements[:10]

        issues = detector.detect(
            first_interactive_elements=first_elements, page_url=self.page_url
        )
        self.all_issues.extend(issues)

    def _detect_heading_structure(self, headings: list[VisitedElement]):
        """Detect heading structure issues"""
        detector = self.detectors["2.4.6"]
        issues = detector.detect(headings=headings, page_url=self.page_url)
        self.all_issues.extend(issues)

    def _detect_insufficient_link_text(self, events: list[CorrelatedEvent]):
        """Detect insufficient link text from correlation events"""
        detector = self.detectors["2.4.4"]
        for event in events:
            issues = detector.detect_from_correlation(event, self.page_url)
            self.all_issues.extend(issues)

    def _detect_incomplete_aria(self, events: list[CorrelatedEvent]):
        """Detect incomplete ARIA usage from correlation events"""
        detector = self.detectors["4.1.2"]
        for event in events:
            issues = detector.detect_from_correlation(event, self.page_url)
            self.all_issues.extend(issues)

    def _filter_by_type(
        self, elements: list[VisitedElement], *keywords: str
    ) -> list[VisitedElement]:
        """Filter elements by NVDA output keywords"""
        filtered = []
        for element in elements:
            text_lower = element.nvda_text.lower()
            if any(keyword.lower() in text_lower for keyword in keywords):
                filtered.append(element)
        return filtered

    def _count_by_severity(
        self, issues: list[AccessibilityIssue]
    ) -> dict[str, int]:
        """Count issues by severity"""
        counts = {
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0,
        }
        for issue in issues:
            counts[issue.severity] += 1
        return counts

    def _count_by_criterion(
        self, issues: list[AccessibilityIssue]
    ) -> dict[str, int]:
        """Count issues by WCAG criterion"""
        counts: dict[str, int] = {}
        for issue in issues:
            criterion_id = issue.criterion.criterion_id
            counts[criterion_id] = counts.get(criterion_id, 0) + 1
        return counts

    def get_all_issues(self) -> list[AccessibilityIssue]:
        """Get all detected issues"""
        return self.all_issues

    def get_issues_by_severity(
        self, severity: IssueSeverity
    ) -> list[AccessibilityIssue]:
        """Get issues filtered by severity"""
        return [i for i in self.all_issues if i.severity == severity]

    def clear_issues(self):
        """Clear all detected issues"""
        self.all_issues.clear()
        for detector in self.detectors.values():
            detector.clear_issues()
