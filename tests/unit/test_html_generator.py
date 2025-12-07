"""Tests for HTML report generator module."""

import pytest
import tempfile
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch

from src.reporting.html_generator import HTMLGenerator
from src.wcag.validator import ValidationReport
from src.wcag.issue_detector import AccessibilityIssue
from src.wcag.criteria_mapper import (
    WCAGCriterion,
    WCAGLevel,
    WCAGVersion,
    IssueSeverity,
    CRITERION_1_1_1,
    CRITERION_2_1_2,
    CRITERION_2_4_4,
    CRITERION_3_3_2,
)


class TestHTMLGeneratorInitialization:
    """Tests for HTMLGenerator initialization"""

    def test_create_with_default_template_dir(self):
        """Test creating generator with default template directory"""
        generator = HTMLGenerator()

        assert generator.template_dir is not None
        assert "templates" in generator.template_dir
        assert generator.env is not None

    def test_create_with_custom_template_dir(self, tmp_path):
        """Test creating generator with custom template directory"""
        template_dir = str(tmp_path / "custom_templates")
        Path(template_dir).mkdir(parents=True, exist_ok=True)

        generator = HTMLGenerator(template_dir=template_dir)

        assert generator.template_dir == template_dir

    def test_custom_filters_registered(self):
        """Test that custom Jinja2 filters are registered"""
        generator = HTMLGenerator()

        assert "format_datetime" in generator.env.filters
        assert "severity_badge_class" in generator.env.filters
        assert "level_badge_class" in generator.env.filters

    def test_autoescape_enabled(self):
        """Test that autoescape is enabled for security"""
        generator = HTMLGenerator()

        assert generator.env.autoescape is True

    def test_trim_blocks_enabled(self):
        """Test that trim_blocks is enabled"""
        generator = HTMLGenerator()

        assert generator.env.trim_blocks is True


class TestFormatDateTime:
    """Tests for _format_datetime static method"""

    def test_format_datetime_basic(self):
        """Test formatting a datetime object"""
        dt = datetime(2025, 12, 6, 14, 30, 45)

        result = HTMLGenerator._format_datetime(dt)

        assert result == "2025-12-06 14:30:45"

    def test_format_datetime_midnight(self):
        """Test formatting datetime at midnight"""
        dt = datetime(2025, 1, 1, 0, 0, 0)

        result = HTMLGenerator._format_datetime(dt)

        assert result == "2025-01-01 00:00:00"

    def test_format_datetime_single_digit_values(self):
        """Test formatting with single-digit month/day/time"""
        dt = datetime(2025, 3, 5, 9, 8, 7)

        result = HTMLGenerator._format_datetime(dt)

        assert result == "2025-03-05 09:08:07"


class TestSeverityBadgeClass:
    """Tests for _severity_badge_class static method"""

    def test_critical_severity(self):
        """Test CSS class for critical severity"""
        result = HTMLGenerator._severity_badge_class("critical")

        assert result == "badge-critical"

    def test_high_severity(self):
        """Test CSS class for high severity"""
        result = HTMLGenerator._severity_badge_class("high")

        assert result == "badge-high"

    def test_medium_severity(self):
        """Test CSS class for medium severity"""
        result = HTMLGenerator._severity_badge_class("medium")

        assert result == "badge-medium"

    def test_low_severity(self):
        """Test CSS class for low severity"""
        result = HTMLGenerator._severity_badge_class("low")

        assert result == "badge-low"

    def test_case_insensitive(self):
        """Test that severity matching is case-insensitive"""
        assert HTMLGenerator._severity_badge_class("CRITICAL") == "badge-critical"
        assert HTMLGenerator._severity_badge_class("High") == "badge-high"
        assert HTMLGenerator._severity_badge_class("MeDiUm") == "badge-medium"

    def test_unknown_severity(self):
        """Test unknown severity returns default"""
        result = HTMLGenerator._severity_badge_class("unknown")

        assert result == "badge-default"


