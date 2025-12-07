"""Unit tests for FeedbackCorrelator."""

import time
from datetime import datetime, timedelta
from unittest.mock import Mock

import pytest

from src.correlation.action_logger import ActionLogger
from src.correlation.correlator import FeedbackCorrelator
from src.correlation.models import CorrelatedEvent, KeyboardAction, NVDAOutput


class TestFeedbackCorrelatorInitialization:
    """Tests for FeedbackCorrelator initialization."""

    def test_create_default_correlator(self) -> None:
        """Test creating FeedbackCorrelator with default settings."""
        action_logger = ActionLogger()
        correlator = FeedbackCorrelator(action_logger)

        assert correlator.action_logger == action_logger
        assert correlator.correlation_timeout == 2.0
        assert correlator.max_history == 1000

    def test_create_correlator_with_custom_settings(self) -> None:
        """Test creating FeedbackCorrelator with custom settings."""
        action_logger = ActionLogger()
        correlator = FeedbackCorrelator(
            action_logger,
            correlation_timeout=5.0,
            max_history=500,
        )

        assert correlator.correlation_timeout == 5.0
        assert correlator.max_history == 500

    def test_create_correlator_with_invalid_timeout(self) -> None:
        """Test that invalid timeout raises ValueError."""
        action_logger = ActionLogger()

        with pytest.raises(ValueError, match="correlation_timeout must be >= 0"):
            FeedbackCorrelator(action_logger, correlation_timeout=-1.0)

    def test_create_correlator_with_invalid_max_history(self) -> None:
        """Test that invalid max_history raises ValueError."""
        action_logger = ActionLogger()

        with pytest.raises(ValueError, match="max_history must be >= 1"):
            FeedbackCorrelator(action_logger, max_history=0)


class TestCallbackRegistration:
    """Tests for callback registration."""

    def test_register_on_correlation_callback(self) -> None:
        """Test registering correlation callback."""
        action_logger = ActionLogger()
        correlator = FeedbackCorrelator(action_logger)
        callback = Mock()

        correlator.on_correlation(callback)

        assert correlator._on_correlation_callback == callback

    def test_register_on_timeout_callback(self) -> None:
        """Test registering timeout callback."""
        action_logger = ActionLogger()
        correlator = FeedbackCorrelator(action_logger)
        callback = Mock()

        correlator.on_timeout(callback)

        assert correlator._on_timeout_callback == callback


class TestAddNVDAOutput:
    """Tests for adding NVDA output."""

    def test_add_nvda_output(self) -> None:
        """Test adding NVDA output to correlator."""
        action_logger = ActionLogger()
        correlator = FeedbackCorrelator(action_logger)

        output = NVDAOutput(text="Login button")
        correlator.add_nvda_output(output)

        # Output should be in pending buffer
        assert len(correlator._pending_outputs) == 1

    def test_add_multiple_outputs(self) -> None:
        """Test adding multiple NVDA outputs."""
        action_logger = ActionLogger()
        correlator = FeedbackCorrelator(action_logger)

        output1 = NVDAOutput(text="Login button")
        output2 = NVDAOutput(text="Username edit")

        correlator.add_nvda_output(output1)
        correlator.add_nvda_output(output2)

        assert len(correlator._pending_outputs) == 2


class TestCorrelateAction:
    """Tests for correlating actions with NVDA output."""

    def test_correlate_action_immediate_without_wait(self) -> None:
        """Test immediate correlation without waiting."""
        action_logger = ActionLogger()
        correlator = FeedbackCorrelator(action_logger)

        action = KeyboardAction(key="Tab")

        # Try to correlate without output (should return None)
        result = correlator.correlate_action(action, wait=False)

        assert result is None

    def test_correlate_action_with_existing_output(self) -> None:
        """Test correlating action with pre-existing output."""
        action_logger = ActionLogger()
        correlator = FeedbackCorrelator(action_logger, correlation_timeout=0.5)

        # Log action first
        action = KeyboardAction(key="Tab")

        # Add output after action
        time.sleep(0.01)  # Small delay
        output = NVDAOutput(text="Login button")
        correlator.add_nvda_output(output)

        # Try immediate correlation
        result = correlator.correlate_action(action, wait=False)

        assert result is not None
        assert result.success is True
        assert result.action.key == "Tab"
        assert result.output.text == "Login button"

    def test_correlate_action_with_wait_and_success(self) -> None:
        """Test correlating action with wait mode (successful)."""
        action_logger = ActionLogger()
        correlator = FeedbackCorrelator(action_logger, correlation_timeout=1.0)

        action = KeyboardAction(key="Enter")

        # Add output after small delay in a separate thread simulation
        # (In real usage, output arrives asynchronously)
        output = NVDAOutput(text="Form submitted")
        correlator.add_nvda_output(output)

        result = correlator.correlate_action(action, wait=True)

        assert result is not None
        assert result.success is True
        assert result.latency_ms > 0

    def test_correlate_action_with_wait_and_timeout(self) -> None:
        """Test correlating action with wait mode (timeout)."""
        action_logger = ActionLogger()
        correlator = FeedbackCorrelator(action_logger, correlation_timeout=0.2)

        action = KeyboardAction(key="Tab")

        # Don't add any output - should timeout
        result = correlator.correlate_action(action, wait=True)

        assert result is not None
        assert result.success is False
        assert result.output is None
        assert result.latency_ms >= 200  # At least timeout duration


