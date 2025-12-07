"""Tests for WCAG validator module."""

import pytest
from datetime import datetime

from src.wcag.validator import ValidationReport, WCAGValidator
from src.wcag.issue_detector import AccessibilityIssue
from src.wcag.criteria_mapper import (
    CRITERION_1_1_1,
    CRITERION_2_1_2,
    CRITERION_3_3_2,
    IssueSeverity,
)
from src.agent.memory import AgentMemory, VisitedElement
from src.correlation.models import CorrelatedEvent


class TestValidationReport:
    """Tests for ValidationReport model"""

    def test_create_empty_report(self):
        """Test creating an empty validation report"""
        report = ValidationReport(page_url="https://example.com")

        assert report.page_url == "https://example.com"
        assert report.total_issues == 0
        assert len(report.issues) == 0
        assert report.elements_explored == 0

    def test_create_report_with_issues(self):
        """Test creating report with issues"""
        issue = AccessibilityIssue(
            issue_id="test-1",
            criterion=CRITERION_1_1_1,
            severity=IssueSeverity.HIGH,
            title="Test",
            description="Test description"
        )
        report = ValidationReport(
            page_url="https://example.com",
            total_issues=1,
            issues=[issue],
            issues_by_severity={"high": 1},
            issues_by_criterion={"1.1.1": 1}
        )

        assert report.total_issues == 1
        assert len(report.issues) == 1
        assert report.issues[0] == issue

    def test_get_summary_empty_report(self):
        """Test get_summary with no issues"""
        report = ValidationReport(page_url="https://example.com")

        summary = report.get_summary()

        assert "https://example.com" in summary
        assert "Total Issues Found: 0" in summary
        assert "Elements Explored: 0" in summary

    def test_get_summary_with_issues(self):
        """Test get_summary with issues"""
        issue = AccessibilityIssue(
            issue_id="test-1",
            criterion=CRITERION_1_1_1,
            severity=IssueSeverity.HIGH,
            title="Test",
            description="Test"
        )
        report = ValidationReport(
            page_url="https://example.com",
            total_issues=1,
            issues=[issue],
            issues_by_severity={"high": 1},
            issues_by_criterion={"1.1.1": 1},
            elements_explored=10,
            headings_found=2,
            links_found=5,
            forms_found=1,
            duration_seconds=1.5
        )

        summary = report.get_summary()

        assert "Total Issues Found: 1" in summary
        assert "HIGH: 1" in summary
        assert "1.1.1: 1" in summary
        assert "Elements Explored: 10" in summary
        assert "Headings: 2" in summary
        assert "Links: 5" in summary
        assert "Forms: 1" in summary
        assert "Duration: 1.50s" in summary

    def test_get_critical_issues(self):
        """Test filtering critical issues"""
        critical = AccessibilityIssue(
            issue_id="test-1",
            criterion=CRITERION_2_1_2,
            severity=IssueSeverity.CRITICAL,
            title="Critical",
            description="Test"
        )
        high = AccessibilityIssue(
            issue_id="test-2",
            criterion=CRITERION_1_1_1,
            severity=IssueSeverity.HIGH,
            title="High",
            description="Test"
        )
        report = ValidationReport(
            page_url="https://example.com",
            total_issues=2,
            issues=[critical, high]
        )

        critical_issues = report.get_critical_issues()

        assert len(critical_issues) == 1
        assert critical_issues[0].severity == IssueSeverity.CRITICAL

    def test_get_high_issues(self):
        """Test filtering high severity issues"""
        high1 = AccessibilityIssue(
            issue_id="test-1",
            criterion=CRITERION_1_1_1,
            severity=IssueSeverity.HIGH,
            title="High 1",
            description="Test"
        )
        high2 = AccessibilityIssue(
            issue_id="test-2",
            criterion=CRITERION_3_3_2,
            severity=IssueSeverity.HIGH,
            title="High 2",
            description="Test"
        )
        medium = AccessibilityIssue(
            issue_id="test-3",
            criterion=CRITERION_1_1_1,
            severity=IssueSeverity.MEDIUM,
            title="Medium",
            description="Test"
        )
        report = ValidationReport(
            page_url="https://example.com",
            total_issues=3,
            issues=[high1, high2, medium]
        )

        high_issues = report.get_high_issues()

        assert len(high_issues) == 2
        assert all(i.severity == IssueSeverity.HIGH for i in high_issues)

    def test_get_issues_by_criterion(self):
        """Test filtering issues by criterion"""
        issue1 = AccessibilityIssue(
            issue_id="test-1",
            criterion=CRITERION_1_1_1,
            severity=IssueSeverity.HIGH,
            title="Alt 1",
            description="Test"
        )
        issue2 = AccessibilityIssue(
            issue_id="test-2",
            criterion=CRITERION_1_1_1,
            severity=IssueSeverity.HIGH,
            title="Alt 2",
            description="Test"
        )
        issue3 = AccessibilityIssue(
            issue_id="test-3",
            criterion=CRITERION_3_3_2,
            severity=IssueSeverity.HIGH,
            title="Label",
            description="Test"
        )
        report = ValidationReport(
            page_url="https://example.com",
            total_issues=3,
            issues=[issue1, issue2, issue3]
        )

        alt_issues = report.get_issues_by_criterion("1.1.1")
        label_issues = report.get_issues_by_criterion("3.3.2")

        assert len(alt_issues) == 2
        assert len(label_issues) == 1
        assert all(i.criterion.criterion_id == "1.1.1" for i in alt_issues)


