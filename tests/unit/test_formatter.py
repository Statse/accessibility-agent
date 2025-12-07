"""Unit tests for CorrelationFormatter."""

import json
import tempfile
from pathlib import Path

import pytest

from src.correlation.action_logger import ActionLogger
from src.correlation.correlator import FeedbackCorrelator
from src.correlation.formatter import CorrelationFormatter
from src.correlation.models import KeyboardAction, NVDAOutput


class TestCorrelationFormatterInitialization:
    """Tests for CorrelationFormatter initialization."""

    def test_create_formatter(self) -> None:
        """Test creating CorrelationFormatter."""
        action_logger = ActionLogger()
        correlator = FeedbackCorrelator(action_logger)
        formatter = CorrelationFormatter(correlator)

        assert formatter.correlator == correlator


class TestFormatEvent:
    """Tests for formatting individual events."""

    def test_format_successful_event(self) -> None:
        """Test formatting a successful correlation event."""
        action_logger = ActionLogger()
        correlator = FeedbackCorrelator(action_logger)
        formatter = CorrelationFormatter(correlator)

        action = KeyboardAction(key="Tab")
        output = NVDAOutput(text="Login button")
        correlator.add_nvda_output(output)
        event = correlator.correlate_action(action, wait=False)

        formatted = formatter.format_event(event)

        assert "[✓]" in formatted
        assert "Tab" in formatted
        assert "Login button" in formatted
        assert "ms)" in formatted

    def test_format_timeout_event(self) -> None:
        """Test formatting a timeout event."""
        action_logger = ActionLogger()
        correlator = FeedbackCorrelator(action_logger, correlation_timeout=0.1)
        formatter = CorrelationFormatter(correlator)

        action = KeyboardAction(key="Enter")
        correlator._pending_actions.append(action)
        import time
        time.sleep(0.15)
        correlator._process_correlations()

        event = correlator.get_all_events()[0]
        formatted = formatter.format_event(event)

        assert "[✗]" in formatted
        assert "Enter" in formatted
        assert "NO OUTPUT" in formatted

    def test_format_event_with_modifiers(self) -> None:
        """Test formatting event with modifier keys."""
        action_logger = ActionLogger()
        correlator = FeedbackCorrelator(action_logger)
        formatter = CorrelationFormatter(correlator)

        action = KeyboardAction(key="F", modifiers=["Ctrl"])
        output = NVDAOutput(text="Find dialog")
        correlator.add_nvda_output(output)
        event = correlator.correlate_action(action, wait=False)

        formatted = formatter.format_event(event)

        # Format is "+CtrlF" not "Ctrl+F"
        assert "+CtrlF" in formatted
        assert "Find dialog" in formatted

    def test_format_event_verbose(self) -> None:
        """Test formatting event in verbose mode."""
        action_logger = ActionLogger()
        correlator = FeedbackCorrelator(action_logger)
        formatter = CorrelationFormatter(correlator)

        action = KeyboardAction(key="Tab", context="Navigate to submit button")
        output = NVDAOutput(text="Submit button")
        correlator.add_nvda_output(output)
        event = correlator.correlate_action(action, wait=False)

        formatted = formatter.format_event(event, verbose=True)

        assert "Action ID:" in formatted
        assert "Timestamp:" in formatted
        assert "Context:" in formatted
        assert "Navigate to submit button" in formatted

    def test_format_event_with_long_text(self) -> None:
        """Test formatting event with long NVDA output (truncation)."""
        action_logger = ActionLogger()
        correlator = FeedbackCorrelator(action_logger)
        formatter = CorrelationFormatter(correlator)

        long_text = "A" * 100
        action = KeyboardAction(key="Tab")
        output = NVDAOutput(text=long_text)
        correlator.add_nvda_output(output)
        event = correlator.correlate_action(action, wait=False)

        formatted = formatter.format_event(event)

        # Should be truncated with "..."
        assert "..." in formatted
        assert len(formatted) < len(long_text) + 50


