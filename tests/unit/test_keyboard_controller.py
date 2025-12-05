"""Unit tests for keyboard_controller module."""

import time
from unittest.mock import MagicMock, Mock, call, patch

import pytest
from pynput.keyboard import Key

from src.automation.keyboard_controller import KeyboardController, NVDAKey


class TestKeyboardController:
    """Test suite for KeyboardController class."""

    @pytest.fixture
    def mock_controller(self):
        """Create a mock pynput Controller."""
        with patch("src.automation.keyboard_controller.Controller") as mock_ctrl:
            yield mock_ctrl

    @pytest.fixture
    def kb_controller(self, mock_controller):
        """Create a KeyboardController instance with mocked pynput."""
        return KeyboardController(delay=0.01)  # Small delay for tests

    def test_init_default_delay(self, mock_controller):
        """Test initialization with default delay."""
        controller = KeyboardController()
        assert controller.delay == 0.1
        mock_controller.assert_called_once()

    def test_init_custom_delay(self, mock_controller):
        """Test initialization with custom delay."""
        controller = KeyboardController(delay=0.5)
        assert controller.delay == 0.5

    def test_init_negative_delay_raises_error(self, mock_controller):
        """Test that negative delay raises ValueError."""
        with pytest.raises(ValueError, match="Delay must be non-negative"):
            KeyboardController(delay=-0.1)

    def test_press_key_with_string(self, kb_controller, mock_controller):
        """Test pressing a key using string representation."""
        kb_controller.press_key("tab")

        mock_ctrl = mock_controller.return_value
        mock_ctrl.press.assert_called_once_with(Key.tab)
        mock_ctrl.release.assert_called_once_with(Key.tab)

    def test_press_key_with_key_enum(self, kb_controller, mock_controller):
        """Test pressing a key using Key enum."""
        kb_controller.press_key(Key.enter)

        mock_ctrl = mock_controller.return_value
        mock_ctrl.press.assert_called_once_with(Key.enter)
        mock_ctrl.release.assert_called_once_with(Key.enter)

    def test_press_key_single_character(self, kb_controller, mock_controller):
        """Test pressing a single character key."""
        kb_controller.press_key("a")

        mock_ctrl = mock_controller.return_value
        mock_ctrl.press.assert_called_once_with("a")
        mock_ctrl.release.assert_called_once_with("a")

    @pytest.mark.parametrize(
        "key_string,expected_key",
        [
            ("tab", Key.tab),
            ("enter", Key.enter),
            ("space", Key.space),
            ("escape", Key.esc),
            ("esc", Key.esc),
            ("up", Key.up),
            ("down", Key.down),
            ("left", Key.left),
            ("right", Key.right),
            ("backspace", Key.backspace),
            ("delete", Key.delete),
            ("home", Key.home),
            ("end", Key.end),
            ("pageup", Key.page_up),
            ("pagedown", Key.page_down),
            ("insert", Key.insert),
        ],
    )
    def test_press_key_string_mapping(
        self, kb_controller, mock_controller, key_string, expected_key
    ):
        """Test that string keys are correctly mapped to Key enum."""
        kb_controller.press_key(key_string)

        mock_ctrl = mock_controller.return_value
        mock_ctrl.press.assert_called_once_with(expected_key)
        mock_ctrl.release.assert_called_once_with(expected_key)

    def test_press_tab(self, kb_controller, mock_controller):
        """Test press_tab convenience method."""
        kb_controller.press_tab()

        mock_ctrl = mock_controller.return_value
        mock_ctrl.press.assert_called_once_with(Key.tab)
        mock_ctrl.release.assert_called_once_with(Key.tab)

    def test_press_shift_tab(self, kb_controller, mock_controller):
        """Test press_shift_tab convenience method."""
        kb_controller.press_shift_tab()

        mock_ctrl = mock_controller.return_value
        # Should press Shift and Tab together
        assert mock_ctrl.press.call_count == 2
        assert mock_ctrl.release.call_count == 2

    def test_press_enter(self, kb_controller, mock_controller):
        """Test press_enter convenience method."""
        kb_controller.press_enter()

        mock_ctrl = mock_controller.return_value
        mock_ctrl.press.assert_called_once_with(Key.enter)

    def test_press_space(self, kb_controller, mock_controller):
        """Test press_space convenience method."""
        kb_controller.press_space()

        mock_ctrl = mock_controller.return_value
        mock_ctrl.press.assert_called_once_with(Key.space)

    def test_press_escape(self, kb_controller, mock_controller):
        """Test press_escape convenience method."""
        kb_controller.press_escape()

        mock_ctrl = mock_controller.return_value
        mock_ctrl.press.assert_called_once_with(Key.esc)

    def test_press_arrow_keys(self, kb_controller, mock_controller):
        """Test arrow key convenience methods."""
        mock_ctrl = mock_controller.return_value

        kb_controller.press_arrow_up()
        assert mock_ctrl.press.call_args[0][0] == Key.up

        kb_controller.press_arrow_down()
        assert mock_ctrl.press.call_args[0][0] == Key.down

        kb_controller.press_arrow_left()
        assert mock_ctrl.press.call_args[0][0] == Key.left

        kb_controller.press_arrow_right()
        assert mock_ctrl.press.call_args[0][0] == Key.right

    def test_press_combination(self, kb_controller, mock_controller):
        """Test pressing key combinations."""
        kb_controller.press_combination([Key.ctrl, "f"])

        mock_ctrl = mock_controller.return_value

        # Should press both keys
        assert mock_ctrl.press.call_count == 2
        assert mock_ctrl.release.call_count == 2

        # Check press order: Ctrl, then F
        press_calls = mock_ctrl.press.call_args_list
        assert press_calls[0] == call(Key.ctrl)
        assert press_calls[1] == call("f")

        # Check release order: F, then Ctrl (reversed)
        release_calls = mock_ctrl.release.call_args_list
        assert release_calls[0] == call("f")
        assert release_calls[1] == call(Key.ctrl)

    def test_press_combination_with_strings(self, kb_controller, mock_controller):
        """Test pressing combinations with string representations."""
        kb_controller.press_combination(["ctrl", "f"])

        mock_ctrl = mock_controller.return_value

        # Should convert "ctrl" to Key.ctrl
        press_calls = mock_ctrl.press.call_args_list
        assert press_calls[0] == call(Key.ctrl)
        assert press_calls[1] == call("f")

    def test_press_nvda_key_lowercase(self, kb_controller, mock_controller):
        """Test pressing NVDA navigation key (lowercase, no modifier)."""
        kb_controller.press_nvda_key(NVDAKey.NEXT_HEADING)

        mock_ctrl = mock_controller.return_value
        mock_ctrl.press.assert_called_once_with("h")

    def test_press_nvda_key_uppercase(self, kb_controller, mock_controller):
        """Test pressing NVDA navigation key (uppercase, with Shift)."""
        kb_controller.press_nvda_key(NVDAKey.PREV_HEADING)

        mock_ctrl = mock_controller.return_value

        # Should press Shift+H
        assert mock_ctrl.press.call_count == 2
        press_calls = mock_ctrl.press.call_args_list
        assert press_calls[0] == call(Key.shift)
        assert press_calls[1] == call("h")

    @pytest.mark.parametrize(
        "nvda_key,expected_key",
        [
            (NVDAKey.NEXT_HEADING, "h"),
            (NVDAKey.NEXT_LINK, "k"),
            (NVDAKey.NEXT_LANDMARK, "d"),
            (NVDAKey.NEXT_FORM_FIELD, "f"),
            (NVDAKey.NEXT_BUTTON, "b"),
            (NVDAKey.NEXT_LIST, "l"),
        ],
    )
    def test_nvda_key_enum_values(
        self, kb_controller, mock_controller, nvda_key, expected_key
    ):
        """Test NVDA key enum values are correct."""
        kb_controller.press_nvda_key(nvda_key)

        mock_ctrl = mock_controller.return_value
        mock_ctrl.press.assert_called_once_with(expected_key)

    def test_press_nvda_say_all(self, kb_controller, mock_controller):
        """Test NVDA Say All command (Insert+Down)."""
        kb_controller.press_nvda_say_all()

        mock_ctrl = mock_controller.return_value

        # Should press Insert and Down
        assert mock_ctrl.press.call_count == 2
        press_calls = mock_ctrl.press.call_args_list
        assert press_calls[0] == call(Key.insert)
        assert press_calls[1] == call(Key.down)

    def test_press_nvda_read_title(self, kb_controller, mock_controller):
        """Test NVDA Read Title command (Insert+T)."""
        kb_controller.press_nvda_read_title()

        mock_ctrl = mock_controller.return_value

        # Should press Insert and T
        assert mock_ctrl.press.call_count == 2
        press_calls = mock_ctrl.press.call_args_list
        assert press_calls[0] == call(Key.insert)
        assert press_calls[1] == call("t")

    def test_press_ctrl_f(self, kb_controller, mock_controller):
        """Test Ctrl+F shortcut."""
        kb_controller.press_ctrl_f()

        mock_ctrl = mock_controller.return_value

        # Should press Ctrl and F
        assert mock_ctrl.press.call_count == 2
        press_calls = mock_ctrl.press.call_args_list
        assert press_calls[0] == call(Key.ctrl)
        assert press_calls[1] == call("f")

    def test_type_text(self, kb_controller, mock_controller):
        """Test typing text character by character."""
        test_text = "hello"
        kb_controller.type_text(test_text)

        mock_ctrl = mock_controller.return_value

        # Should press and release each character
        assert mock_ctrl.press.call_count == len(test_text)
        assert mock_ctrl.release.call_count == len(test_text)

        # Check each character was pressed
        for i, char in enumerate(test_text):
            assert mock_ctrl.press.call_args_list[i] == call(char)
            assert mock_ctrl.release.call_args_list[i] == call(char)

    def test_type_text_empty_string(self, kb_controller, mock_controller):
        """Test typing empty string doesn't press any keys."""
        kb_controller.type_text("")

        mock_ctrl = mock_controller.return_value
        mock_ctrl.press.assert_not_called()
        mock_ctrl.release.assert_not_called()

    def test_set_delay(self, kb_controller):
        """Test updating delay value."""
        assert kb_controller.delay == 0.01

        kb_controller.set_delay(0.5)
        assert kb_controller.delay == 0.5

    def test_set_delay_negative_raises_error(self, kb_controller):
        """Test that setting negative delay raises ValueError."""
        with pytest.raises(ValueError, match="Delay must be non-negative"):
            kb_controller.set_delay(-0.1)

    def test_delay_is_applied(self, kb_controller, mock_controller):
        """Test that delay is actually applied between keystrokes."""
        kb_controller.set_delay(0.05)

        start_time = time.time()
        kb_controller.press_key("a")
        elapsed = time.time() - start_time

        # Should take at least the delay time
        assert elapsed >= 0.05

    def test_logging_disabled(self, kb_controller, mock_controller):
        """Test that logging can be disabled for a key press."""
        # This test just ensures the log parameter is accepted
        # Actual logging verification would require capturing log output
        kb_controller.press_key("a", log=False)

        mock_ctrl = mock_controller.return_value
        mock_ctrl.press.assert_called_once_with("a")