class TestWCAGValidatorInitialization:
    """Tests for WCAGValidator initialization"""

    def test_create_validator(self):
        """Test creating a validator"""
        validator = WCAGValidator(page_url="https://example.com")

        assert validator.page_url == "https://example.com"
        assert len(validator.detectors) == 7
        assert "1.1.1" in validator.detectors
        assert "2.1.2" in validator.detectors
        assert "3.3.2" in validator.detectors

    def test_all_detectors_initialized(self):
        """Test that all expected detectors are present"""
        validator = WCAGValidator(page_url="https://example.com")

        expected_criteria = ["1.1.1", "3.3.2", "2.1.2", "2.4.1", "2.4.6", "2.4.4", "4.1.2"]

        for criterion_id in expected_criteria:
            assert criterion_id in validator.detectors

    def test_initial_state(self):
        """Test validator initial state"""
        validator = WCAGValidator(page_url="https://example.com")

        assert validator.start_time is None
        assert len(validator.all_issues) == 0


class TestWCAGValidatorHelperMethods:
    """Tests for validator helper methods"""

    def test_filter_by_type_headings(self):
        """Test filtering elements by type - headings"""
        validator = WCAGValidator(page_url="https://example.com")
        elements = [
            VisitedElement(
                nvda_text="Heading level 1 Main Title",
                key_used="h",
                element_id="h1",
                is_interactive=False
            ),
            VisitedElement(
                nvda_text="Link Home",
                key_used="Tab",
                element_id="link1",
                is_interactive=True
            ),
            VisitedElement(
                nvda_text="Heading level 2 Subtitle",
                key_used="h",
                element_id="h2",
                is_interactive=False
            ),
        ]

        headings = validator._filter_by_type(elements, "heading")

        assert len(headings) == 2
        assert "heading" in headings[0].nvda_text.lower()
        assert "heading" in headings[1].nvda_text.lower()

    def test_filter_by_type_links(self):
        """Test filtering elements by type - links"""
        validator = WCAGValidator(page_url="https://example.com")
        elements = [
            VisitedElement(
                nvda_text="Link Home",
                key_used="Tab",
                element_id="link1",
                is_interactive=True
            ),
            VisitedElement(
                nvda_text="Button Submit",
                key_used="Tab",
                element_id="btn1",
                is_interactive=True
            ),
            VisitedElement(
                nvda_text="Link About Us",
                key_used="k",
                element_id="link2",
                is_interactive=True
            ),
        ]

        links = validator._filter_by_type(elements, "link")

        assert len(links) == 2
        assert all("link" in e.nvda_text.lower() for e in links)

    def test_filter_by_type_forms(self):
        """Test filtering elements by type - forms"""
        validator = WCAGValidator(page_url="https://example.com")
        elements = [
            VisitedElement(
                nvda_text="Edit Email",
                key_used="Tab",
                element_id="input1",
                is_interactive=True
            ),
            VisitedElement(
                nvda_text="Combo box Country",
                key_used="Tab",
                element_id="select1",
                is_interactive=True
            ),
            VisitedElement(
                nvda_text="Checkbox Subscribe",
                key_used="Tab",
                element_id="check1",
                is_interactive=True
            ),
            VisitedElement(
                nvda_text="Link Home",
                key_used="Tab",
                element_id="link1",
                is_interactive=True
            ),
        ]

        forms = validator._filter_by_type(elements, "edit", "combo box", "checkbox")

        assert len(forms) == 3

    def test_count_by_severity(self):
        """Test counting issues by severity"""
        validator = WCAGValidator(page_url="https://example.com")
        issues = [
            AccessibilityIssue(
                issue_id="1",
                criterion=CRITERION_2_1_2,
                severity=IssueSeverity.CRITICAL,
                title="C1",
                description="Test"
            ),
            AccessibilityIssue(
                issue_id="2",
                criterion=CRITERION_1_1_1,
                severity=IssueSeverity.HIGH,
                title="H1",
                description="Test"
            ),
            AccessibilityIssue(
                issue_id="3",
                criterion=CRITERION_1_1_1,
                severity=IssueSeverity.HIGH,
                title="H2",
                description="Test"
            ),
            AccessibilityIssue(
                issue_id="4",
                criterion=CRITERION_1_1_1,
                severity=IssueSeverity.MEDIUM,
                title="M1",
                description="Test"
            ),
        ]

        counts = validator._count_by_severity(issues)

        assert counts["critical"] == 1
        assert counts["high"] == 2
        assert counts["medium"] == 1
        assert counts["low"] == 0

    def test_count_by_criterion(self):
        """Test counting issues by criterion"""
        validator = WCAGValidator(page_url="https://example.com")
        issues = [
            AccessibilityIssue(
                issue_id="1",
                criterion=CRITERION_1_1_1,
                severity=IssueSeverity.HIGH,
                title="Alt 1",
                description="Test"
            ),
            AccessibilityIssue(
                issue_id="2",
                criterion=CRITERION_1_1_1,
                severity=IssueSeverity.HIGH,
                title="Alt 2",
                description="Test"
            ),
            AccessibilityIssue(
                issue_id="3",
                criterion=CRITERION_3_3_2,
                severity=IssueSeverity.HIGH,
                title="Label",
                description="Test"
            ),
        ]

        counts = validator._count_by_criterion(issues)

        assert counts["1.1.1"] == 2
        assert counts["3.3.2"] == 1


