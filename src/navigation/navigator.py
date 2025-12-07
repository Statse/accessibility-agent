"""Navigator for coordinating web page navigation strategies."""

import logging
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from ..automation.keyboard_controller import KeyboardController, NVDAKey

logger = logging.getLogger(__name__)


class ElementType(str, Enum):
    """Types of elements that can be navigated."""

    HEADING = "heading"
    LINK = "link"
    LANDMARK = "landmark"
    FORM_FIELD = "form_field"
    BUTTON = "button"
    LIST = "list"
    GRAPHIC = "graphic"
    TABLE = "table"
    EDIT = "edit"  # Text input
    CHECKBOX = "checkbox"
    RADIO = "radio"
    COMBOBOX = "combobox"  # Dropdown
    UNKNOWN = "unknown"


class NavigationResult(BaseModel):
    """Result of a navigation action.

    Attributes:
        success: Whether navigation was successful
        element_type: Type of element reached (if known)
        nvda_output: What NVDA announced (if available)
        key_used: The key that was pressed
        error: Error message if navigation failed
    """

    model_config = ConfigDict(ser_json_timedelta="iso8601")

    success: bool
    element_type: ElementType = ElementType.UNKNOWN
    nvda_output: Optional[str] = None
    key_used: str
    error: Optional[str] = None


