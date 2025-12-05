"""Unit tests for NVDA output monitor."""

import time
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from src.screen_reader.output_monitor import CorrelatedEvent, NVDAOutputMonitor


class TestCorrelatedEvent:
    """Test suite for CorrelatedEvent model."""

    def test_correlated_event_with_output(self) -> None:
        """Test correlated event with successful output."""
        from src.screen_reader.nvda_parser import KeyboardInput, SpeechOutput

        action = KeyboardInput(
            timestamp=datetime.now(),
            key="tab",
            modifiers=[],
            raw_input="tab",
        )

        output = SpeechOutput(
            timestamp=datetime.now() + timedelta(milliseconds=100),
            text_parts=["Login", "button"],
            raw_speech="test",
        )

        event = CorrelatedEvent(
            action=action,
            output=output,
            latency_ms=100.0,
            success=True,
            timeout=False,
        )

        assert event.has_output is True
        assert event.is_silent is False
        assert event.success is True

    def test_correlated_event_timeout(self) -> None:
        """Test correlated event with timeout."""
        from src.screen_reader.nvda_parser import KeyboardInput

        action = KeyboardInput(
            timestamp=datetime.now(),
            key="tab",
            modifiers=[],
            raw_input="tab",
        )

        event = CorrelatedEvent(
            action=action,
            output=None,
            latency_ms=2000.0,
            success=False,
            timeout=True,
        )

        assert event.has_output is False
        assert event.is_silent is True
        assert event.timeout is True