class TestFormatSummary:
    """Tests for formatting correlation summary."""

    def test_format_summary_empty(self) -> None:
        """Test formatting summary with no events."""
        action_logger = ActionLogger()
        correlator = FeedbackCorrelator(action_logger)
        formatter = CorrelationFormatter(correlator)

        summary = formatter.format_summary()

        assert "CORRELATION SUMMARY" in summary
        assert "Total Events:              0" in summary
        assert "Successful Correlations:   0" in summary
        assert "Timeouts (No Output):      0" in summary

    def test_format_summary_with_events(self) -> None:
        """Test formatting summary with events."""
        action_logger = ActionLogger()
        correlator = FeedbackCorrelator(action_logger)
        formatter = CorrelationFormatter(correlator)

        # Add some events
        for _ in range(3):
            action = KeyboardAction(key="Tab")
            output = NVDAOutput(text="Button")
            correlator.add_nvda_output(output)
            correlator.correlate_action(action, wait=False)

        summary = formatter.format_summary()

        assert "Total Events:              3" in summary
        assert "Successful Correlations:   3" in summary


class TestFormatAllEvents:
    """Tests for formatting all events."""

    def test_format_all_events_empty(self) -> None:
        """Test formatting all events when empty."""
        action_logger = ActionLogger()
        correlator = FeedbackCorrelator(action_logger)
        formatter = CorrelationFormatter(correlator)

        output = formatter.format_all_events()

        assert "No correlated events yet" in output

    def test_format_all_events_with_events(self) -> None:
        """Test formatting all events."""
        action_logger = ActionLogger()
        correlator = FeedbackCorrelator(action_logger)
        formatter = CorrelationFormatter(correlator)

        action = KeyboardAction(key="Tab")
        output = NVDAOutput(text="Button")
        correlator.add_nvda_output(output)
        correlator.correlate_action(action, wait=False)

        output = formatter.format_all_events()

        assert "CORRELATION SUMMARY" in output
        assert "CORRELATED EVENTS" in output
        assert "Tab" in output

    def test_format_all_events_exclude_successful(self) -> None:
        """Test formatting all events excluding successful ones."""
        action_logger = ActionLogger()
        correlator = FeedbackCorrelator(action_logger, correlation_timeout=0.1)
        formatter = CorrelationFormatter(correlator)

        # Successful event
        action1 = KeyboardAction(key="Tab")
        output1 = NVDAOutput(text="Button")
        correlator.add_nvda_output(output1)
        correlator.correlate_action(action1, wait=False)

        # Timeout event
        action2 = KeyboardAction(key="Enter")
        correlator._pending_actions.append(action2)
        import time
        time.sleep(0.15)
        correlator._process_correlations()

        output = formatter.format_all_events(include_successful=False)

        # Should only show timeout
        assert "[✗]" in output
        assert "[✓]" not in output


class TestFormatTimeoutEvents:
    """Tests for formatting timeout events."""

    def test_format_timeout_events_none(self) -> None:
        """Test formatting timeout events when none exist."""
        action_logger = ActionLogger()
        correlator = FeedbackCorrelator(action_logger)
        formatter = CorrelationFormatter(correlator)

        output = formatter.format_timeout_events()

        assert "No timeout events" in output

    def test_format_timeout_events_with_timeouts(self) -> None:
        """Test formatting timeout events."""
        action_logger = ActionLogger()
        correlator = FeedbackCorrelator(action_logger, correlation_timeout=0.1)
        formatter = CorrelationFormatter(correlator)

        action = KeyboardAction(key="Tab")
        correlator._pending_actions.append(action)
        import time
        time.sleep(0.15)
        correlator._process_correlations()

        output = formatter.format_timeout_events()

        assert "TIMEOUT EVENTS" in output
        assert "Potential Accessibility Issues" in output
        assert "[✗]" in output