class TestSuccessfulCorrelation:
    """Tests for successful action-output correlation."""

    def test_successful_correlation_creates_event(self) -> None:
        """Test that successful correlation creates CorrelatedEvent."""
        action_logger = ActionLogger()
        correlator = FeedbackCorrelator(action_logger)

        action = KeyboardAction(key="h")
        output = NVDAOutput(text="Heading level 1, Welcome")

        correlator.add_nvda_output(output)
        event = correlator.correlate_action(action, wait=False)

        assert event is not None
        assert event.success is True
        assert event.action.key == "h"
        assert event.output.text == "Heading level 1, Welcome"
        assert event.latency_ms > 0

    def test_successful_correlation_calls_callback(self) -> None:
        """Test that successful correlation triggers callback."""
        action_logger = ActionLogger()
        correlator = FeedbackCorrelator(action_logger)
        callback = Mock()

        correlator.on_correlation(callback)

        action = KeyboardAction(key="Tab")
        output = NVDAOutput(text="Submit button")

        correlator.add_nvda_output(output)
        correlator.correlate_action(action, wait=False)

        # Callback should have been called once
        assert callback.call_count == 1
        event = callback.call_args[0][0]
        assert isinstance(event, CorrelatedEvent)
        assert event.success is True

    def test_correlation_matches_first_output_after_action(self) -> None:
        """Test that correlation matches the first output after action timestamp."""
        action_logger = ActionLogger()
        correlator = FeedbackCorrelator(action_logger)

        # Add output before action (should not match)
        old_output = NVDAOutput(text="Old output")
        old_output.timestamp = datetime.now() - timedelta(seconds=1)
        correlator.add_nvda_output(old_output)

        action = KeyboardAction(key="Tab")

        # Add outputs after action
        time.sleep(0.01)
        output1 = NVDAOutput(text="First output")
        output2 = NVDAOutput(text="Second output")

        correlator.add_nvda_output(output1)
        correlator.add_nvda_output(output2)

        event = correlator.correlate_action(action, wait=False)

        # Should match first output after action, not old output
        assert event is not None
        assert event.output.text == "First output"


class TestTimeoutCorrelation:
    """Tests for timeout correlation (no NVDA output)."""

    def test_timeout_creates_event(self) -> None:
        """Test that timeout creates CorrelatedEvent with success=False."""
        action_logger = ActionLogger()
        correlator = FeedbackCorrelator(action_logger, correlation_timeout=0.1)

        action = KeyboardAction(key="Tab")

        event = correlator.correlate_action(action, wait=True)

        assert event is not None
        assert event.success is False
        assert event.output is None
        assert event.latency_ms >= 100

    def test_timeout_calls_callback(self) -> None:
        """Test that timeout triggers timeout callback."""
        action_logger = ActionLogger()
        correlator = FeedbackCorrelator(action_logger, correlation_timeout=0.1)
        callback = Mock()

        correlator.on_timeout(callback)

        action = KeyboardAction(key="Tab")

        # Add action to pending without wait, let it timeout via process
        correlator._pending_actions.append(action)
        time.sleep(0.15)  # Wait for timeout
        correlator._process_correlations()

        # Timeout callback should have been called
        assert callback.call_count == 1
        event = callback.call_args[0][0]
        assert isinstance(event, CorrelatedEvent)
        assert event.success is False


