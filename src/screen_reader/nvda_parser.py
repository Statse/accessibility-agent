"""NVDA log parser for extracting keyboard inputs and speech outputs.

Parses NVDA log files to extract:
- Keyboard actions (Tab, Enter, NVDA navigation keys)
- Speech output (what NVDA announces)
- Timestamps with millisecond precision
"""

import re
from datetime import datetime, time
from typing import Literal

from pydantic import BaseModel, Field


LogLevel = Literal["DEBUG", "INFO", "IO", "WARNING", "ERROR"]


class KeyboardInput(BaseModel):
    """Represents a keyboard input event from NVDA log."""

    timestamp: datetime
    key: str
    modifiers: list[str] = Field(default_factory=list)
    raw_input: str

    @property
    def key_combination(self) -> str:
        """Get the full key combination string."""
        if self.modifiers:
            return "+".join(self.modifiers + [self.key])
        return self.key


class SpeechOutput(BaseModel):
    """Represents speech output from NVDA."""

    timestamp: datetime
    text_parts: list[str]
    raw_speech: str

    @property
    def full_text(self) -> str:
        """Get the full speech text as a single string."""
        return " ".join(self.text_parts)


class LogEntry(BaseModel):
    """Represents a generic log entry."""

    timestamp: datetime
    level: LogLevel
    module: str
    thread: str
    message: str