class TestLevelBadgeClass:
    """Tests for _level_badge_class static method"""

    def test_level_a(self):
        """Test CSS class for Level A"""
        result = HTMLGenerator._level_badge_class("A")

        assert result == "badge-level-a"

    def test_level_aa(self):
        """Test CSS class for Level AA"""
        result = HTMLGenerator._level_badge_class("AA")

        assert result == "badge-level-aa"

    def test_level_aaa(self):
        """Test CSS class for Level AAA"""
        result = HTMLGenerator._level_badge_class("AAA")

        assert result == "badge-level-aaa"

    def test_unknown_level(self):
        """Test unknown level returns default"""
        result = HTMLGenerator._level_badge_class("B")

        assert result == "badge-default"


class TestCalculatePassFail:
    """Tests for _calculate_pass_fail method"""

    def test_all_levels_pass_no_issues(self):
        """Test all levels pass when no issues"""
        generator = HTMLGenerator()
        report = ValidationReport(
            page_url="https://example.com",
            total_issues=0,
            issues_by_severity={},
            issues_by_criterion={},
            issues=[]
        )

        result = generator._calculate_pass_fail(report)

        assert result["level_a_pass"] is True
        assert result["level_aa_pass"] is True
        assert result["level_aaa_pass"] is True
        assert result["total_criteria_tested"] == 0

    def test_level_a_fail_with_level_a_issue(self):
        """Test Level A fails when Level A issue present"""
        generator = HTMLGenerator()
        issue = AccessibilityIssue(
            issue_id="test-1",
            criterion=CRITERION_1_1_1,  # Level A
            severity=IssueSeverity.HIGH,
            title="Missing alt text",
            description="Image missing alt text",
            nvda_output="unlabeled graphic"
        )
        report = ValidationReport(
            page_url="https://example.com",
            total_issues=1,
            issues_by_severity={"high": 1},
            issues_by_criterion={"1.1.1": 1},
            issues=[issue]
        )

        result = generator._calculate_pass_fail(report)

        assert result["level_a_pass"] is False
        assert result["level_aa_pass"] is True
        assert result["level_aaa_pass"] is True
        assert result["total_criteria_tested"] == 1

    def test_level_aa_fail_with_level_aa_issue(self):
        """Test Level AA fails when Level AA issue present"""
        generator = HTMLGenerator()
        # Create a Level AA criterion
        aa_criterion = WCAGCriterion(
            criterion_id="2.4.6",
            name="Headings and Labels",
            level=WCAGLevel.AA,
            version=WCAGVersion.WCAG_2_0,
            guideline="2.4",
            principle="Operable",
            description="Headings and labels describe topic or purpose",
            detection_method="Check heading hierarchy"
        )
        issue = AccessibilityIssue(
            issue_id="test-2",
            criterion=aa_criterion,
            severity=IssueSeverity.MEDIUM,
            title="Poor heading structure",
            description="Heading hierarchy skips levels",
            nvda_output="heading level 4"
        )
        report = ValidationReport(
            page_url="https://example.com",
            total_issues=1,
            issues_by_severity={"medium": 1},
            issues_by_criterion={"2.4.6": 1},
            issues=[issue]
        )

        result = generator._calculate_pass_fail(report)

        assert result["level_a_pass"] is True
        assert result["level_aa_pass"] is False
        assert result["level_aaa_pass"] is True

    def test_multiple_criteria_tested(self):
        """Test counting multiple failed criteria"""
        generator = HTMLGenerator()
        issues = [
            AccessibilityIssue(
                issue_id="test-3a",
                criterion=CRITERION_1_1_1,
                severity=IssueSeverity.HIGH,
                title="Missing alt",
                description="Image missing alt text",
                nvda_output="unlabeled graphic"
            ),
            AccessibilityIssue(
                issue_id="test-3b",
                criterion=CRITERION_1_1_1,  # Same criterion
                severity=IssueSeverity.HIGH,
                title="Missing alt",
                description="Image missing alt text",
                nvda_output="unlabeled graphic"
            ),
            AccessibilityIssue(
                issue_id="test-3c",
                criterion=CRITERION_3_3_2,  # Different criterion
                severity=IssueSeverity.HIGH,
                title="Missing label",
                description="Form field missing label",
                nvda_output="edit unlabeled"
            ),
        ]
        report = ValidationReport(
            page_url="https://example.com",
            total_issues=3,
            issues_by_severity={"high": 3},
            issues_by_criterion={"1.1.1": 2, "3.3.2": 1},
            issues=issues
        )

        result = generator._calculate_pass_fail(report)

        # Should count unique criteria (1.1.1 and 3.3.2 = 2 total)
        assert result["total_criteria_tested"] == 2


