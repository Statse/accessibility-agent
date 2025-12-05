"""Unit tests for NVDA log parser."""

from datetime import datetime
from pathlib import Path

import pytest

from src.screen_reader.nvda_parser import KeyboardInput, NVDALogParser, SpeechOutput


class TestNVDALogParser:
    """Test suite for NVDALogParser."""

    @pytest.fixture
    def parser(self) -> NVDALogParser:
        """Create a parser instance."""
        return NVDALogParser(base_date=datetime(2025, 12, 5).date())

    def test_parse_timestamp(self, parser: NVDALogParser) -> None:
        """Test timestamp parsing with milliseconds."""
        result = parser.parse_timestamp("14:23:45.123")

        assert result.hour == 14
        assert result.minute == 23
        assert result.second == 45
        assert result.microsecond == 123000

    def test_parse_keyboard_input_tab(self, parser: NVDALogParser) -> None:
        """Test parsing Tab key input."""
        line = "Input: kb(desktop):tab"
        timestamp = datetime.now()

        result = parser.parse_keyboard_input(line, timestamp)

        assert result is not None
        assert result.key == "tab"
        assert result.modifiers == []
        assert result.raw_input == "tab"

    def test_parse_keyboard_input_shift_tab(self, parser: NVDALogParser) -> None:
        """Test parsing Shift+Tab key input."""
        line = "Input: kb(desktop):shift+tab"
        timestamp = datetime.now()

        result = parser.parse_keyboard_input(line, timestamp)

        assert result is not None
        assert result.key == "tab"
        assert result.modifiers == ["shift"]
        assert result.key_combination == "shift+tab"

    def test_parse_keyboard_input_ctrl_shift_enter(self, parser: NVDALogParser) -> None:
        """Test parsing Ctrl+Shift+Enter key input."""
        line = "Input: kb(desktop):control+shift+enter"
        timestamp = datetime.now()

        result = parser.parse_keyboard_input(line, timestamp)

        assert result is not None
        assert result.key == "enter"
        assert "control" in result.modifiers
        assert "shift" in result.modifiers

    def test_parse_keyboard_input_no_match(self, parser: NVDALogParser) -> None:
        """Test parsing line with no keyboard input."""
        line = "Some other log message"
        timestamp = datetime.now()

        result = parser.parse_keyboard_input(line, timestamp)

        assert result is None

    def test_parse_speech_output_simple(self, parser: NVDALogParser) -> None:
        """Test parsing simple speech output."""
        line = "Speaking: [u'Login button']"
        timestamp = datetime.now()

        result = parser.parse_speech_output(line, timestamp)

        assert result is not None
        assert result.text_parts == ["Login button"]
        assert result.full_text == "Login button"

    def test_parse_speech_output_multiple_parts(self, parser: NVDALogParser) -> None:
        """Test parsing speech with multiple parts."""
        line = "Speaking: [u'Email', u'edit', u'blank']"
        timestamp = datetime.now()

        result = parser.parse_speech_output(line, timestamp)

        assert result is not None
        assert result.text_parts == ["Email", "edit", "blank"]
        assert result.full_text == "Email edit blank"

    def test_parse_speech_output_multiline(self, parser: NVDALogParser) -> None:
        """Test parsing multi-line speech output."""
        line = """Speaking: [u'Welcome to our website',
 u'heading',
 u'level 1']"""
        timestamp = datetime.now()

        result = parser.parse_speech_output(line, timestamp)

        assert result is not None
        assert "Welcome to our website" in result.text_parts
        assert "heading" in result.text_parts
        assert "level 1" in result.text_parts

    def test_parse_speech_output_no_unicode_prefix(self, parser: NVDALogParser) -> None:
        """Test parsing speech without u prefix."""
        line = "Speaking: ['Submit', 'button']"
        timestamp = datetime.now()

        result = parser.parse_speech_output(line, timestamp)

        assert result is not None
        assert result.text_parts == ["Submit", "button"]

    def test_parse_speech_output_empty(self, parser: NVDALogParser) -> None:
        """Test parsing empty speech output."""
        line = "Speaking: []"
        timestamp = datetime.now()

        result = parser.parse_speech_output(line, timestamp)

        assert result is None

    def test_parse_line_keyboard_input(self, parser: NVDALogParser) -> None:
        """Test parsing complete log line with keyboard input."""
        line = "IO - inputCore.InputManager.executeGesture (14:23:45.123) MainThread (INFO):"

        entry, message = parser.parse_line(line)

        assert entry is not None
        assert entry.level == "IO"
        assert entry.module == "inputCore.InputManager.executeGesture"
        assert entry.thread == "MainThread"
        assert entry.timestamp.hour == 14
        assert entry.timestamp.minute == 23
        assert entry.timestamp.second == 45

    def test_parse_line_speech_output(self, parser: NVDALogParser) -> None:
        """Test parsing complete log line with speech."""
        line = "DEBUG - speech.speech.speak (14:23:45.234) MainThread (DEBUG):"

        entry, message = parser.parse_line(line)

        assert entry is not None
        assert entry.level == "DEBUG"
        assert entry.module == "speech.speech.speak"
        assert entry.thread == "MainThread"

    def test_parse_line_invalid(self, parser: NVDALogParser) -> None:
        """Test parsing invalid log line."""
        line = "This is not a valid log line"

        entry, message = parser.parse_line(line)

        assert entry is None
        assert message == line

    def test_parse_log_file(self, parser: NVDALogParser, tmp_path: Path) -> None:
        """Test parsing complete log file."""
        # Create test log file
        log_file = tmp_path / "test_nvda.log"
        log_content = """IO - inputCore.InputManager.executeGesture (14:23:45.123) MainThread (INFO):
Input: kb(desktop):tab

DEBUG - speech.speech.speak (14:23:45.234) MainThread (DEBUG):
Speaking: [u'Email', u'edit', u'blank']

IO - inputCore.InputManager.executeGesture (14:23:47.456) MainThread (INFO):
Input: kb(desktop):tab

DEBUG - speech.speech.speak (14:23:47.567) MainThread (DEBUG):
Speaking: [u'Password', u'edit', u'password']

IO - inputCore.InputManager.executeGesture (14:23:50.789) MainThread (INFO):
Input: kb(desktop):enter

DEBUG - speech.speech.speak (14:23:50.890) MainThread (DEBUG):
Speaking: [u'Sign in', u'button']
"""
        log_file.write_text(log_content)

        # Parse log file
        keyboard_inputs, speech_outputs = parser.parse_log_file(str(log_file))

        # Verify keyboard inputs
        assert len(keyboard_inputs) == 3
        assert keyboard_inputs[0].key == "tab"
        assert keyboard_inputs[1].key == "tab"
        assert keyboard_inputs[2].key == "enter"

        # Verify speech outputs
        assert len(speech_outputs) == 3
        assert "Email" in speech_outputs[0].text_parts
        assert "Password" in speech_outputs[1].text_parts
        assert "Sign in" in speech_outputs[2].text_parts

    def test_parse_log_file_from_line(self, parser: NVDALogParser, tmp_path: Path) -> None:
        """Test parsing log file starting from specific line."""
        log_file = tmp_path / "test_nvda.log"
        log_content = """Line 1
Line 2
Line 3
IO - inputCore.InputManager.executeGesture (14:23:45.123) MainThread (INFO):
Input: kb(desktop):tab

DEBUG - speech.speech.speak (14:23:45.234) MainThread (DEBUG):
Speaking: [u'Test']
"""
        log_file.write_text(log_content)

        # Parse from line 3 (skip first 3 lines)
        keyboard_inputs, speech_outputs = parser.parse_log_file(str(log_file), from_line=3)

        assert len(keyboard_inputs) == 1
        assert len(speech_outputs) == 1

    def test_keyboard_input_key_combination_property(self) -> None:
        """Test KeyboardInput key_combination property."""
        kb_simple = KeyboardInput(
            timestamp=datetime.now(),
            key="tab",
            modifiers=[],
            raw_input="tab",
        )
        assert kb_simple.key_combination == "tab"

        kb_complex = KeyboardInput(
            timestamp=datetime.now(),
            key="enter",
            modifiers=["ctrl", "shift"],
            raw_input="ctrl+shift+enter",
        )
        assert kb_complex.key_combination == "ctrl+shift+enter"

    def test_speech_output_full_text_property(self) -> None:
        """Test SpeechOutput full_text property."""
        speech = SpeechOutput(
            timestamp=datetime.now(),
            text_parts=["Login", "button", "unavailable"],
            raw_speech="test",
        )
        assert speech.full_text == "Login button unavailable"