class NVDALogParser:
    """Parser for NVDA log files."""

    # Regex patterns
    LOG_PATTERN = re.compile(
        r"^(DEBUG|INFO|IO|WARNING|ERROR)\s+-\s+"
        r"([\w.]+)\s+"
        r"\((\d{2}:\d{2}:\d{2}\.\d{3})\)\s+"
        r"(\w+)\s+"
        r"\((DEBUG|INFO|IO|WARNING|ERROR)\):"
    )

    KEYBOARD_INPUT_PATTERN = re.compile(r"Input:\s+kb\([^)]+\):(.+)")

    SPEECH_PATTERN = re.compile(r"Speaking:\s+\[(.+?)\]", re.DOTALL)

    def __init__(self, base_date: datetime | None = None):
        """Initialize NVDA log parser.

        Args:
            base_date: Base date for timestamps (defaults to today).
                       NVDA logs only contain time, not date.
        """
        self.base_date = base_date or datetime.now().date()

    def parse_timestamp(self, time_str: str) -> datetime:
        """Parse timestamp from NVDA log format (HH:MM:SS.mmm).

        Args:
            time_str: Time string in format "HH:MM:SS.mmm"

        Returns:
            datetime object with millisecond precision

        Example:
            >>> parser = NVDALogParser()
            >>> dt = parser.parse_timestamp("14:23:45.123")
            >>> print(dt.time())
            14:23:45.123000
        """
        # Parse time components
        time_obj = datetime.strptime(time_str, "%H:%M:%S.%f").time()

        # Combine with base date
        return datetime.combine(self.base_date, time_obj)

    def parse_keyboard_input(self, line: str, timestamp: datetime) -> KeyboardInput | None:
        """Parse keyboard input from log line.

        Args:
            line: Log message line
            timestamp: Timestamp of the log entry

        Returns:
            KeyboardInput object if line contains keyboard input, None otherwise

        Example:
            >>> parser = NVDALogParser()
            >>> ts = datetime.now()
            >>> kb = parser.parse_keyboard_input("Input: kb(desktop):shift+tab", ts)
            >>> print(kb.key)
            'tab'
            >>> print(kb.modifiers)
            ['shift']
        """
        match = self.KEYBOARD_INPUT_PATTERN.search(line)
        if not match:
            return None

        raw_input = match.group(1).strip()

        # Parse modifiers and key
        parts = raw_input.split("+")
        if len(parts) > 1:
            modifiers = [p.lower() for p in parts[:-1]]
            key = parts[-1].lower()
        else:
            modifiers = []
            key = raw_input.lower()

        return KeyboardInput(
            timestamp=timestamp,
            key=key,
            modifiers=modifiers,
            raw_input=raw_input,
        )

    def parse_speech_output(self, line: str, timestamp: datetime) -> SpeechOutput | None:
        """Parse speech output from log line.

        Args:
            line: Log message line (can be multi-line)
            timestamp: Timestamp of the log entry

        Returns:
            SpeechOutput object if line contains speech, None otherwise

        Example:
            >>> parser = NVDALogParser()
            >>> ts = datetime.now()
            >>> speech = parser.parse_speech_output("Speaking: [u'Login', u'button']", ts)
            >>> print(speech.text_parts)
            ['Login', 'button']
            >>> print(speech.full_text)
            'Login button'
        """
        match = self.SPEECH_PATTERN.search(line)
        if not match:
            return None

        raw_speech = match.group(1)

        # Extract text parts from speech array
        # Handle both u'text' and 'text' formats
        text_parts: list[str] = []

        # Match quoted strings
        quote_pattern = re.compile(r"u?['\"]([^'\"]*)['\"]")
        for match in quote_pattern.finditer(raw_speech):
            text = match.group(1)
            if text:  # Skip empty strings
                text_parts.append(text)

        if not text_parts:
            return None

        return SpeechOutput(
            timestamp=timestamp,
            text_parts=text_parts,
            raw_speech=raw_speech,
        )

    def parse_line(self, line: str) -> tuple[LogEntry | None, str]:
        """Parse a single log line.

        Args:
            line: Raw log line

        Returns:
            Tuple of (LogEntry or None, remaining message text)
            Returns (None, line) if line doesn't match log format

        Example:
            >>> parser = NVDALogParser()
            >>> entry, msg = parser.parse_line(
            ...     "IO - inputCore.InputManager (14:23:45.123) MainThread (INFO):"
            ... )
            >>> print(entry.level)
            'IO'
            >>> print(entry.timestamp.time())
            14:23:45.123000
        """
        match = self.LOG_PATTERN.match(line)
        if not match:
            return None, line

        level_str, module, time_str, thread, _ = match.groups()

        # Parse timestamp
        timestamp = self.parse_timestamp(time_str)

        # Extract message (everything after the matched pattern)
        message = line[match.end() :].strip()

        return (
            LogEntry(
                timestamp=timestamp,
                level=level_str,  # type: ignore
                module=module,
                thread=thread,
                message=message,
            ),
            message,
        )

    def parse_log_file(
        self, file_path: str, from_line: int = 0
    ) -> tuple[list[KeyboardInput], list[SpeechOutput]]:
        """Parse entire log file and extract keyboard inputs and speech outputs.

        Args:
            file_path: Path to NVDA log file
            from_line: Start parsing from this line number (0-indexed)

        Returns:
            Tuple of (keyboard_inputs, speech_outputs)

        Raises:
            FileNotFoundError: If log file doesn't exist

        Example:
            >>> parser = NVDALogParser()
            >>> kb_inputs, speeches = parser.parse_log_file("nvda.log")
            >>> print(f"Found {len(kb_inputs)} keyboard actions")
            >>> print(f"Found {len(speeches)} speech outputs")
        """
        keyboard_inputs: list[KeyboardInput] = []
        speech_outputs: list[SpeechOutput] = []

        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()

        # Skip to from_line
        lines = lines[from_line:]

        current_entry: LogEntry | None = None
        accumulated_message = ""

        for line in lines:
            line = line.rstrip()

            # Try to parse as new log entry
            entry, message = self.parse_line(line)

            if entry:
                # Process previous accumulated entry
                if current_entry and accumulated_message:
                    self._process_entry(
                        current_entry, accumulated_message, keyboard_inputs, speech_outputs
                    )

                # Start new entry
                current_entry = entry
                accumulated_message = message
            else:
                # Continuation line (indented or part of multi-line message)
                if current_entry:
                    accumulated_message += "\n" + line

        # Process last entry
        if current_entry and accumulated_message:
            self._process_entry(
                current_entry, accumulated_message, keyboard_inputs, speech_outputs
            )

        return keyboard_inputs, speech_outputs

    def _process_entry(
        self,
        entry: LogEntry,
        message: str,
        keyboard_inputs: list[KeyboardInput],
        speech_outputs: list[SpeechOutput],
    ) -> None:
        """Process a log entry and extract keyboard/speech data.

        Args:
            entry: Parsed log entry
            message: Full message text (may be multi-line)
            keyboard_inputs: List to append keyboard inputs to
            speech_outputs: List to append speech outputs to
        """
        # Check for keyboard input
        if entry.module.startswith("inputCore.InputManager") and "Input:" in message:
            kb_input = self.parse_keyboard_input(message, entry.timestamp)
            if kb_input:
                keyboard_inputs.append(kb_input)

        # Check for speech output
        if entry.module.startswith("speech.speech.speak") and "Speaking:" in message:
            speech = self.parse_speech_output(message, entry.timestamp)
            if speech:
                speech_outputs.append(speech)