class TestGenerateRecommendations:
    """Tests for _generate_recommendations method"""

    def test_no_recommendations_when_no_issues(self):
        """Test no recommendations when no issues found"""
        generator = HTMLGenerator()
        report = ValidationReport(
            page_url="https://example.com",
            total_issues=0,
            issues_by_severity={},
            issues_by_criterion={},
            issues=[]
        )

        recommendations = generator._generate_recommendations(report)

        assert len(recommendations) == 0

    def test_critical_keyboard_trap_recommendation(self):
        """Test recommendation for critical keyboard trap"""
        generator = HTMLGenerator()
        issue = AccessibilityIssue(
            issue_id="test-4",
            criterion=CRITERION_2_1_2,
            severity=IssueSeverity.CRITICAL,
            title="Keyboard trap",
            description="User stuck in modal dialog",
            nvda_output="circular navigation"
        )
        report = ValidationReport(
            page_url="https://example.com",
            total_issues=1,
            issues_by_severity={"critical": 1},
            issues_by_criterion={"2.1.2": 1},
            issues=[issue]
        )

        recommendations = generator._generate_recommendations(report)

        # Should have critical + general recommendation
        assert len(recommendations) >= 1
        assert any("keyboard trap" in r["title"].lower() for r in recommendations)
        assert any(r["priority"] == "Critical" for r in recommendations)

    def test_high_missing_alt_text_recommendation(self):
        """Test recommendation for missing alt text"""
        generator = HTMLGenerator()
        issue = AccessibilityIssue(
            issue_id="test-5",
            criterion=CRITERION_1_1_1,
            severity=IssueSeverity.HIGH,
            title="Missing alt",
            description="Image missing alt text",
            nvda_output="unlabeled graphic"
        )
        report = ValidationReport(
            page_url="https://example.com",
            total_issues=1,
            issues_by_severity={"high": 1},
            issues_by_criterion={"1.1.1": 1},
            issues=[issue]
        )

        recommendations = generator._generate_recommendations(report)

        assert any("alt text" in r["title"].lower() for r in recommendations)
        assert any(r["priority"] == "High" for r in recommendations)

    def test_high_missing_label_recommendation(self):
        """Test recommendation for missing form labels"""
        generator = HTMLGenerator()
        issue = AccessibilityIssue(
            issue_id="test-6",
            criterion=CRITERION_3_3_2,
            severity=IssueSeverity.HIGH,
            title="Missing label",
            description="Form field missing label",
            nvda_output="edit unlabeled"
        )
        report = ValidationReport(
            page_url="https://example.com",
            total_issues=1,
            issues_by_severity={"high": 1},
            issues_by_criterion={"3.3.2": 1},
            issues=[issue]
        )

        recommendations = generator._generate_recommendations(report)

        assert any("label" in r["title"].lower() for r in recommendations)
        assert any(r["priority"] == "High" for r in recommendations)

    def test_medium_poor_link_text_recommendation(self):
        """Test recommendation for poor link text"""
        generator = HTMLGenerator()
        issue = AccessibilityIssue(
            issue_id="test-7",
            criterion=CRITERION_2_4_4,
            severity=IssueSeverity.MEDIUM,
            title="Generic link text",
            description="Link text is not descriptive",
            nvda_output="link click here"
        )
        report = ValidationReport(
            page_url="https://example.com",
            total_issues=1,
            issues_by_severity={"medium": 1},
            issues_by_criterion={"2.4.4": 1},
            issues=[issue]
        )

        recommendations = generator._generate_recommendations(report)

        assert any("link text" in r["title"].lower() for r in recommendations)
        assert any(r["priority"] == "Medium" for r in recommendations)

    def test_general_recommendation_always_present(self):
        """Test general recommendation present when issues found"""
        generator = HTMLGenerator()
        issue = AccessibilityIssue(
            issue_id="test-8",
            criterion=CRITERION_1_1_1,
            severity=IssueSeverity.HIGH,
            title="Test issue",
            description="Test description",
            nvda_output="test"
        )
        report = ValidationReport(
            page_url="https://example.com",
            total_issues=1,
            issues_by_severity={"high": 1},
            issues_by_criterion={"1.1.1": 1},
            issues=[issue]
        )

        recommendations = generator._generate_recommendations(report)

        assert any(r["priority"] == "General" for r in recommendations)
        assert any("screen reader users" in r["action"].lower() for r in recommendations)

    def test_multiple_recommendations_prioritized(self):
        """Test multiple recommendations in priority order"""
        generator = HTMLGenerator()
        issues = [
            AccessibilityIssue(
                issue_id="test-9a",
                criterion=CRITERION_2_1_2,
                severity=IssueSeverity.CRITICAL,
                title="Keyboard trap",
                description="User stuck in modal",
                nvda_output="circular"
            ),
            AccessibilityIssue(
                issue_id="test-9b",
                criterion=CRITERION_1_1_1,
                severity=IssueSeverity.HIGH,
                title="Missing alt",
                description="Image missing alt text",
                nvda_output="unlabeled graphic"
            ),
            AccessibilityIssue(
                issue_id="test-9c",
                criterion=CRITERION_2_4_4,
                severity=IssueSeverity.MEDIUM,
                title="Poor link",
                description="Link text not descriptive",
                nvda_output="click here"
            ),
        ]
        report = ValidationReport(
            page_url="https://example.com",
            total_issues=3,
            issues_by_severity={"critical": 1, "high": 1, "medium": 1},
            issues_by_criterion={"2.1.2": 1, "1.1.1": 1, "2.4.4": 1},
            issues=issues
        )

        recommendations = generator._generate_recommendations(report)

        # Should have Critical, High, Medium, and General
        priorities = [r["priority"] for r in recommendations]
        assert "Critical" in priorities
        assert "High" in priorities
        assert "Medium" in priorities
        assert "General" in priorities