class Navigator:
    """Coordinates navigation strategies for web page exploration.

    This class provides high-level navigation methods that work with
    NVDA shortcuts and standard keyboard navigation. It abstracts the
    complexity of different navigation methods (headings, links, landmarks, etc.)
    into a unified interface.

    Attributes:
        keyboard_controller: Controller for sending keyboard input
    """

    def __init__(self, keyboard_controller: Optional[KeyboardController] = None):
        """Initialize the navigator.

        Args:
            keyboard_controller: Keyboard controller (creates new if None)
        """
        self.keyboard_controller = keyboard_controller or KeyboardController()
        logger.info("Navigator initialized")

    def navigate_to_next_heading(self, reverse: bool = False) -> NavigationResult:
        """Navigate to the next (or previous) heading on the page.

        Uses NVDA's 'h' shortcut (Shift+h for reverse).

        Args:
            reverse: If True, navigate to previous heading

        Returns:
            NavigationResult with outcome
        """
        try:
            if reverse:
                self.keyboard_controller.press_nvda_key(NVDAKey.H)  # Shift+h
                key_used = "H (Shift+h)"
            else:
                self.keyboard_controller.press_nvda_key(NVDAKey.h)
                key_used = "h"

            logger.debug(f"Navigated to {'previous' if reverse else 'next'} heading")

            return NavigationResult(
                success=True,
                element_type=ElementType.HEADING,
                key_used=key_used,
            )

        except Exception as e:
            logger.error(f"Error navigating to heading: {e}")
            return NavigationResult(
                success=False,
                key_used="h",
                error=str(e),
            )

    def navigate_to_next_link(self, reverse: bool = False) -> NavigationResult:
        """Navigate to the next (or previous) link on the page.

        Uses NVDA's 'k' shortcut (Shift+k for reverse).

        Args:
            reverse: If True, navigate to previous link

        Returns:
            NavigationResult with outcome
        """
        try:
            if reverse:
                self.keyboard_controller.press_nvda_key(NVDAKey.K)  # Shift+k
                key_used = "K (Shift+k)"
            else:
                self.keyboard_controller.press_nvda_key(NVDAKey.k)
                key_used = "k"

            logger.debug(f"Navigated to {'previous' if reverse else 'next'} link")

            return NavigationResult(
                success=True,
                element_type=ElementType.LINK,
                key_used=key_used,
            )

        except Exception as e:
            logger.error(f"Error navigating to link: {e}")
            return NavigationResult(
                success=False,
                key_used="k",
                error=str(e),
            )

    def navigate_to_next_landmark(self, reverse: bool = False) -> NavigationResult:
        """Navigate to the next (or previous) ARIA landmark on the page.

        Uses NVDA's 'd' shortcut (Shift+d for reverse).

        Args:
            reverse: If True, navigate to previous landmark

        Returns:
            NavigationResult with outcome
        """
        try:
            if reverse:
                self.keyboard_controller.press_nvda_key(NVDAKey.D)  # Shift+d
                key_used = "D (Shift+d)"
            else:
                self.keyboard_controller.press_nvda_key(NVDAKey.d)
                key_used = "d"

            logger.debug(f"Navigated to {'previous' if reverse else 'next'} landmark")

            return NavigationResult(
                success=True,
                element_type=ElementType.LANDMARK,
                key_used=key_used,
            )

        except Exception as e:
            logger.error(f"Error navigating to landmark: {e}")
            return NavigationResult(
                success=False,
                key_used="d",
                error=str(e),
            )

    def navigate_to_next_form_field(self, reverse: bool = False) -> NavigationResult:
        """Navigate to the next (or previous) form field on the page.

        Uses NVDA's 'f' shortcut (Shift+f for reverse).

        Args:
            reverse: If True, navigate to previous form field

        Returns:
            NavigationResult with outcome
        """
        try:
            if reverse:
                self.keyboard_controller.press_nvda_key(NVDAKey.F)  # Shift+f
                key_used = "F (Shift+f)"
            else:
                self.keyboard_controller.press_nvda_key(NVDAKey.f)
                key_used = "f"

            logger.debug(f"Navigated to {'previous' if reverse else 'next'} form field")

            return NavigationResult(
                success=True,
                element_type=ElementType.FORM_FIELD,
                key_used=key_used,
            )

        except Exception as e:
            logger.error(f"Error navigating to form field: {e}")
            return NavigationResult(
                success=False,
                key_used="f",
                error=str(e),
            )

    def navigate_to_next_button(self, reverse: bool = False) -> NavigationResult:
        """Navigate to the next (or previous) button on the page.

        Uses NVDA's 'b' shortcut (Shift+b for reverse).

        Args:
            reverse: If True, navigate to previous button

        Returns:
            NavigationResult with outcome
        """
        try:
            if reverse:
                self.keyboard_controller.press_nvda_key(NVDAKey.B)  # Shift+b
                key_used = "B (Shift+b)"
            else:
                self.keyboard_controller.press_nvda_key(NVDAKey.b)
                key_used = "b"

            logger.debug(f"Navigated to {'previous' if reverse else 'next'} button")

            return NavigationResult(
                success=True,
                element_type=ElementType.BUTTON,
                key_used=key_used,
            )

        except Exception as e:
            logger.error(f"Error navigating to button: {e}")
            return NavigationResult(
                success=False,
                key_used="b",
                error=str(e),
            )

    def navigate_to_next_list(self, reverse: bool = False) -> NavigationResult:
        """Navigate to the next (or previous) list on the page.

        Uses NVDA's 'l' shortcut (Shift+l for reverse).

        Args:
            reverse: If True, navigate to previous list

        Returns:
            NavigationResult with outcome
        """
        try:
            if reverse:
                self.keyboard_controller.press_nvda_key(NVDAKey.L)  # Shift+l
                key_used = "L (Shift+l)"
            else:
                self.keyboard_controller.press_nvda_key(NVDAKey.l)
                key_used = "l"

            logger.debug(f"Navigated to {'previous' if reverse else 'next'} list")

            return NavigationResult(
                success=True,
                element_type=ElementType.LIST,
                key_used=key_used,
            )

        except Exception as e:
            logger.error(f"Error navigating to list: {e}")
            return NavigationResult(
                success=False,
                key_used="l",
                error=str(e),
            )

    def navigate_sequential(self, reverse: bool = False) -> NavigationResult:
        """Navigate sequentially through focusable elements.

        Uses Tab (or Shift+Tab for reverse) to move through elements.

        Args:
            reverse: If True, navigate backwards

        Returns:
            NavigationResult with outcome
        """
        try:
            if reverse:
                self.keyboard_controller.press_shift_tab()
                key_used = "Shift+Tab"
            else:
                self.keyboard_controller.press_tab()
                key_used = "Tab"

            logger.debug(f"Sequential navigation: {key_used}")

            return NavigationResult(
                success=True,
                element_type=ElementType.UNKNOWN,
                key_used=key_used,
            )

        except Exception as e:
            logger.error(f"Error in sequential navigation: {e}")
            return NavigationResult(
                success=False,
                key_used="Tab",
                error=str(e),
            )

    def activate_element(self) -> NavigationResult:
        """Activate the currently focused element.

        Presses Enter to activate links, buttons, etc.

        Returns:
            NavigationResult with outcome
        """
        try:
            self.keyboard_controller.press_enter()
            logger.debug("Activated element with Enter")

            return NavigationResult(
                success=True,
                key_used="Enter",
            )

        except Exception as e:
            logger.error(f"Error activating element: {e}")
            return NavigationResult(
                success=False,
                key_used="Enter",
                error=str(e),
            )

    def toggle_element(self) -> NavigationResult:
        """Toggle the currently focused element.

        Presses Space to toggle checkboxes, radio buttons, etc.

        Returns:
            NavigationResult with outcome
        """
        try:
            self.keyboard_controller.press_space()
            logger.debug("Toggled element with Space")

            return NavigationResult(
                success=True,
                key_used="Space",
            )

        except Exception as e:
            logger.error(f"Error toggling element: {e}")
            return NavigationResult(
                success=False,
                key_used="Space",
                error=str(e),
            )

    def read_page_title(self) -> NavigationResult:
        """Read the page title using NVDA.

        Uses Insert+T to announce the page title.

        Returns:
            NavigationResult with outcome
        """
        try:
            self.keyboard_controller.press_nvda_read_title()
            logger.debug("Read page title")

            return NavigationResult(
                success=True,
                key_used="Insert+t",
            )

        except Exception as e:
            logger.error(f"Error reading page title: {e}")
            return NavigationResult(
                success=False,
                key_used="Insert+t",
                error=str(e),
            )

    def read_from_cursor(self) -> NavigationResult:
        """Read from current cursor position to end of page.

        Uses Insert+Down (NVDA Say All command).

        Returns:
            NavigationResult with outcome
        """
        try:
            self.keyboard_controller.press_nvda_say_all()
            logger.debug("Started Say All from cursor")

            return NavigationResult(
                success=True,
                key_used="Insert+Down",
            )

        except Exception as e:
            logger.error(f"Error reading from cursor: {e}")
            return NavigationResult(
                success=False,
                key_used="Insert+Down",
                error=str(e),
            )

    @staticmethod
    def parse_element_type(nvda_output: str) -> ElementType:
        """Parse NVDA output to determine element type.

        Args:
            nvda_output: Text announced by NVDA

        Returns:
            Detected ElementType
        """
        if not nvda_output:
            return ElementType.UNKNOWN

        nvda_lower = nvda_output.lower()

        # Check for specific element type indicators
        type_map = {
            "heading": ElementType.HEADING,
            "link": ElementType.LINK,
            "landmark": ElementType.LANDMARK,
            "navigation": ElementType.LANDMARK,
            "main": ElementType.LANDMARK,
            "banner": ElementType.LANDMARK,
            "button": ElementType.BUTTON,
            "edit": ElementType.EDIT,
            "text field": ElementType.EDIT,
            "input": ElementType.EDIT,
            "checkbox": ElementType.CHECKBOX,
            "radio button": ElementType.RADIO,
            "combo box": ElementType.COMBOBOX,
            "dropdown": ElementType.COMBOBOX,
            "list": ElementType.LIST,
            "graphic": ElementType.GRAPHIC,
            "image": ElementType.GRAPHIC,
            "table": ElementType.TABLE,
        }

        for keyword, element_type in type_map.items():
            if keyword in nvda_lower:
                return element_type

        return ElementType.UNKNOWN

    @staticmethod
    def is_interactive(element_type: ElementType) -> bool:
        """Check if an element type is interactive.

        Args:
            element_type: The element type to check

        Returns:
            True if the element is interactive, False otherwise
        """
        interactive_types = {
            ElementType.LINK,
            ElementType.BUTTON,
            ElementType.EDIT,
            ElementType.CHECKBOX,
            ElementType.RADIO,
            ElementType.COMBOBOX,
        }

        return element_type in interactive_types