class TestGetEvents:
    """Tests for retrieving correlated events."""

    def test_get_all_events_empty(self) -> None:
        """Test getting all events from empty correlator."""
        action_logger = ActionLogger()
        correlator = FeedbackCorrelator(action_logger)

        events = correlator.get_all_events()

        assert len(events) == 0

    def test_get_all_events_with_events(self) -> None:
        """Test getting all events."""
        action_logger = ActionLogger()
        correlator = FeedbackCorrelator(action_logger)

        action1 = KeyboardAction(key="Tab")
        output1 = NVDAOutput(text="Button")
        correlator.add_nvda_output(output1)
        correlator.correlate_action(action1, wait=False)

        action2 = KeyboardAction(key="Enter")
        output2 = NVDAOutput(text="Submitted")
        correlator.add_nvda_output(output2)
        correlator.correlate_action(action2, wait=False)

        events = correlator.get_all_events()

        assert len(events) == 2

    def test_get_successful_events(self) -> None:
        """Test getting only successful correlation events."""
        action_logger = ActionLogger()
        correlator = FeedbackCorrelator(action_logger, correlation_timeout=0.1)

        # Successful correlation
        action1 = KeyboardAction(key="Tab")
        output1 = NVDAOutput(text="Button")
        correlator.add_nvda_output(output1)
        correlator.correlate_action(action1, wait=False)

        # Timeout
        action2 = KeyboardAction(key="Enter")
        correlator.correlate_action(action2, wait=True)

        successful = correlator.get_successful_events()

        assert len(successful) == 1
        assert successful[0].success is True

    def test_get_timeout_events(self) -> None:
        """Test getting only timeout events."""
        action_logger = ActionLogger()
        correlator = FeedbackCorrelator(action_logger, correlation_timeout=0.1)

        # Successful correlation
        action1 = KeyboardAction(key="Tab")
        output1 = NVDAOutput(text="Button")
        correlator.add_nvda_output(output1)
        correlator.correlate_action(action1, wait=False)

        # Timeout via pending action
        action2 = KeyboardAction(key="Enter")
        correlator._pending_actions.append(action2)
        time.sleep(0.15)  # Wait for timeout
        correlator._process_correlations()

        timeouts = correlator.get_timeout_events()

        assert len(timeouts) == 1
        assert timeouts[0].success is False


class TestGetEventsInRange:
    """Tests for getting events in time ranges."""

    def test_get_events_in_range(self) -> None:
        """Test getting events within a time range."""
        action_logger = ActionLogger()
        correlator = FeedbackCorrelator(action_logger)

        # Event before range
        action0 = KeyboardAction(key="Escape")
        output0 = NVDAOutput(text="Before")
        correlator.add_nvda_output(output0)
        correlator.correlate_action(action0, wait=False)

        time.sleep(0.01)
        start = datetime.now()
        time.sleep(0.01)

        # Event 1 in range
        action1 = KeyboardAction(key="Tab")
        output1 = NVDAOutput(text="Button")
        correlator.add_nvda_output(output1)
        correlator.correlate_action(action1, wait=False)

        # Event 2 in range
        action2 = KeyboardAction(key="Enter")
        output2 = NVDAOutput(text="Submitted")
        correlator.add_nvda_output(output2)
        correlator.correlate_action(action2, wait=False)

        time.sleep(0.01)
        end = datetime.now()
        time.sleep(0.01)

        # Event after range
        action3 = KeyboardAction(key="h")
        output3 = NVDAOutput(text="Heading")
        correlator.add_nvda_output(output3)
        correlator.correlate_action(action3, wait=False)

        events = correlator.get_events_in_range(start, end)

        assert len(events) == 2

    def test_get_events_in_last_seconds(self) -> None:
        """Test getting events from last N seconds."""
        action_logger = ActionLogger()
        correlator = FeedbackCorrelator(action_logger)

        action = KeyboardAction(key="Tab")
        output = NVDAOutput(text="Button")
        correlator.add_nvda_output(output)
        correlator.correlate_action(action, wait=False)

        events = correlator.get_events_in_last_seconds(10)

        assert len(events) >= 1


class TestGetStatistics:
    """Tests for correlation statistics."""

    def test_get_statistics_empty(self) -> None:
        """Test getting statistics from empty correlator."""
        action_logger = ActionLogger()
        correlator = FeedbackCorrelator(action_logger)

        stats = correlator.get_statistics()

        assert stats["total_events"] == 0
        assert stats["successful_correlations"] == 0
        assert stats["timeouts"] == 0
        assert stats["timeout_rate"] == 0.0
        assert stats["average_latency_ms"] == 0.0

    def test_get_statistics_with_events(self) -> None:
        """Test getting statistics with successful and timeout events."""
        action_logger = ActionLogger()
        correlator = FeedbackCorrelator(action_logger, correlation_timeout=0.1)

        # 2 successful
        for _ in range(2):
            action = KeyboardAction(key="Tab")
            output = NVDAOutput(text="Button")
            correlator.add_nvda_output(output)
            correlator.correlate_action(action, wait=False)

        # 1 timeout via pending action
        action = KeyboardAction(key="Enter")
        correlator._pending_actions.append(action)
        time.sleep(0.15)  # Wait for timeout
        correlator._process_correlations()

        stats = correlator.get_statistics()

        assert stats["total_events"] == 3
        assert stats["successful_correlations"] == 2
        assert stats["timeouts"] == 1
        assert stats["timeout_rate"] == pytest.approx(33.33, rel=0.1)
        assert stats["average_latency_ms"] > 0

    def test_get_statistics_calculates_average_latency(self) -> None:
        """Test that statistics correctly calculate average latency."""
        action_logger = ActionLogger()
        correlator = FeedbackCorrelator(action_logger)

        # Create events with known latencies
        action1 = KeyboardAction(key="Tab")
        output1 = NVDAOutput(text="Button")
        correlator.add_nvda_output(output1)
        event1 = correlator.correlate_action(action1, wait=False)

        action2 = KeyboardAction(key="Enter")
        output2 = NVDAOutput(text="Submitted")
        correlator.add_nvda_output(output2)
        event2 = correlator.correlate_action(action2, wait=False)

        stats = correlator.get_statistics()

        expected_avg = (event1.latency_ms + event2.latency_ms) / 2
        assert stats["average_latency_ms"] == pytest.approx(expected_avg, rel=0.01)