class TestPrepareContext:
    """Tests for _prepare_context method"""

    def test_context_structure(self):
        """Test that context has all required keys"""
        generator = HTMLGenerator()
        report = ValidationReport(
            page_url="https://example.com",
            total_issues=0,
            issues_by_severity={},
            issues_by_criterion={},
            issues=[]
        )

        context = generator._prepare_context(report)

        assert "report" in context
        assert "issues_by_severity" in context
        assert "issues_by_level" in context
        assert "pass_fail" in context
        assert "recommendations" in context
        assert "generation_time" in context

    def test_context_report_reference(self):
        """Test that context contains report reference"""
        generator = HTMLGenerator()
        report = ValidationReport(
            page_url="https://example.com",
            total_issues=0,
            issues_by_severity={},
            issues_by_criterion={},
            issues=[]
        )

        context = generator._prepare_context(report)

        assert context["report"] is report
        assert context["report"].page_url == "https://example.com"

    def test_context_issues_grouped_by_severity(self):
        """Test that issues are grouped by severity"""
        generator = HTMLGenerator()
        critical_issue = AccessibilityIssue(
            issue_id="test-10a",
            criterion=CRITERION_2_1_2,
            severity=IssueSeverity.CRITICAL,
            title="Test critical",
            description="Test description",
            nvda_output="test"
        )
        high_issue = AccessibilityIssue(
            issue_id="test-10b",
            criterion=CRITERION_1_1_1,
            severity=IssueSeverity.HIGH,
            title="Test high",
            description="Test description",
            nvda_output="test"
        )
        report = ValidationReport(
            page_url="https://example.com",
            total_issues=2,
            issues_by_severity={"critical": 1, "high": 1},
            issues_by_criterion={"2.1.2": 1, "1.1.1": 1},
            issues=[critical_issue, high_issue]
        )

        context = generator._prepare_context(report)

        assert len(context["issues_by_severity"]["critical"]) == 1
        assert len(context["issues_by_severity"]["high"]) == 1
        assert len(context["issues_by_severity"]["medium"]) == 0
        assert len(context["issues_by_severity"]["low"]) == 0

    def test_context_issues_grouped_by_level(self):
        """Test that issues are grouped by WCAG level"""
        generator = HTMLGenerator()
        level_a_issue = AccessibilityIssue(
            issue_id="test-11a",
            criterion=CRITERION_1_1_1,  # Level A
            severity=IssueSeverity.HIGH,
            title="Test Level A",
            description="Test description",
            nvda_output="test"
        )
        aa_criterion = WCAGCriterion(
            criterion_id="2.4.6",
            name="Headings and Labels",
            level=WCAGLevel.AA,
            version=WCAGVersion.WCAG_2_0,
            guideline="2.4",
            principle="Operable",
            description="Test",
            detection_method="Test"
        )
        level_aa_issue = AccessibilityIssue(
            issue_id="test-11b",
            criterion=aa_criterion,
            severity=IssueSeverity.MEDIUM,
            title="Test Level AA",
            description="Test description",
            nvda_output="test"
        )
        report = ValidationReport(
            page_url="https://example.com",
            total_issues=2,
            issues_by_severity={"high": 1, "medium": 1},
            issues_by_criterion={"1.1.1": 1, "2.4.6": 1},
            issues=[level_a_issue, level_aa_issue]
        )

        context = generator._prepare_context(report)

        assert len(context["issues_by_level"]["A"]) == 1
        assert len(context["issues_by_level"]["AA"]) == 1
        assert len(context["issues_by_level"]["AAA"]) == 0

    def test_context_generation_time_is_datetime(self):
        """Test that generation_time is a datetime object"""
        generator = HTMLGenerator()
        report = ValidationReport(
            page_url="https://example.com",
            total_issues=0,
            issues_by_severity={},
            issues_by_criterion={},
            issues=[]
        )

        context = generator._prepare_context(report)

        assert isinstance(context["generation_time"], datetime)


