"""Keyboard controller for sending OS-level keystrokes using pynput.

This module provides a KeyboardController class for simulating keyboard input
at the operating system level. It supports basic keys, arrow keys, special keys,
and NVDA screen reader shortcuts.
"""

import logging
import time
from enum import Enum
from typing import Optional

from pynput.keyboard import Controller, Key


logger = logging.getLogger(__name__)


class NVDAKey(Enum):
    """NVDA navigation keys for screen reader shortcuts."""

    NEXT_HEADING = "h"
    PREV_HEADING = "H"
    NEXT_LINK = "k"
    PREV_LINK = "K"
    NEXT_LANDMARK = "d"
    PREV_LANDMARK = "D"
    NEXT_FORM_FIELD = "f"
    PREV_FORM_FIELD = "F"
    NEXT_BUTTON = "b"
    PREV_BUTTON = "B"
    NEXT_LIST = "l"
    PREV_LIST = "L"


class KeyboardController:
    """Controls keyboard input at the OS level using pynput.

    This controller sends keystrokes to the active window and supports
    configurable delays between key presses for reliable automation.

    Attributes:
        delay: Time in seconds to wait between keystrokes (default: 0.1)
        _controller: Internal pynput keyboard controller instance
    """

    def __init__(self, delay: float = 0.1) -> None:
        """Initialize the keyboard controller.

        Args:
            delay: Time in seconds to wait between keystrokes.
                Must be >= 0. Default is 0.1 seconds.

        Raises:
            ValueError: If delay is negative.
        """
        if delay < 0:
            raise ValueError(f"Delay must be non-negative, got {delay}")

        self.delay = delay
        self._controller = Controller()
        logger.info(f"KeyboardController initialized with delay={delay}s")

    def press_key(self, key: str | Key, log: bool = True) -> None:
        """Press and release a single key.

        Args:
            key: Key to press. Can be a string (e.g., 'a', 'tab') or
                pynput Key enum (e.g., Key.tab, Key.enter).
            log: Whether to log this action (default: True).
        """
        timestamp = time.time()

        # Convert string keys to Key enum if needed
        if isinstance(key, str):
            key_lower = key.lower()
            # Map common string representations to Key enum
            key_map = {
                "tab": Key.tab,
                "enter": Key.enter,
                "return": Key.enter,
                "space": Key.space,
                "escape": Key.esc,
                "esc": Key.esc,
                "backspace": Key.backspace,
                "delete": Key.delete,
                "up": Key.up,
                "down": Key.down,
                "left": Key.left,
                "right": Key.right,
                "home": Key.home,
                "end": Key.end,
                "pageup": Key.page_up,
                "pagedown": Key.page_down,
                "insert": Key.insert,
            }

            if key_lower in key_map:
                key_to_press = key_map[key_lower]
            else:
                # Single character key
                key_to_press = key
        else:
            key_to_press = key

        # Press and release the key
        self._controller.press(key_to_press)
        self._controller.release(key_to_press)

        if log:
            logger.info(
                "Keyboard action",
                extra={
                    "key": str(key),
                    "timestamp": timestamp,
                    "action": "press",
                },
            )

        time.sleep(self.delay)

    def press_tab(self) -> None:
        """Press Tab key to navigate to next focusable element."""
        self.press_key(Key.tab)

    def press_shift_tab(self) -> None:
        """Press Shift+Tab to navigate to previous focusable element."""
        self.press_combination([Key.shift, Key.tab])

    def press_enter(self) -> None:
        """Press Enter key to activate element."""
        self.press_key(Key.enter)

    def press_space(self) -> None:
        """Press Space key to toggle checkbox or activate button."""
        self.press_key(Key.space)

    def press_escape(self) -> None:
        """Press Escape key to close dialog or cancel action."""
        self.press_key(Key.esc)

    def press_arrow_up(self) -> None:
        """Press Up arrow key."""
        self.press_key(Key.up)

    def press_arrow_down(self) -> None:
        """Press Down arrow key."""
        self.press_key(Key.down)

    def press_arrow_left(self) -> None:
        """Press Left arrow key."""
        self.press_key(Key.left)

    def press_arrow_right(self) -> None:
        """Press Right arrow key."""
        self.press_key(Key.right)

    def press_combination(self, keys: list[str | Key], log: bool = True) -> None:
        """Press a combination of keys simultaneously (e.g., Ctrl+F).

        Args:
            keys: List of keys to press together. Each key can be a string
                or pynput Key enum. Example: [Key.ctrl, 'f'] for Ctrl+F.
            log: Whether to log this action (default: True).

        Example:
            controller.press_combination([Key.ctrl, 'f'])  # Ctrl+F
            controller.press_combination([Key.insert, Key.down])  # Insert+Down
        """
        timestamp = time.time()

        # Convert string keys to proper format
        processed_keys = []
        for key in keys:
            if isinstance(key, str):
                key_lower = key.lower()
                key_map = {
                    "ctrl": Key.ctrl,
                    "control": Key.ctrl,
                    "shift": Key.shift,
                    "alt": Key.alt,
                    "cmd": Key.cmd,
                    "win": Key.cmd,
                    "windows": Key.cmd,
                    "insert": Key.insert,
                    "tab": Key.tab,
                    "enter": Key.enter,
                    "space": Key.space,
                    "escape": Key.esc,
                    "up": Key.up,
                    "down": Key.down,
                    "left": Key.left,
                    "right": Key.right,
                    "t": "t",
                    "f": "f",
                }
                processed_keys.append(key_map.get(key_lower, key))
            else:
                processed_keys.append(key)

        # Press all keys
        for key in processed_keys:
            self._controller.press(key)

        # Release all keys in reverse order
        for key in reversed(processed_keys):
            self._controller.release(key)

        if log:
            key_names = "+".join(str(k) for k in keys)
            logger.info(
                "Keyboard action",
                extra={
                    "key": key_names,
                    "timestamp": timestamp,
                    "action": "combination",
                },
            )

        time.sleep(self.delay)

    def press_nvda_key(self, nvda_key: NVDAKey) -> None:
        """Press an NVDA navigation key.

        Args:
            nvda_key: NVDA key from NVDAKey enum.

        Example:
            controller.press_nvda_key(NVDAKey.NEXT_HEADING)  # Press H
            controller.press_nvda_key(NVDAKey.PREV_LINK)     # Press Shift+K
        """
        key_value = nvda_key.value

        # Check if uppercase (indicates Shift+ combination)
        if key_value.isupper():
            self.press_combination([Key.shift, key_value.lower()])
        else:
            self.press_key(key_value)

    def press_nvda_say_all(self) -> None:
        """Press Insert+Down to make NVDA read from current position."""
        self.press_combination([Key.insert, Key.down])

    def press_nvda_read_title(self) -> None:
        """Press Insert+T to make NVDA announce page title."""
        self.press_combination([Key.insert, "t"])

    def press_ctrl_f(self) -> None:
        """Press Ctrl+F to open find dialog."""
        self.press_combination([Key.ctrl, "f"])

    def type_text(self, text: str, log: bool = True) -> None:
        """Type a string of text character by character.

        Args:
            text: Text to type.
            log: Whether to log this action (default: True).

        Example:
            controller.type_text("john.doe@example.com")
        """
        timestamp = time.time()

        for char in text:
            self._controller.press(char)
            self._controller.release(char)
            time.sleep(self.delay)

        if log:
            logger.info(
                "Keyboard action",
                extra={
                    "text": text,
                    "timestamp": timestamp,
                    "action": "type",
                },
            )

    def set_delay(self, delay: float) -> None:
        """Update the delay between keystrokes.

        Args:
            delay: New delay in seconds. Must be >= 0.

        Raises:
            ValueError: If delay is negative.
        """
        if delay < 0:
            raise ValueError(f"Delay must be non-negative, got {delay}")

        old_delay = self.delay
        self.delay = delay
        logger.info(f"Keyboard delay updated from {old_delay}s to {delay}s")