@pytest.mark.integration
class TestNVDALogParserIntegration:
    """Integration tests for NVDA parser with real-world log samples."""

    @pytest.fixture
    def parser(self) -> NVDALogParser:
        """Create a parser instance."""
        return NVDALogParser()

    def test_parse_complex_navigation_sequence(self, parser: NVDALogParser, tmp_path: Path) -> None:
        """Test parsing complex navigation sequence with headings."""
        log_file = tmp_path / "complex_nvda.log"
        log_content = """IO - inputCore.InputManager.executeGesture (10:00:00.000) MainThread (INFO):
Input: kb(desktop):h

DEBUG - speech.speech.speak (10:00:00.100) MainThread (DEBUG):
Speaking: [u'Main navigation', u'heading', u'level 2']

IO - inputCore.InputManager.executeGesture (10:00:01.000) MainThread (INFO):
Input: kb(desktop):h

DEBUG - speech.speech.speak (10:00:01.100) MainThread (DEBUG):
Speaking: [u'Products', u'heading', u'level 2']

IO - inputCore.InputManager.executeGesture (10:00:02.000) MainThread (INFO):
Input: kb(desktop):k

DEBUG - speech.speech.speak (10:00:02.100) MainThread (DEBUG):
Speaking: [u'View details', u'link']
"""
        log_file.write_text(log_content)

        keyboard_inputs, speech_outputs = parser.parse_log_file(str(log_file))

        # Verify navigation keys
        assert len(keyboard_inputs) == 3
        assert keyboard_inputs[0].key == "h"  # Heading navigation
        assert keyboard_inputs[1].key == "h"
        assert keyboard_inputs[2].key == "k"  # Link navigation

        # Verify speech includes element types
        assert len(speech_outputs) == 3
        assert "heading" in speech_outputs[0].text_parts
        assert "link" in speech_outputs[2].text_parts