class TestGenerateReport:
    """Tests for generate_report method"""

    def test_generate_report_creates_file(self, tmp_path):
        """Test that generate_report creates HTML file"""
        generator = HTMLGenerator()
        output_path = tmp_path / "test_report.html"
        report = ValidationReport(
            page_url="https://example.com",
            total_issues=0,
            issues_by_severity={},
            issues_by_criterion={},
            issues=[]
        )

        result = generator.generate_report(report, str(output_path))

        assert Path(result).exists()
        assert Path(result).suffix == ".html"

    def test_generate_report_creates_parent_directories(self, tmp_path):
        """Test that parent directories are created if needed"""
        generator = HTMLGenerator()
        output_path = tmp_path / "nested" / "dir" / "report.html"
        report = ValidationReport(
            page_url="https://example.com",
            total_issues=0,
            issues_by_severity={},
            issues_by_criterion={},
            issues=[]
        )

        result = generator.generate_report(report, str(output_path))

        assert Path(result).exists()
        assert Path(result).parent.exists()

    def test_generate_report_returns_path(self, tmp_path):
        """Test that generate_report returns the output path"""
        generator = HTMLGenerator()
        output_path = tmp_path / "report.html"
        report = ValidationReport(
            page_url="https://example.com",
            total_issues=0,
            issues_by_severity={},
            issues_by_criterion={},
            issues=[]
        )

        result = generator.generate_report(report, str(output_path))

        assert result == str(output_path)

    def test_generate_report_contains_page_url(self, tmp_path):
        """Test that generated report contains page URL"""
        generator = HTMLGenerator()
        output_path = tmp_path / "report.html"
        report = ValidationReport(
            page_url="https://example.com",
            total_issues=0,
            issues_by_severity={},
            issues_by_criterion={},
            issues=[]
        )

        result = generator.generate_report(report, str(output_path))
        content = Path(result).read_text(encoding="utf-8")

        assert "https://example.com" in content

    def test_generate_report_contains_issue_data(self, tmp_path):
        """Test that generated report contains issue information"""
        generator = HTMLGenerator()
        output_path = tmp_path / "report.html"
        issue = AccessibilityIssue(
            issue_id="test-12",
            criterion=CRITERION_1_1_1,
            severity=IssueSeverity.HIGH,
            title="Missing alt text",
            description="Image logo missing alt text",
            nvda_output="unlabeled graphic"
        )
        report = ValidationReport(
            page_url="https://example.com",
            total_issues=1,
            issues_by_severity={"high": 1},
            issues_by_criterion={"1.1.1": 1},
            issues=[issue]
        )

        result = generator.generate_report(report, str(output_path))
        content = Path(result).read_text(encoding="utf-8")

        assert "Missing alt text" in content
        assert "1.1.1" in content

    def test_generate_report_html_structure(self, tmp_path):
        """Test that generated report has valid HTML structure"""
        generator = HTMLGenerator()
        output_path = tmp_path / "report.html"
        report = ValidationReport(
            page_url="https://example.com",
            total_issues=0,
            issues_by_severity={},
            issues_by_criterion={},
            issues=[]
        )

        result = generator.generate_report(report, str(output_path))
        content = Path(result).read_text(encoding="utf-8")

        assert "<!DOCTYPE html>" in content or "<html" in content
        assert "</html>" in content
        assert "<head>" in content or "<title>" in content
        assert "<body>" in content or content.strip().endswith("</html>")

    def test_generate_report_utf8_encoding(self, tmp_path):
        """Test that report is saved with UTF-8 encoding"""
        generator = HTMLGenerator()
        output_path = tmp_path / "report.html"
        report = ValidationReport(
            page_url="https://example.com/tëst",  # Unicode character
            total_issues=0,
            issues_by_severity={},
            issues_by_criterion={},
            issues=[]
        )

        result = generator.generate_report(report, str(output_path))
        content = Path(result).read_text(encoding="utf-8")

        assert "tëst" in content


