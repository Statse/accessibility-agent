"""Real-time NVDA output monitor with action-feedback correlation.

Monitors NVDA log file in real-time and correlates keyboard actions
with screen reader speech output.
"""

import time
from datetime import datetime
from pathlib import Path
from typing import Callable

from pydantic import BaseModel, Field

from .nvda_parser import KeyboardInput, NVDALogParser, SpeechOutput


class CorrelatedEvent(BaseModel):
    """Represents a correlated keyboard action and NVDA speech output."""

    action: KeyboardInput
    output: SpeechOutput | None = None
    latency_ms: float = Field(default=0.0)
    success: bool = Field(default=False)
    timeout: bool = Field(default=False)

    @property
    def has_output(self) -> bool:
        """Check if event has associated speech output."""
        return self.output is not None

    @property
    def is_silent(self) -> bool:
        """Check if action resulted in no speech (potential accessibility issue)."""
        return self.timeout or self.output is None


class NVDAOutputMonitor:
    """Monitor NVDA log file in real-time and correlate actions with output."""

    def __init__(
        self,
        log_path: str | Path,
        correlation_timeout: float = 2.0,
        poll_interval: float = 0.1,
    ):
        """Initialize NVDA output monitor.

        Args:
            log_path: Path to NVDA log file
            correlation_timeout: Seconds to wait for speech after keyboard action
            poll_interval: Seconds between file polling checks
        """
        self.log_path = Path(log_path)
        self.correlation_timeout = correlation_timeout
        self.poll_interval = poll_interval

        self.parser = NVDALogParser()
        self._file_position = 0
        self._line_number = 0

        # Buffers for pending correlation
        self._pending_actions: list[KeyboardInput] = []
        self._pending_speeches: list[SpeechOutput] = []

        # All collected events
        self.correlated_events: list[CorrelatedEvent] = []

        # Callbacks
        self._on_keyboard_callback: Callable[[KeyboardInput], None] | None = None
        self._on_speech_callback: Callable[[SpeechOutput], None] | None = None
        self._on_correlated_callback: Callable[[CorrelatedEvent], None] | None = None

        self._running = False

    def on_keyboard_input(self, callback: Callable[[KeyboardInput], None]) -> None:
        """Register callback for keyboard input events.

        Args:
            callback: Function to call when keyboard input detected
        """
        self._on_keyboard_callback = callback

    def on_speech_output(self, callback: Callable[[SpeechOutput], None]) -> None:
        """Register callback for speech output events.

        Args:
            callback: Function to call when speech output detected
        """
        self._on_speech_callback = callback

    def on_correlated_event(self, callback: Callable[[CorrelatedEvent], None]) -> None:
        """Register callback for correlated events.

        Args:
            callback: Function to call when action-output correlation complete
        """
        self._on_correlated_callback = callback

    def start(self) -> None:
        """Start monitoring NVDA log file.

        Seeks to end of file and begins monitoring for new entries.
        """
        if not self.log_path.exists():
            raise FileNotFoundError(f"NVDA log file not found: {self.log_path}")

        # Seek to end of file
        with open(self.log_path, "r", encoding="utf-8") as f:
            f.seek(0, 2)  # Seek to end
            self._file_position = f.tell()

        # Count existing lines
        with open(self.log_path, "r", encoding="utf-8") as f:
            self._line_number = sum(1 for _ in f)

        self._running = True

    def stop(self) -> None:
        """Stop monitoring and process any pending correlations."""
        self._running = False
        self._process_pending_correlations(force=True)

    def read_new_entries(self) -> tuple[list[KeyboardInput], list[SpeechOutput]]:
        """Read new log entries since last read.

        Returns:
            Tuple of (keyboard_inputs, speech_outputs)
        """
        if not self.log_path.exists():
            return [], []

        keyboard_inputs: list[KeyboardInput] = []
        speech_outputs: list[SpeechOutput] = []

        with open(self.log_path, "r", encoding="utf-8", errors="ignore") as f:
            # Seek to last position
            f.seek(self._file_position)

            # Read new lines
            new_lines = f.readlines()
            self._file_position = f.tell()

        if not new_lines:
            return [], []

        # Parse new lines
        current_entry = None
        accumulated_message = ""

        for line in new_lines:
            line = line.rstrip()
            self._line_number += 1

            entry, message = self.parser.parse_line(line)

            if entry:
                # Process previous entry
                if current_entry and accumulated_message:
                    self._process_parser_entry(
                        current_entry, accumulated_message, keyboard_inputs, speech_outputs
                    )

                current_entry = entry
                accumulated_message = message
            else:
                if current_entry:
                    accumulated_message += "\n" + line

        # Process last entry
        if current_entry and accumulated_message:
            self._process_parser_entry(
                current_entry, accumulated_message, keyboard_inputs, speech_outputs
            )

        return keyboard_inputs, speech_outputs

    def _process_parser_entry(
        self, entry, message, keyboard_inputs, speech_outputs
    ) -> None:  # type: ignore
        """Process parser entry and extract keyboard/speech data."""
        if entry.module.startswith("inputCore.InputManager") and "Input:" in message:
            kb_input = self.parser.parse_keyboard_input(message, entry.timestamp)
            if kb_input:
                keyboard_inputs.append(kb_input)

        if entry.module.startswith("speech.speech.speak") and "Speaking:" in message:
            speech = self.parser.parse_speech_output(message, entry.timestamp)
            if speech:
                speech_outputs.append(speech)

    def poll(self) -> None:
        """Poll for new log entries and process correlations.

        Call this method repeatedly in a loop to monitor the log file.
        """
        # Read new entries
        keyboard_inputs, speech_outputs = self.read_new_entries()

        # Add to pending buffers
        for kb_input in keyboard_inputs:
            self._pending_actions.append(kb_input)
            if self._on_keyboard_callback:
                self._on_keyboard_callback(kb_input)

        for speech in speech_outputs:
            self._pending_speeches.append(speech)
            if self._on_speech_callback:
                self._on_speech_callback(speech)

        # Process correlations
        self._process_pending_correlations()

    def _process_pending_correlations(self, force: bool = False) -> None:
        """Correlate pending keyboard actions with speech outputs.

        Args:
            force: Force correlation of all pending actions (on shutdown)
        """
        now = datetime.now()

        # Process each pending action
        actions_to_remove: list[KeyboardInput] = []

        for action in self._pending_actions:
            # Find first speech after this action
            matching_speech: SpeechOutput | None = None

            for speech in self._pending_speeches:
                if speech.timestamp > action.timestamp:
                    matching_speech = speech
                    break

            if matching_speech:
                # Calculate latency
                latency_ms = (
                    matching_speech.timestamp - action.timestamp
                ).total_seconds() * 1000

                # Create correlated event
                event = CorrelatedEvent(
                    action=action,
                    output=matching_speech,
                    latency_ms=latency_ms,
                    success=True,
                    timeout=False,
                )

                self.correlated_events.append(event)
                actions_to_remove.append(action)
                self._pending_speeches.remove(matching_speech)

                if self._on_correlated_callback:
                    self._on_correlated_callback(event)

            else:
                # Check timeout
                elapsed = (now - action.timestamp).total_seconds()

                if force or elapsed > self.correlation_timeout:
                    # Timeout - no speech detected
                    event = CorrelatedEvent(
                        action=action,
                        output=None,
                        latency_ms=elapsed * 1000,
                        success=False,
                        timeout=True,
                    )

                    self.correlated_events.append(event)
                    actions_to_remove.append(action)

                    if self._on_correlated_callback:
                        self._on_correlated_callback(event)

        # Remove processed actions
        for action in actions_to_remove:
            self._pending_actions.remove(action)

    def get_output_after(
        self, timestamp: datetime, timeout: float = 2.0
    ) -> SpeechOutput | None:
        """Get the first speech output after a given timestamp.

        Polls the log file until speech is found or timeout reached.

        Args:
            timestamp: Timestamp to search after
            timeout: Maximum seconds to wait

        Returns:
            First SpeechOutput after timestamp, or None if timeout
        """
        start_time = time.time()

        while time.time() - start_time < timeout:
            keyboard_inputs, speech_outputs = self.read_new_entries()

            for speech in speech_outputs:
                if speech.timestamp > timestamp:
                    return speech

            time.sleep(self.poll_interval)

        return None

    def wait_for_idle(self, idle_time: float = 1.0, max_wait: float = 10.0) -> bool:
        """Wait for NVDA to become idle (no new log entries).

        Args:
            idle_time: Seconds of no activity to consider idle
            max_wait: Maximum seconds to wait

        Returns:
            True if became idle, False if timeout
        """
        start_time = time.time()
        last_activity = time.time()

        while time.time() - start_time < max_wait:
            keyboard_inputs, speech_outputs = self.read_new_entries()

            if keyboard_inputs or speech_outputs:
                last_activity = time.time()

            if time.time() - last_activity >= idle_time:
                return True

            time.sleep(self.poll_interval)

        return False

    def get_statistics(self) -> dict[str, int | float]:
        """Get monitoring statistics.

        Returns:
            Dictionary with statistics
        """
        total_events = len(self.correlated_events)
        successful = sum(1 for e in self.correlated_events if e.success)
        timeouts = sum(1 for e in self.correlated_events if e.timeout)

        avg_latency = 0.0
        if successful > 0:
            avg_latency = sum(
                e.latency_ms for e in self.correlated_events if e.success
            ) / successful

        return {
            "total_events": total_events,
            "successful_correlations": successful,
            "timeouts": timeouts,
            "average_latency_ms": avg_latency,
            "pending_actions": len(self._pending_actions),
            "pending_speeches": len(self._pending_speeches),
        }