class TestNVDAOutputMonitor:
    """Test suite for NVDAOutputMonitor."""

    @pytest.fixture
    def test_log_file(self, tmp_path: Path) -> Path:
        """Create a test log file."""
        log_file = tmp_path / "test_nvda.log"
        log_file.write_text("")
        return log_file

    @pytest.fixture
    def monitor(self, test_log_file: Path) -> NVDAOutputMonitor:
        """Create a monitor instance."""
        return NVDAOutputMonitor(
            log_path=test_log_file,
            correlation_timeout=1.0,
            poll_interval=0.05,
        )

    def test_monitor_initialization(self, monitor: NVDAOutputMonitor) -> None:
        """Test monitor initialization."""
        assert monitor.correlation_timeout == 1.0
        assert monitor.poll_interval == 0.05
        assert len(monitor.correlated_events) == 0

    def test_start_monitor(self, monitor: NVDAOutputMonitor) -> None:
        """Test starting the monitor."""
        monitor.start()
        assert monitor._running is True

    def test_start_monitor_missing_file(self, tmp_path: Path) -> None:
        """Test starting monitor with missing log file."""
        monitor = NVDAOutputMonitor(log_path=tmp_path / "nonexistent.log")

        with pytest.raises(FileNotFoundError):
            monitor.start()

    def test_read_new_entries_empty(self, monitor: NVDAOutputMonitor) -> None:
        """Test reading when no new entries."""
        monitor.start()

        keyboard_inputs, speech_outputs = monitor.read_new_entries()

        assert len(keyboard_inputs) == 0
        assert len(speech_outputs) == 0

    def test_read_new_entries_with_data(
        self, monitor: NVDAOutputMonitor, test_log_file: Path
    ) -> None:
        """Test reading new log entries."""
        monitor.start()

        # Append new log entries
        new_content = """IO - inputCore.InputManager.executeGesture (14:23:45.123) MainThread (INFO):
Input: kb(desktop):tab

DEBUG - speech.speech.speak (14:23:45.234) MainThread (DEBUG):
Speaking: [u'Email', u'edit']
"""
        with open(test_log_file, "a") as f:
            f.write(new_content)

        # Read new entries
        keyboard_inputs, speech_outputs = monitor.read_new_entries()

        assert len(keyboard_inputs) == 1
        assert keyboard_inputs[0].key == "tab"

        assert len(speech_outputs) == 1
        assert "Email" in speech_outputs[0].text_parts

    def test_poll_and_correlate(
        self, monitor: NVDAOutputMonitor, test_log_file: Path
    ) -> None:
        """Test polling and automatic correlation."""
        monitor.start()

        # Use current time for timestamps
        now = datetime.now()
        time_str_action = now.strftime("%H:%M:%S") + ".000"
        time_str_speech = (now + timedelta(milliseconds=100)).strftime("%H:%M:%S") + ".100"

        # Append keyboard input
        with open(test_log_file, "a") as f:
            f.write(
                f"IO - inputCore.InputManager.executeGesture ({time_str_action}) MainThread (INFO):\n"
            )
            f.write("Input: kb(desktop):tab\n")

        monitor.poll()

        # Append speech output
        with open(test_log_file, "a") as f:
            f.write(
                f"DEBUG - speech.speech.speak ({time_str_speech}) MainThread (DEBUG):\n"
            )
            f.write("Speaking: [u'Login', u'button']\n")

        monitor.poll()

        # Should have correlated the action with output
        assert len(monitor.correlated_events) == 1
        event = monitor.correlated_events[0]

        assert event.success is True
        assert event.has_output is True
        assert event.action.key == "tab"
        assert "Login" in event.output.text_parts  # type: ignore

    def test_correlation_timeout(
        self, monitor: NVDAOutputMonitor, test_log_file: Path
    ) -> None:
        """Test correlation timeout when no speech follows action."""
        monitor.start()

        # Append keyboard input
        with open(test_log_file, "a") as f:
            f.write(
                "IO - inputCore.InputManager.executeGesture (10:00:00.000) MainThread (INFO):\n"
            )
            f.write("Input: kb(desktop):tab\n")

        monitor.poll()

        # Wait for timeout
        time.sleep(1.2)
        monitor.poll()

        # Should have timeout event
        assert len(monitor.correlated_events) == 1
        event = monitor.correlated_events[0]

        assert event.timeout is True
        assert event.success is False
        assert event.has_output is False

    def test_callbacks_keyboard_input(
        self, monitor: NVDAOutputMonitor, test_log_file: Path
    ) -> None:
        """Test keyboard input callback."""
        monitor.start()

        keyboard_events = []

        def on_keyboard(kb_input):  # type: ignore
            keyboard_events.append(kb_input)

        monitor.on_keyboard_input(on_keyboard)

        # Append keyboard input
        with open(test_log_file, "a") as f:
            f.write(
                "IO - inputCore.InputManager.executeGesture (14:23:45.123) MainThread (INFO):\n"
            )
            f.write("Input: kb(desktop):enter\n")

        monitor.poll()

        assert len(keyboard_events) == 1
        assert keyboard_events[0].key == "enter"

    def test_callbacks_speech_output(
        self, monitor: NVDAOutputMonitor, test_log_file: Path
    ) -> None:
        """Test speech output callback."""
        monitor.start()

        speech_events = []

        def on_speech(speech):  # type: ignore
            speech_events.append(speech)

        monitor.on_speech_output(on_speech)

        # Append speech
        with open(test_log_file, "a") as f:
            f.write(
                "DEBUG - speech.speech.speak (14:23:45.234) MainThread (DEBUG):\n"
            )
            f.write("Speaking: [u'Submit', u'button']\n")

        monitor.poll()

        assert len(speech_events) == 1
        assert "Submit" in speech_events[0].text_parts

    def test_callbacks_correlated_event(
        self, monitor: NVDAOutputMonitor, test_log_file: Path
    ) -> None:
        """Test correlated event callback."""
        monitor.start()

        correlated_events = []

        def on_correlated(event):  # type: ignore
            correlated_events.append(event)

        monitor.on_correlated_event(on_correlated)

        # Append action and output
        with open(test_log_file, "a") as f:
            f.write(
                "IO - inputCore.InputManager.executeGesture (14:23:45.123) MainThread (INFO):\n"
            )
            f.write("Input: kb(desktop):tab\n")
            f.write(
                "DEBUG - speech.speech.speak (14:23:45.234) MainThread (DEBUG):\n"
            )
            f.write("Speaking: [u'Test']\n")

        monitor.poll()

        assert len(correlated_events) == 1
        assert correlated_events[0].success is True

    def test_get_output_after(
        self, monitor: NVDAOutputMonitor, test_log_file: Path
    ) -> None:
        """Test getting output after specific timestamp."""
        monitor.start()

        timestamp = datetime.now()

        # Append speech after timestamp with sufficient time gap
        time.sleep(0.2)
        now_after = datetime.now() + timedelta(milliseconds=500)
        time_str = now_after.strftime("%H:%M:%S.%f")[:-3]

        with open(test_log_file, "a") as f:
            f.write(
                f"DEBUG - speech.speech.speak ({time_str}) MainThread (DEBUG):\n"
            )
            f.write("Speaking: [u'Found it']\n")

        output = monitor.get_output_after(timestamp, timeout=1.0)

        assert output is not None
        assert "Found it" in output.text_parts

    def test_get_output_after_timeout(
        self, monitor: NVDAOutputMonitor, test_log_file: Path
    ) -> None:
        """Test get_output_after with timeout."""
        monitor.start()

        timestamp = datetime.now()

        # No speech added
        output = monitor.get_output_after(timestamp, timeout=0.5)

        assert output is None

    def test_wait_for_idle(
        self, monitor: NVDAOutputMonitor, test_log_file: Path
    ) -> None:
        """Test waiting for idle state."""
        monitor.start()

        # Should become idle immediately (no activity)
        is_idle = monitor.wait_for_idle(idle_time=0.2, max_wait=1.0)

        assert is_idle is True

    def test_stop_monitor(
        self, monitor: NVDAOutputMonitor, test_log_file: Path
    ) -> None:
        """Test stopping monitor and processing pending actions."""
        monitor.start()

        # Add pending action
        with open(test_log_file, "a") as f:
            f.write(
                "IO - inputCore.InputManager.executeGesture (14:23:45.123) MainThread (INFO):\n"
            )
            f.write("Input: kb(desktop):tab\n")

        monitor.poll()

        # Stop should force process pending
        monitor.stop()

        assert monitor._running is False
        # Should have timeout event for pending action
        assert len(monitor.correlated_events) >= 1

    def test_get_statistics(
        self, monitor: NVDAOutputMonitor, test_log_file: Path
    ) -> None:
        """Test getting monitoring statistics."""
        monitor.start()

        # Add correlated event
        with open(test_log_file, "a") as f:
            f.write(
                "IO - inputCore.InputManager.executeGesture (14:23:45.123) MainThread (INFO):\n"
            )
            f.write("Input: kb(desktop):tab\n")
            f.write(
                "DEBUG - speech.speech.speak (14:23:45.234) MainThread (DEBUG):\n"
            )
            f.write("Speaking: [u'Test']\n")

        monitor.poll()

        stats = monitor.get_statistics()

        assert stats["total_events"] >= 1
        assert stats["successful_correlations"] >= 1
        assert "average_latency_ms" in stats


