"""Unit tests for correlation models (Pydantic schemas)."""

from datetime import datetime, timedelta

import pytest

from src.correlation.models import CorrelatedEvent, KeyboardAction, NVDAOutput


class TestKeyboardAction:
    """Tests for KeyboardAction model."""

    def test_create_basic_action(self) -> None:
        """Test creating a basic keyboard action."""
        action = KeyboardAction(key="Tab")

        assert action.key == "Tab"
        assert action.modifiers == []
        assert action.context is None
        assert isinstance(action.timestamp, datetime)
        assert isinstance(action.action_id, str)
        assert len(action.action_id) == 36  # UUID format

    def test_create_action_with_modifiers(self) -> None:
        """Test creating an action with modifier keys."""
        action = KeyboardAction(key="F", modifiers=["Ctrl"])

        assert action.key == "F"
        assert action.modifiers == ["Ctrl"]

    def test_create_action_with_multiple_modifiers(self) -> None:
        """Test creating an action with multiple modifiers."""
        action = KeyboardAction(key="c", modifiers=["Ctrl", "Shift"])

        assert action.key == "c"
        assert action.modifiers == ["Ctrl", "Shift"]

    def test_create_action_with_context(self) -> None:
        """Test creating an action with context information."""
        action = KeyboardAction(key="Enter", context="Submit login form")

        assert action.key == "Enter"
        assert action.context == "Submit login form"

    def test_unique_action_ids(self) -> None:
        """Test that each action gets a unique ID."""
        action1 = KeyboardAction(key="Tab")
        action2 = KeyboardAction(key="Tab")

        assert action1.action_id != action2.action_id

    def test_timestamp_auto_generated(self) -> None:
        """Test that timestamp is auto-generated."""
        before = datetime.now()
        action = KeyboardAction(key="Enter")
        after = datetime.now()

        assert before <= action.timestamp <= after

    def test_json_serialization(self) -> None:
        """Test that action can be serialized to JSON."""
        action = KeyboardAction(key="Tab", modifiers=["Shift"])
        json_data = action.model_dump(mode="json")

        assert json_data["key"] == "Tab"
        assert json_data["modifiers"] == ["Shift"]
        assert "action_id" in json_data
        assert "timestamp" in json_data


class TestNVDAOutput:
    """Tests for NVDAOutput model."""

    def test_create_basic_output(self) -> None:
        """Test creating basic NVDA output."""
        output = NVDAOutput(text="Login button")

        assert output.text == "Login button"
        assert output.raw_log_entry is None
        assert isinstance(output.timestamp, datetime)
        assert isinstance(output.output_id, str)
        assert len(output.output_id) == 36  # UUID format

    def test_create_output_with_log_entry(self) -> None:
        """Test creating output with raw log entry."""
        log_entry = "DEBUG - speech.speech.speak (10:23:45.234)"
        output = NVDAOutput(text="Submit button", raw_log_entry=log_entry)

        assert output.text == "Submit button"
        assert output.raw_log_entry == log_entry

    def test_unique_output_ids(self) -> None:
        """Test that each output gets a unique ID."""
        output1 = NVDAOutput(text="Same text")
        output2 = NVDAOutput(text="Same text")

        assert output1.output_id != output2.output_id

    def test_timestamp_auto_generated(self) -> None:
        """Test that timestamp is auto-generated."""
        before = datetime.now()
        output = NVDAOutput(text="Test output")
        after = datetime.now()

        assert before <= output.timestamp <= after

    def test_json_serialization(self) -> None:
        """Test that output can be serialized to JSON."""
        output = NVDAOutput(text="Hello world")
        json_data = output.model_dump(mode="json")

        assert json_data["text"] == "Hello world"
        assert "output_id" in json_data
        assert "timestamp" in json_data


class TestCorrelatedEvent:
    """Tests for CorrelatedEvent model."""

    def test_create_successful_event(self) -> None:
        """Test creating a successful correlation event."""
        action = KeyboardAction(key="Tab")
        output = NVDAOutput(text="Username edit")

        event = CorrelatedEvent(
            action=action,
            output=output,
            latency_ms=125.5,
            success=True,
        )

        assert event.action == action
        assert event.output == output
        assert event.latency_ms == 125.5
        assert event.success is True
        assert isinstance(event.correlation_id, str)

    def test_create_timeout_event(self) -> None:
        """Test creating a timeout event (no output)."""
        action = KeyboardAction(key="Enter")

        event = CorrelatedEvent(
            action=action,
            output=None,
            latency_ms=2000.0,
            success=False,
        )

        assert event.action == action
        assert event.output is None
        assert event.latency_ms == 2000.0
        assert event.success is False

    def test_unique_correlation_ids(self) -> None:
        """Test that each event gets a unique correlation ID."""
        action = KeyboardAction(key="Tab")
        output = NVDAOutput(text="Test")

        event1 = CorrelatedEvent(action=action, output=output, latency_ms=100, success=True)
        event2 = CorrelatedEvent(action=action, output=output, latency_ms=100, success=True)

        assert event1.correlation_id != event2.correlation_id

    def test_to_dict_successful_event(self) -> None:
        """Test converting successful event to dictionary."""
        action = KeyboardAction(key="h")
        output = NVDAOutput(text="Heading level 1, Welcome")

        event = CorrelatedEvent(
            action=action,
            output=output,
            latency_ms=87.3,
            success=True,
        )

        data = event.to_dict()

        assert data["success"] is True
        assert data["latency_ms"] == 87.3
        assert data["action"]["key"] == "h"
        assert data["output"]["text"] == "Heading level 1, Welcome"

    def test_to_dict_timeout_event(self) -> None:
        """Test converting timeout event to dictionary."""
        action = KeyboardAction(key="Tab")

        event = CorrelatedEvent(
            action=action,
            output=None,
            latency_ms=2000.0,
            success=False,
        )

        data = event.to_dict()

        assert data["success"] is False
        assert data["latency_ms"] == 2000.0
        assert data["action"]["key"] == "Tab"
        assert data["output"] is None

    def test_json_serialization(self) -> None:
        """Test that event can be serialized to JSON."""
        action = KeyboardAction(key="Enter")
        output = NVDAOutput(text="Form submitted")

        event = CorrelatedEvent(
            action=action,
            output=output,
            latency_ms=150.0,
            success=True,
        )

        json_data = event.model_dump(mode="json")

        assert "action" in json_data
        assert "output" in json_data
        assert json_data["latency_ms"] == 150.0
        assert json_data["success"] is True