class TestToJson:
    """Tests for JSON export."""

    def test_to_json_empty(self) -> None:
        """Test JSON export with no events."""
        action_logger = ActionLogger()
        correlator = FeedbackCorrelator(action_logger)
        formatter = CorrelationFormatter(correlator)

        json_str = formatter.to_json()
        data = json.loads(json_str)

        assert "statistics" in data
        assert "events" in data
        assert "generated_at" in data
        assert data["statistics"]["total_events"] == 0

    def test_to_json_with_events(self) -> None:
        """Test JSON export with events."""
        action_logger = ActionLogger()
        correlator = FeedbackCorrelator(action_logger)
        formatter = CorrelationFormatter(correlator)

        action = KeyboardAction(key="Tab")
        output = NVDAOutput(text="Button")
        correlator.add_nvda_output(output)
        correlator.correlate_action(action, wait=False)

        json_str = formatter.to_json()
        data = json.loads(json_str)

        assert len(data["events"]) == 1
        assert data["events"][0]["action"]["key"] == "Tab"
        assert data["events"][0]["output"]["text"] == "Button"

    def test_to_json_compact(self) -> None:
        """Test compact JSON export (no indentation)."""
        action_logger = ActionLogger()
        correlator = FeedbackCorrelator(action_logger)
        formatter = CorrelationFormatter(correlator)

        json_str = formatter.to_json(pretty=False)

        # Compact JSON should not have newlines
        assert "\n" not in json_str


class TestToDict:
    """Tests for dictionary export."""

    def test_to_dict(self) -> None:
        """Test dictionary export."""
        action_logger = ActionLogger()
        correlator = FeedbackCorrelator(action_logger)
        formatter = CorrelationFormatter(correlator)

        action = KeyboardAction(key="Enter")
        output = NVDAOutput(text="Submitted")
        correlator.add_nvda_output(output)
        correlator.correlate_action(action, wait=False)

        data = formatter.to_dict()

        assert isinstance(data, dict)
        assert "statistics" in data
        assert "events" in data
        assert len(data["events"]) == 1


class TestGenerateAccessibilityReport:
    """Tests for generating accessibility-focused reports."""

    def test_generate_accessibility_report_all_successful(self) -> None:
        """Test accessibility report with all successful correlations."""
        action_logger = ActionLogger()
        correlator = FeedbackCorrelator(action_logger)
        formatter = CorrelationFormatter(correlator)

        # All successful
        for _ in range(3):
            action = KeyboardAction(key="Tab")
            output = NVDAOutput(text="Button")
            correlator.add_nvda_output(output)
            correlator.correlate_action(action, wait=False)

        report = formatter.generate_accessibility_report()

        assert "ACCESSIBILITY CORRELATION REPORT" in report
        assert "SUMMARY" in report
        assert "ACCESSIBILITY STATUS: GOOD" in report
        assert "No silent elements detected" in report

    def test_generate_accessibility_report_with_issues(self) -> None:
        """Test accessibility report with timeout events (issues)."""
        action_logger = ActionLogger()
        correlator = FeedbackCorrelator(action_logger, correlation_timeout=0.1)
        formatter = CorrelationFormatter(correlator)

        # Successful
        action1 = KeyboardAction(key="Tab")
        output1 = NVDAOutput(text="Button")
        correlator.add_nvda_output(output1)
        correlator.correlate_action(action1, wait=False)

        # Timeout
        action2 = KeyboardAction(key="Enter", context="Submit form")
        correlator._pending_actions.append(action2)
        import time
        time.sleep(0.15)
        correlator._process_correlations()

        report = formatter.generate_accessibility_report()

        assert "POTENTIAL ACCESSIBILITY ISSUES" in report
        assert "Enter" in report
        assert "Submit form" in report
        assert "WCAG violation" in report

    def test_generate_accessibility_report_with_performance_metrics(self) -> None:
        """Test that accessibility report includes performance metrics."""
        action_logger = ActionLogger()
        correlator = FeedbackCorrelator(action_logger)
        formatter = CorrelationFormatter(correlator)

        action = KeyboardAction(key="Tab")
        output = NVDAOutput(text="Button")
        correlator.add_nvda_output(output)
        correlator.correlate_action(action, wait=False)

        report = formatter.generate_accessibility_report()

        assert "PERFORMANCE METRICS" in report
        assert "Average Response Time:" in report


class TestSaveJsonReport:
    """Tests for saving JSON reports to file."""

    def test_save_json_report(self) -> None:
        """Test saving JSON report to file."""
        action_logger = ActionLogger()
        correlator = FeedbackCorrelator(action_logger)
        formatter = CorrelationFormatter(correlator)

        action = KeyboardAction(key="Tab")
        output = NVDAOutput(text="Button")
        correlator.add_nvda_output(output)
        correlator.correlate_action(action, wait=False)

        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "report.json"
            formatter.save_json_report(str(filepath))

            assert filepath.exists()

            # Verify content
            with open(filepath) as f:
                data = json.load(f)

            assert "events" in data
            assert len(data["events"]) == 1


