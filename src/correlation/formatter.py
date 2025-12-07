"""Correlation report formatter for generating human-readable reports.

This module provides formatting utilities for correlation data,
generating reports in various formats (text, JSON, structured).
"""

import json
import logging
from datetime import datetime
from typing import Any

from .correlator import FeedbackCorrelator
from .models import CorrelatedEvent

logger = logging.getLogger(__name__)


class CorrelationFormatter:
    """Formats correlation data into human-readable reports.

    This formatter generates reports from correlated events,
    highlighting potential accessibility issues (timeouts, slow responses)
    and providing statistics for analysis.

    Attributes:
        correlator: FeedbackCorrelator instance to generate reports from
    """

    def __init__(self, correlator: FeedbackCorrelator) -> None:
        """Initialize the correlation formatter.

        Args:
            correlator: FeedbackCorrelator to generate reports from
        """
        self.correlator = correlator
        logger.info("CorrelationFormatter initialized")

    def format_event(self, event: CorrelatedEvent, verbose: bool = False) -> str:
        """Format a single correlated event as text.

        Args:
            event: CorrelatedEvent to format
            verbose: If True, include more details (IDs, timestamps)

        Returns:
            Formatted string representation of the event
        """
        action = event.action
        modifiers_str = f"+{'+'.join(action.modifiers)}" if action.modifiers else ""
        key_str = f"{modifiers_str}{action.key}" if modifiers_str else action.key

        if event.success and event.output:
            output_text = event.output.text[:80]
            if len(event.output.text) > 80:
                output_text += "..."

            result = f"[✓] {key_str} → '{output_text}' ({event.latency_ms:.1f}ms)"
        else:
            result = f"[✗] {key_str} → (NO OUTPUT - timeout after {event.latency_ms:.0f}ms)"

        if verbose:
            result += f"\n    Action ID: {action.action_id}"
            result += f"\n    Timestamp: {action.timestamp.isoformat()}"
            if action.context:
                result += f"\n    Context: {action.context}"
            if event.output:
                result += f"\n    Output ID: {event.output.output_id}"

        return result

    def format_summary(self) -> str:
        """Generate a summary of all correlation statistics.

        Returns:
            Formatted summary string with statistics
        """
        stats = self.correlator.get_statistics()

        summary = "=" * 60 + "\n"
        summary += "CORRELATION SUMMARY\n"
        summary += "=" * 60 + "\n\n"

        summary += f"Total Events:              {stats['total_events']}\n"
        summary += f"Successful Correlations:   {stats['successful_correlations']}\n"
        summary += f"Timeouts (No Output):      {stats['timeouts']}\n"
        summary += f"Timeout Rate:              {stats['timeout_rate']:.1f}%\n"
        summary += f"Average Latency:           {stats['average_latency_ms']:.1f}ms\n"
        summary += f"\nPending Actions:           {stats['pending_actions']}\n"
        summary += f"Pending Outputs:           {stats['pending_outputs']}\n"

        return summary

    def format_all_events(
        self, verbose: bool = False, include_successful: bool = True
    ) -> str:
        """Format all correlated events as text.

        Args:
            verbose: If True, include detailed information
            include_successful: If True, include successful correlations.
                If False, only show timeouts (potential issues).

        Returns:
            Formatted string with all events
        """
        events = self.correlator.get_all_events()

        if not events:
            return "No correlated events yet.\n"

        output = self.format_summary() + "\n"
        output += "=" * 60 + "\n"
        output += "CORRELATED EVENTS\n"
        output += "=" * 60 + "\n\n"

        for i, event in enumerate(events, 1):
            if not include_successful and event.success:
                continue

            output += f"{i}. {self.format_event(event, verbose=verbose)}\n"
            if verbose:
                output += "\n"

        return output

    def format_timeout_events(self, verbose: bool = False) -> str:
        """Format only timeout events (potential accessibility issues).

        Timeout events indicate that a keyboard action did not result
        in NVDA feedback, which often indicates an accessibility issue
        (e.g., unlabeled element, missing alt text).

        Args:
            verbose: If True, include detailed information

        Returns:
            Formatted string with timeout events
        """
        timeout_events = self.correlator.get_timeout_events()

        if not timeout_events:
            return "No timeout events (all actions had NVDA feedback).\n"

        output = "=" * 60 + "\n"
        output += "TIMEOUT EVENTS (Potential Accessibility Issues)\n"
        output += "=" * 60 + "\n\n"

        for i, event in enumerate(timeout_events, 1):
            output += f"{i}. {self.format_event(event, verbose=verbose)}\n"
            if verbose:
                output += "\n"

        return output

    def to_json(self, pretty: bool = True) -> str:
        """Export all correlation data as JSON.

        Args:
            pretty: If True, format with indentation. If False, compact.

        Returns:
            JSON string with all events and statistics
        """
        events = self.correlator.get_all_events()
        stats = self.correlator.get_statistics()

        data = {
            "statistics": stats,
            "events": [event.to_dict() for event in events],
            "generated_at": datetime.now().isoformat(),
        }

        if pretty:
            return json.dumps(data, indent=2)
        else:
            return json.dumps(data)

    def to_dict(self) -> dict[str, Any]:
        """Export all correlation data as dictionary.

        Returns:
            Dictionary with events and statistics
        """
        events = self.correlator.get_all_events()
        stats = self.correlator.get_statistics()

        return {
            "statistics": stats,
            "events": [event.to_dict() for event in events],
            "generated_at": datetime.now().isoformat(),
        }

    def generate_accessibility_report(self) -> str:
        """Generate a report focused on accessibility issues.

        This report highlights timeout events (no NVDA feedback)
        which are likely accessibility violations.

        Returns:
            Formatted accessibility-focused report
        """
        stats = self.correlator.get_statistics()
        timeout_events = self.correlator.get_timeout_events()
        successful_events = self.correlator.get_successful_events()

        report = "=" * 60 + "\n"
        report += "ACCESSIBILITY CORRELATION REPORT\n"
        report += "=" * 60 + "\n\n"

        report += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

        # Summary
        report += "SUMMARY\n"
        report += "-" * 60 + "\n"
        report += f"Total Actions Tested:      {stats['total_events']}\n"
        report += f"Actions with Feedback:     {stats['successful_correlations']}\n"
        report += f"Actions without Feedback:  {stats['timeouts']}\n"
        report += f"Issue Rate:                {stats['timeout_rate']:.1f}%\n\n"

        # Timeout analysis
        if timeout_events:
            report += "POTENTIAL ACCESSIBILITY ISSUES (No NVDA Feedback)\n"
            report += "-" * 60 + "\n"
            report += (
                "The following keyboard actions did not produce NVDA output.\n"
                "This may indicate unlabeled elements, missing alt text, or\n"
                "other accessibility violations.\n\n"
            )

            for i, event in enumerate(timeout_events, 1):
                action = event.action
                modifiers_str = (
                    f"+{'+'.join(action.modifiers)}" if action.modifiers else ""
                )
                key_str = (
                    f"{modifiers_str}{action.key}" if modifiers_str else action.key
                )

                report += f"{i}. Key: {key_str}\n"
                if action.context:
                    report += f"   Context: {action.context}\n"
                report += f"   Timestamp: {action.timestamp.strftime('%H:%M:%S.%f')[:-3]}\n"
                report += f"   Waited: {event.latency_ms:.0f}ms (timeout)\n"
                report += "   → Likely WCAG violation (missing label/alt text)\n\n"
        else:
            report += "ACCESSIBILITY STATUS: GOOD\n"
            report += "-" * 60 + "\n"
            report += "All keyboard actions produced NVDA feedback.\n"
            report += "No silent elements detected.\n\n"

        # Performance analysis
        if successful_events:
            latencies = [e.latency_ms for e in successful_events]
            avg_latency = sum(latencies) / len(latencies)
            max_latency = max(latencies)
            min_latency = min(latencies)

            report += "PERFORMANCE METRICS\n"
            report += "-" * 60 + "\n"
            report += f"Average Response Time:     {avg_latency:.1f}ms\n"
            report += f"Min Response Time:         {min_latency:.1f}ms\n"
            report += f"Max Response Time:         {max_latency:.1f}ms\n\n"

            # Identify slow responses
            slow_threshold = 1000  # 1 second
            slow_events = [e for e in successful_events if e.latency_ms > slow_threshold]

            if slow_events:
                report += f"SLOW RESPONSES (>{slow_threshold}ms)\n"
                report += "-" * 60 + "\n"
                for event in slow_events:
                    action = event.action
                    output_preview = (
                        event.output.text[:50] if event.output else "N/A"
                    )
                    report += (
                        f"  {action.key} → '{output_preview}...' "
                        f"({event.latency_ms:.0f}ms)\n"
                    )
                report += "\n"

        report += "=" * 60 + "\n"
        return report

    def save_json_report(self, filepath: str) -> None:
        """Save correlation data to JSON file.

        Args:
            filepath: Path to save JSON file
        """
        json_data = self.to_json(pretty=True)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(json_data)

        logger.info(f"Correlation report saved to {filepath}")

    def save_text_report(self, filepath: str, report_type: str = "full") -> None:
        """Save correlation report to text file.

        Args:
            filepath: Path to save text file
            report_type: Type of report to generate:
                - "full": All events with statistics
                - "accessibility": Accessibility-focused report
                - "timeouts": Only timeout events

        Raises:
            ValueError: If report_type is invalid
        """
        if report_type == "full":
            content = self.format_all_events(verbose=True)
        elif report_type == "accessibility":
            content = self.generate_accessibility_report()
        elif report_type == "timeouts":
            content = self.format_timeout_events(verbose=True)
        else:
            raise ValueError(
                f"Invalid report_type: {report_type}. "
                "Must be 'full', 'accessibility', or 'timeouts'"
            )

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

        logger.info(f"Correlation report saved to {filepath} (type={report_type})")