class TestIntegration:
    """Integration tests for complete workflow"""

    def test_full_report_generation_workflow(self, tmp_path):
        """Test complete workflow from issues to HTML report"""
        generator = HTMLGenerator()
        output_path = tmp_path / "full_report.html"

        # Create realistic validation report
        issues = [
            AccessibilityIssue(
                issue_id="test-13a",
                criterion=CRITERION_2_1_2,
                severity=IssueSeverity.CRITICAL,
                title="Keyboard trap in modal",
                description="User cannot escape modal dialog",
                nvda_output="circular navigation detected"
            ),
            AccessibilityIssue(
                issue_id="test-13b",
                criterion=CRITERION_1_1_1,
                severity=IssueSeverity.HIGH,
                title="Missing alt text",
                description="Logo image missing alt text",
                nvda_output="unlabeled graphic"
            ),
            AccessibilityIssue(
                issue_id="test-13c",
                criterion=CRITERION_3_3_2,
                severity=IssueSeverity.HIGH,
                title="Missing form label",
                description="Email field missing label",
                nvda_output="edit unlabeled"
            ),
        ]
        report = ValidationReport(
            page_url="https://example.com/test",
            total_issues=3,
            issues_by_severity={"critical": 1, "high": 2},
            issues_by_criterion={"2.1.2": 1, "1.1.1": 1, "3.3.2": 1},
            issues=issues
        )

        # Generate report
        result = generator.generate_report(report, str(output_path))

        # Verify file exists
        assert Path(result).exists()

        # Verify content
        content = Path(result).read_text(encoding="utf-8")
        assert "https://example.com/test" in content
        assert "Keyboard trap" in content
        assert "Missing alt text" in content  # Title is in the content
        assert "Missing form label" in content  # Title is in the content

        # Verify file size is reasonable (should be > 1KB for full report)
        file_size = Path(result).stat().st_size
        assert file_size > 1024  # At least 1KB