class TestNVDAKeyEnum:
    """Test suite for NVDAKey enum."""

    def test_nvda_key_values(self):
        """Test that NVDA key enum has correct values."""
        assert NVDAKey.NEXT_HEADING.value == "h"
        assert NVDAKey.PREV_HEADING.value == "H"
        assert NVDAKey.NEXT_LINK.value == "k"
        assert NVDAKey.PREV_LINK.value == "K"
        assert NVDAKey.NEXT_LANDMARK.value == "d"
        assert NVDAKey.PREV_LANDMARK.value == "D"
        assert NVDAKey.NEXT_FORM_FIELD.value == "f"
        assert NVDAKey.PREV_FORM_FIELD.value == "F"
        assert NVDAKey.NEXT_BUTTON.value == "b"
        assert NVDAKey.PREV_BUTTON.value == "B"
        assert NVDAKey.NEXT_LIST.value == "l"
        assert NVDAKey.PREV_LIST.value == "L"

    def test_nvda_key_uppercase_detection(self):
        """Test that uppercase values indicate Shift modifier."""
        # Lowercase keys (no modifier)
        assert not NVDAKey.NEXT_HEADING.value.isupper()
        assert not NVDAKey.NEXT_LINK.value.isupper()

        # Uppercase keys (Shift modifier)
        assert NVDAKey.PREV_HEADING.value.isupper()
        assert NVDAKey.PREV_LINK.value.isupper()