class TestClear:
    """Tests for clearing correlation data."""

    def test_clear_empty_correlator(self) -> None:
        """Test clearing empty correlator."""
        action_logger = ActionLogger()
        correlator = FeedbackCorrelator(action_logger)

        correlator.clear()

        assert len(correlator.get_all_events()) == 0

    def test_clear_correlator_with_events(self) -> None:
        """Test clearing correlator with events."""
        action_logger = ActionLogger()
        correlator = FeedbackCorrelator(action_logger)

        action = KeyboardAction(key="Tab")
        output = NVDAOutput(text="Button")
        correlator.add_nvda_output(output)
        correlator.correlate_action(action, wait=False)

        assert len(correlator.get_all_events()) == 1

        correlator.clear()

        assert len(correlator.get_all_events()) == 0
        assert len(correlator._pending_actions) == 0
        assert len(correlator._pending_outputs) == 0


class TestForceCorrelatePending:
    """Tests for force-correlating pending actions."""

    def test_force_correlate_pending_empty(self) -> None:
        """Test force-correlating with no pending actions."""
        action_logger = ActionLogger()
        correlator = FeedbackCorrelator(action_logger)

        new_events = correlator.force_correlate_pending()

        assert len(new_events) == 0

    def test_force_correlate_pending_with_actions(self) -> None:
        """Test force-correlating pending actions as timeouts."""
        action_logger = ActionLogger()
        correlator = FeedbackCorrelator(action_logger)

        # Add actions without outputs (they'll be pending)
        action1 = KeyboardAction(key="Tab")
        action2 = KeyboardAction(key="Enter")

        correlator.correlate_action(action1, wait=False)
        correlator.correlate_action(action2, wait=False)

        # Force correlate
        new_events = correlator.force_correlate_pending()

        assert len(new_events) == 2
        assert all(event.success is False for event in new_events)
        assert all(event.output is None for event in new_events)


class TestBufferOverflow:
    """Tests for event buffer overflow behavior."""

    def test_buffer_respects_max_history(self) -> None:
        """Test that event buffer respects max_history."""
        action_logger = ActionLogger()
        correlator = FeedbackCorrelator(action_logger, max_history=3)

        # Add 4 events
        for i in range(4):
            action = KeyboardAction(key=f"{i}")
            output = NVDAOutput(text=f"Output {i}")
            correlator.add_nvda_output(output)
            correlator.correlate_action(action, wait=False)

        events = correlator.get_all_events()

        # Should only keep last 3
        assert len(events) == 3


class TestMultipleRapidActions:
    """Tests for handling multiple rapid actions."""

    def test_multiple_rapid_actions_correlate_correctly(self) -> None:
        """Test that multiple rapid actions correlate correctly."""
        action_logger = ActionLogger()
        correlator = FeedbackCorrelator(action_logger)

        # Rapid actions
        action1 = KeyboardAction(key="Tab")
        action2 = KeyboardAction(key="Tab")
        action3 = KeyboardAction(key="Tab")

        # Corresponding outputs
        time.sleep(0.01)
        output1 = NVDAOutput(text="Button 1")
        output2 = NVDAOutput(text="Button 2")
        output3 = NVDAOutput(text="Button 3")

        correlator.add_nvda_output(output1)
        correlator.add_nvda_output(output2)
        correlator.add_nvda_output(output3)

        event1 = correlator.correlate_action(action1, wait=False)
        event2 = correlator.correlate_action(action2, wait=False)
        event3 = correlator.correlate_action(action3, wait=False)

        # Each should get the first available output
        assert event1.output.text == "Button 1"
        assert event2.output.text == "Button 2"
        assert event3.output.text == "Button 3"