class TestWCAGValidatorValidate:
    """Tests for validate method"""

    def test_validate_empty_memory(self):
        """Test validation with empty agent memory"""
        validator = WCAGValidator(page_url="https://example.com")
        memory = AgentMemory()
        events = []

        report = validator.validate(memory, events)

        assert report.page_url == "https://example.com"
        assert report.total_issues >= 0
        assert report.elements_explored == 0
        assert report.headings_found == 0
        assert report.links_found == 0
        assert report.forms_found == 0
        assert report.duration_seconds is not None

    def test_validate_with_elements(self):
        """Test validation with visited elements"""
        validator = WCAGValidator(page_url="https://example.com")
        memory = AgentMemory()

        # Add some elements
        memory.add_element(
            nvda_text="Heading level 1 Home",
            key_used="h",
            element_id="h1",
            is_interactive=False
        )
        memory.add_element(
            nvda_text="Link About",
            key_used="Tab",
            element_id="link1",
            is_interactive=True
        )
        memory.add_element(
            nvda_text="Edit Email unlabeled",
            key_used="Tab",
            element_id="input1",
            is_interactive=True
        )

        events = []

        report = validator.validate(memory, events)

        assert report.elements_explored == 3
        assert report.headings_found == 1
        assert report.links_found == 1
        assert report.forms_found == 1

    def test_validate_clears_previous_issues(self):
        """Test that validate clears previous issues"""
        validator = WCAGValidator(page_url="https://example.com")
        memory = AgentMemory()

        # First validation
        report1 = validator.validate(memory, [])
        issues_count_1 = report1.total_issues

        # Second validation
        report2 = validator.validate(memory, [])

        # Should not accumulate issues from previous run
        assert report2.total_issues == issues_count_1

    def test_get_all_issues(self):
        """Test getting all detected issues"""
        validator = WCAGValidator(page_url="https://example.com")
        memory = AgentMemory()

        validator.validate(memory, [])
        issues = validator.get_all_issues()

        assert isinstance(issues, list)

    def test_get_issues_by_severity(self):
        """Test filtering issues by severity"""
        validator = WCAGValidator(page_url="https://example.com")
        memory = AgentMemory()

        validator.validate(memory, [])

        critical = validator.get_issues_by_severity(IssueSeverity.CRITICAL)
        high = validator.get_issues_by_severity(IssueSeverity.HIGH)

        assert isinstance(critical, list)
        assert isinstance(high, list)

    def test_clear_issues(self):
        """Test clearing issues"""
        validator = WCAGValidator(page_url="https://example.com")
        memory = AgentMemory()

        validator.validate(memory, [])
        validator.clear_issues()

        assert len(validator.all_issues) == 0