@pytest.mark.integration
class TestOutputMonitorIntegration:
    """Integration tests for output monitor."""

    def test_real_world_navigation_sequence(self, tmp_path: Path) -> None:
        """Test monitoring a real-world navigation sequence."""
        log_file = tmp_path / "integration_nvda.log"
        log_file.write_text("")

        monitor = NVDAOutputMonitor(
            log_path=log_file,
            correlation_timeout=1.0,
            poll_interval=0.05,
        )
        monitor.start()

        # Use current time and increment for sequence
        base_time = datetime.now()

        # Simulate real navigation sequence with dynamic timestamps
        actions_data = [
            ("tab", "Email", "edit"),
            ("tab", "Password", "edit"),
            ("enter", "Sign in", "button"),
        ]

        for i, (key, text, role) in enumerate(actions_data):
            action_time = base_time + timedelta(milliseconds=i * 1000)
            speech_time = action_time + timedelta(milliseconds=100)

            action_time_str = action_time.strftime("%H:%M:%S.%f")[:-3]
            speech_time_str = speech_time.strftime("%H:%M:%S.%f")[:-3]

            # Write action
            with open(log_file, "a") as f:
                f.write(
                    f"IO - inputCore.InputManager.executeGesture ({action_time_str}) MainThread (INFO):\n"
                )
                f.write(f"Input: kb(desktop):{key}\n")
            monitor.poll()

            # Write speech
            with open(log_file, "a") as f:
                f.write(
                    f"DEBUG - speech.speech.speak ({speech_time_str}) MainThread (DEBUG):\n"
                )
                f.write(f"Speaking: [u'{text}', u'{role}']\n")
            monitor.poll()

        # Verify all actions correlated
        assert len(monitor.correlated_events) == 3

        # Verify all successful
        for event in monitor.correlated_events:
            assert event.success is True
            assert event.has_output is True

        # Verify statistics
        stats = monitor.get_statistics()
        assert stats["total_events"] == 3
        assert stats["successful_correlations"] == 3
        assert stats["timeouts"] == 0
