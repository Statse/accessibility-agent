"""
HTML Report Generator

Generates comprehensive HTML accessibility reports using Jinja2 templates.
Transforms ValidationReport into formatted HTML with executive summary,
issue details, WCAG criteria breakdown, and recommendations.
"""

import os
from pathlib import Path
from typing import Optional
from datetime import datetime
from jinja2 import Environment, FileSystemLoader, Template

from src.wcag.validator import ValidationReport
from src.wcag.issue_detector import AccessibilityIssue
from src.wcag.criteria_mapper import IssueSeverity, WCAGLevel


class HTMLGenerator:
    """
    Generates HTML accessibility reports from validation results.

    Uses Jinja2 templates to create professional, accessible HTML reports
    with executive summary, detailed issue listings, and recommendations.
    """

    def __init__(self, template_dir: Optional[str] = None):
        """
        Initialize HTML generator.

        Args:
            template_dir: Path to Jinja2 template directory.
                         Defaults to src/reporting/templates
        """
        if template_dir is None:
            # Default to src/reporting/templates
            module_dir = Path(__file__).parent
            template_dir = str(module_dir / "templates")

        self.template_dir = template_dir
        self.env = Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=True,  # Security: auto-escape HTML
            trim_blocks=True,
            lstrip_blocks=True,
        )

        # Register custom filters
        self.env.filters["format_datetime"] = self._format_datetime
        self.env.filters["severity_badge_class"] = self._severity_badge_class
        self.env.filters["level_badge_class"] = self._level_badge_class

    def generate_report(
        self, validation_report: ValidationReport, output_path: str
    ) -> str:
        """
        Generate HTML report from validation results.

        Args:
            validation_report: WCAG validation report
            output_path: Path where HTML file should be saved

        Returns:
            Path to generated HTML file
        """
        # Load template
        template = self.env.get_template("report.html.jinja2")

        # Prepare data for template
        context = self._prepare_context(validation_report)

        # Render template
        html_content = template.render(**context)

        # Save to file
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(html_content, encoding="utf-8")

        return str(output_path)

    def _prepare_context(self, report: ValidationReport) -> dict:
        """
        Prepare template context from validation report.

        Args:
            report: Validation report

        Returns:
            Dictionary with all template variables
        """
        # Group issues by severity
        issues_by_severity = {
            "critical": [i for i in report.issues if i.severity == IssueSeverity.CRITICAL],
            "high": [i for i in report.issues if i.severity == IssueSeverity.HIGH],
            "medium": [i for i in report.issues if i.severity == IssueSeverity.MEDIUM],
            "low": [i for i in report.issues if i.severity == IssueSeverity.LOW],
        }

        # Group issues by WCAG level
        issues_by_level = {
            "A": [i for i in report.issues if i.criterion.level == WCAGLevel.A],
            "AA": [i for i in report.issues if i.criterion.level == WCAGLevel.AA],
            "AAA": [i for i in report.issues if i.criterion.level == WCAGLevel.AAA],
        }

        # Calculate pass/fail status
        pass_fail = self._calculate_pass_fail(report)

        # Generate recommendations
        recommendations = self._generate_recommendations(report)

        return {
            "report": report,
            "issues_by_severity": issues_by_severity,
            "issues_by_level": issues_by_level,
            "pass_fail": pass_fail,
            "recommendations": recommendations,
            "generation_time": datetime.now(),
        }

    def _calculate_pass_fail(self, report: ValidationReport) -> dict:
        """
        Calculate pass/fail status for WCAG conformance.

        Args:
            report: Validation report

        Returns:
            Dictionary with conformance levels and pass/fail status
        """
        # Get unique criteria that failed
        failed_criteria = {i.criterion.criterion_id for i in report.issues}

        # Check each level
        level_a_failed = any(
            i.criterion.level == WCAGLevel.A for i in report.issues
        )
        level_aa_failed = any(
            i.criterion.level == WCAGLevel.AA for i in report.issues
        )
        level_aaa_failed = any(
            i.criterion.level == WCAGLevel.AAA for i in report.issues
        )

        return {
            "level_a_pass": not level_a_failed,
            "level_aa_pass": not level_aa_failed,
            "level_aaa_pass": not level_aaa_failed,
            "total_criteria_tested": len(set(i.criterion.criterion_id for i in report.issues)) if report.issues else 0,
        }

    def _generate_recommendations(self, report: ValidationReport) -> list[dict]:
        """
        Generate prioritized recommendations based on issues found.

        Args:
            report: Validation report

        Returns:
            List of recommendation dictionaries
        """
        recommendations = []

        # Critical issues - top priority
        critical_count = report.issues_by_severity.get("critical", 0)
        if critical_count > 0:
            recommendations.append({
                "priority": "Critical",
                "title": "Fix keyboard traps immediately",
                "description": f"{critical_count} critical keyboard trap(s) detected. "
                               "Users cannot navigate away from certain elements.",
                "action": "Review elements with circular navigation and ensure proper keyboard handling.",
            })

        # High severity - missing labels and alt text
        high_count = report.issues_by_severity.get("high", 0)
        if high_count > 0:
            missing_alt = sum(1 for i in report.issues if i.criterion.criterion_id == "1.1.1")
            missing_labels = sum(1 for i in report.issues if i.criterion.criterion_id == "3.3.2")

            if missing_alt > 0:
                recommendations.append({
                    "priority": "High",
                    "title": "Add alt text to images",
                    "description": f"{missing_alt} image(s) missing alt text.",
                    "action": "Add descriptive alt attributes to all images. Use alt=\"\" for decorative images.",
                })

            if missing_labels > 0:
                recommendations.append({
                    "priority": "High",
                    "title": "Label all form fields",
                    "description": f"{missing_labels} form field(s) missing labels.",
                    "action": "Associate <label> elements with form inputs or use aria-label.",
                })

        # Medium severity - usability issues
        medium_count = report.issues_by_severity.get("medium", 0)
        if medium_count > 0:
            poor_links = sum(1 for i in report.issues if i.criterion.criterion_id == "2.4.4")
            heading_issues = sum(1 for i in report.issues if i.criterion.criterion_id == "2.4.6")
            skip_link_missing = sum(1 for i in report.issues if i.criterion.criterion_id == "2.4.1")

            if poor_links > 0:
                recommendations.append({
                    "priority": "Medium",
                    "title": "Improve link text",
                    "description": f"{poor_links} link(s) with generic or missing text.",
                    "action": "Replace generic link text like 'click here' with descriptive text.",
                })

            if heading_issues > 0:
                recommendations.append({
                    "priority": "Medium",
                    "title": "Fix heading structure",
                    "description": f"{heading_issues} heading structure issue(s) detected.",
                    "action": "Ensure headings follow logical hierarchy (H1 → H2 → H3) without skipping levels.",
                })

            if skip_link_missing > 0:
                recommendations.append({
                    "priority": "Medium",
                    "title": "Add skip navigation link",
                    "description": "No skip link found at page start.",
                    "action": "Add a 'Skip to main content' link as the first focusable element.",
                })

        # General recommendations
        if report.total_issues > 0:
            recommendations.append({
                "priority": "General",
                "title": "Test with real screen reader users",
                "description": "Automated testing found issues, but manual testing is essential.",
                "action": "Conduct usability testing with actual screen reader users (NVDA, JAWS, etc.).",
            })

        return recommendations

    @staticmethod
    def _format_datetime(dt: datetime) -> str:
        """Format datetime for display"""
        return dt.strftime("%Y-%m-%d %H:%M:%S")

    @staticmethod
    def _severity_badge_class(severity: str) -> str:
        """Get CSS class for severity badge"""
        severity_classes = {
            "critical": "badge-critical",
            "high": "badge-high",
            "medium": "badge-medium",
            "low": "badge-low",
        }
        return severity_classes.get(severity.lower(), "badge-default")

    @staticmethod
    def _level_badge_class(level: str) -> str:
        """Get CSS class for WCAG level badge"""
        level_classes = {
            "A": "badge-level-a",
            "AA": "badge-level-aa",
            "AAA": "badge-level-aaa",
        }
        return level_classes.get(level, "badge-default")
