"""
HTML Report Generation Module

Generates comprehensive, accessible HTML reports from WCAG validation results.
Uses Jinja2 templates to create professional reports with issue details,
severity breakdown, and recommendations.
"""

from src.reporting.html_generator import HTMLGenerator

__all__ = [
    "HTMLGenerator",
]