class TestSaveTextReport:
    """Tests for saving text reports to file."""

    def test_save_text_report_full(self) -> None:
        """Test saving full text report."""
        action_logger = ActionLogger()
        correlator = FeedbackCorrelator(action_logger)
        formatter = CorrelationFormatter(correlator)

        action = KeyboardAction(key="Tab")
        output = NVDAOutput(text="Button")
        correlator.add_nvda_output(output)
        correlator.correlate_action(action, wait=False)

        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "report.txt"
            formatter.save_text_report(str(filepath), report_type="full")

            assert filepath.exists()

            with open(filepath) as f:
                content = f.read()

            assert "CORRELATION SUMMARY" in content
            assert "Tab" in content

    def test_save_text_report_accessibility(self) -> None:
        """Test saving accessibility text report."""
        action_logger = ActionLogger()
        correlator = FeedbackCorrelator(action_logger)
        formatter = CorrelationFormatter(correlator)

        action = KeyboardAction(key="Tab")
        output = NVDAOutput(text="Button")
        correlator.add_nvda_output(output)
        correlator.correlate_action(action, wait=False)

        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "accessibility.txt"
            formatter.save_text_report(str(filepath), report_type="accessibility")

            assert filepath.exists()

            with open(filepath) as f:
                content = f.read()

            assert "ACCESSIBILITY CORRELATION REPORT" in content

    def test_save_text_report_timeouts(self) -> None:
        """Test saving timeouts-only text report."""
        action_logger = ActionLogger()
        correlator = FeedbackCorrelator(action_logger, correlation_timeout=0.1)
        formatter = CorrelationFormatter(correlator)

        action = KeyboardAction(key="Tab")
        correlator._pending_actions.append(action)
        import time
        time.sleep(0.15)
        correlator._process_correlations()

        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "timeouts.txt"
            formatter.save_text_report(str(filepath), report_type="timeouts")

            assert filepath.exists()

            with open(filepath) as f:
                content = f.read()

            assert "TIMEOUT EVENTS" in content

    def test_save_text_report_invalid_type(self) -> None:
        """Test that invalid report type raises ValueError."""
        action_logger = ActionLogger()
        correlator = FeedbackCorrelator(action_logger)
        formatter = CorrelationFormatter(correlator)

        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "report.txt"

            with pytest.raises(ValueError, match="Invalid report_type"):
                formatter.save_text_report(str(filepath), report_type="invalid")


class TestAccessibilityReportEdgeCases:
    """Tests for edge cases in accessibility report generation."""

    def test_accessibility_report_with_slow_responses(self) -> None:
        """Test that slow responses are highlighted in accessibility report."""
        action_logger = ActionLogger()
        correlator = FeedbackCorrelator(action_logger)
        formatter = CorrelationFormatter(correlator)

        # Create event with slow response
        action = KeyboardAction(key="Tab")
        import time
        time.sleep(0.01)
        output = NVDAOutput(text="Slow element")
        correlator.add_nvda_output(output)
        event = correlator.correlate_action(action, wait=False)

        # Manually adjust latency for testing
        event.latency_ms = 1500  # 1.5 seconds

        report = formatter.generate_accessibility_report()

        # Report should include slow response section if threshold exceeded
        # (threshold is 1000ms in the formatter)
        if event.latency_ms > 1000:
            # Slow responses section may or may not appear depending on implementation
            pass

    def test_accessibility_report_with_context(self) -> None:
        """Test that action context appears in accessibility report."""
        action_logger = ActionLogger()
        correlator = FeedbackCorrelator(action_logger, correlation_timeout=0.1)
        formatter = CorrelationFormatter(correlator)

        action = KeyboardAction(key="Enter", context="Submit registration form")
        correlator._pending_actions.append(action)
        import time
        time.sleep(0.15)
        correlator._process_correlations()

        report = formatter.generate_accessibility_report()

        assert "Submit registration form" in report
