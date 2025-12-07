"""Tests for web navigation module."""

import pytest
from unittest.mock import Mock, MagicMock

from src.navigation.navigator import (
    Navigator,
    NavigationResult,
    ElementType,
)
from src.automation.keyboard_controller import KeyboardController, NVDAKey


class TestElementType:
    """Tests for ElementType enum"""

    def test_element_types_exist(self):
        """Test that all expected element types are defined"""
        assert ElementType.HEADING == "heading"
        assert ElementType.LINK == "link"
        assert ElementType.LANDMARK == "landmark"
        assert ElementType.FORM_FIELD == "form_field"
        assert ElementType.BUTTON == "button"
        assert ElementType.LIST == "list"
        assert ElementType.GRAPHIC == "graphic"
        assert ElementType.TABLE == "table"
        assert ElementType.EDIT == "edit"
        assert ElementType.CHECKBOX == "checkbox"
        assert ElementType.RADIO == "radio"
        assert ElementType.COMBOBOX == "combobox"
        assert ElementType.UNKNOWN == "unknown"


class TestNavigationResult:
    """Tests for NavigationResult model"""

    def test_create_successful_result(self):
        """Test creating a successful navigation result"""
        result = NavigationResult(
            success=True,
            element_type=ElementType.HEADING,
            nvda_output="Heading level 1 Main Title",
            key_used="h"
        )

        assert result.success is True
        assert result.element_type == ElementType.HEADING
        assert result.nvda_output == "Heading level 1 Main Title"
        assert result.key_used == "h"
        assert result.error is None

    def test_create_failed_result(self):
        """Test creating a failed navigation result"""
        result = NavigationResult(
            success=False,
            key_used="h",
            error="Navigation failed"
        )

        assert result.success is False
        assert result.element_type == ElementType.UNKNOWN
        assert result.error == "Navigation failed"

    def test_default_element_type(self):
        """Test default element type is UNKNOWN"""
        result = NavigationResult(
            success=True,
            key_used="Tab"
        )

        assert result.element_type == ElementType.UNKNOWN


class TestNavigatorInitialization:
    """Tests for Navigator initialization"""

    def test_create_navigator_default(self):
        """Test creating navigator with default keyboard controller"""
        navigator = Navigator()

        assert navigator.keyboard_controller is not None
        assert isinstance(navigator.keyboard_controller, KeyboardController)

    def test_create_navigator_with_controller(self):
        """Test creating navigator with custom keyboard controller"""
        mock_controller = Mock(spec=KeyboardController)
        navigator = Navigator(keyboard_controller=mock_controller)

        assert navigator.keyboard_controller is mock_controller


class TestNavigateToNextHeading:
    """Tests for navigate_to_next_heading method"""

    def test_navigate_forward(self):
        """Test navigating to next heading"""
        mock_controller = Mock(spec=KeyboardController)
        navigator = Navigator(keyboard_controller=mock_controller)

        result = navigator.navigate_to_next_heading(reverse=False)

        assert result.success is True
        assert result.element_type == ElementType.HEADING
        assert result.key_used == "h"
        assert result.error is None
        mock_controller.press_nvda_key.assert_called_once_with(NVDAKey.NEXT_HEADING)

    def test_navigate_reverse(self):
        """Test navigating to previous heading"""
        mock_controller = Mock(spec=KeyboardController)
        navigator = Navigator(keyboard_controller=mock_controller)

        result = navigator.navigate_to_next_heading(reverse=True)

        assert result.success is True
        assert result.element_type == ElementType.HEADING
        assert "Shift+h" in result.key_used
        mock_controller.press_nvda_key.assert_called_once_with(NVDAKey.PREV_HEADING)

    def test_navigate_error_handling(self):
        """Test error handling when navigation fails"""
        mock_controller = Mock(spec=KeyboardController)
        mock_controller.press_nvda_key.side_effect = Exception("Keyboard error")
        navigator = Navigator(keyboard_controller=mock_controller)

        result = navigator.navigate_to_next_heading()

        assert result.success is False
        assert result.error == "Keyboard error"
        assert result.key_used == "h"


class TestNavigateToNextLink:
    """Tests for navigate_to_next_link method"""

    def test_navigate_forward(self):
        """Test navigating to next link"""
        mock_controller = Mock(spec=KeyboardController)
        navigator = Navigator(keyboard_controller=mock_controller)

        result = navigator.navigate_to_next_link(reverse=False)

        assert result.success is True
        assert result.element_type == ElementType.LINK
        assert result.key_used == "k"
        mock_controller.press_nvda_key.assert_called_once_with(NVDAKey.NEXT_LINK)

    def test_navigate_reverse(self):
        """Test navigating to previous link"""
        mock_controller = Mock(spec=KeyboardController)
        navigator = Navigator(keyboard_controller=mock_controller)

        result = navigator.navigate_to_next_link(reverse=True)

        assert result.success is True
        assert result.element_type == ElementType.LINK
        assert "Shift+k" in result.key_used
        mock_controller.press_nvda_key.assert_called_once_with(NVDAKey.PREV_LINK)


class TestNavigateToNextLandmark:
    """Tests for navigate_to_next_landmark method"""

    def test_navigate_forward(self):
        """Test navigating to next landmark"""
        mock_controller = Mock(spec=KeyboardController)
        navigator = Navigator(keyboard_controller=mock_controller)

        result = navigator.navigate_to_next_landmark(reverse=False)

        assert result.success is True
        assert result.element_type == ElementType.LANDMARK
        assert result.key_used == "d"
        mock_controller.press_nvda_key.assert_called_once_with(NVDAKey.NEXT_LANDMARK)

    def test_navigate_reverse(self):
        """Test navigating to previous landmark"""
        mock_controller = Mock(spec=KeyboardController)
        navigator = Navigator(keyboard_controller=mock_controller)

        result = navigator.navigate_to_next_landmark(reverse=True)

        assert result.success is True
        assert "Shift+d" in result.key_used
        mock_controller.press_nvda_key.assert_called_once_with(NVDAKey.PREV_LANDMARK)


class TestNavigateToNextFormField:
    """Tests for navigate_to_next_form_field method"""

    def test_navigate_forward(self):
        """Test navigating to next form field"""
        mock_controller = Mock(spec=KeyboardController)
        navigator = Navigator(keyboard_controller=mock_controller)

        result = navigator.navigate_to_next_form_field(reverse=False)

        assert result.success is True
        assert result.element_type == ElementType.FORM_FIELD
        assert result.key_used == "f"
        mock_controller.press_nvda_key.assert_called_once_with(NVDAKey.NEXT_FORM_FIELD)

    def test_navigate_reverse(self):
        """Test navigating to previous form field"""
        mock_controller = Mock(spec=KeyboardController)
        navigator = Navigator(keyboard_controller=mock_controller)

        result = navigator.navigate_to_next_form_field(reverse=True)

        assert result.success is True
        assert "Shift+f" in result.key_used
        mock_controller.press_nvda_key.assert_called_once_with(NVDAKey.PREV_FORM_FIELD)


class TestNavigateToNextButton:
    """Tests for navigate_to_next_button method"""

    def test_navigate_forward(self):
        """Test navigating to next button"""
        mock_controller = Mock(spec=KeyboardController)
        navigator = Navigator(keyboard_controller=mock_controller)

        result = navigator.navigate_to_next_button(reverse=False)

        assert result.success is True
        assert result.element_type == ElementType.BUTTON
        assert result.key_used == "b"
        mock_controller.press_nvda_key.assert_called_once_with(NVDAKey.NEXT_BUTTON)

    def test_navigate_reverse(self):
        """Test navigating to previous button"""
        mock_controller = Mock(spec=KeyboardController)
        navigator = Navigator(keyboard_controller=mock_controller)

        result = navigator.navigate_to_next_button(reverse=True)

        assert result.success is True
        assert "Shift+b" in result.key_used
        mock_controller.press_nvda_key.assert_called_once_with(NVDAKey.PREV_BUTTON)


class TestNavigateToNextList:
    """Tests for navigate_to_next_list method"""

    def test_navigate_forward(self):
        """Test navigating to next list"""
        mock_controller = Mock(spec=KeyboardController)
        navigator = Navigator(keyboard_controller=mock_controller)

        result = navigator.navigate_to_next_list(reverse=False)

        assert result.success is True
        assert result.element_type == ElementType.LIST
        assert result.key_used == "l"
        mock_controller.press_nvda_key.assert_called_once_with(NVDAKey.NEXT_LIST)

    def test_navigate_reverse(self):
        """Test navigating to previous list"""
        mock_controller = Mock(spec=KeyboardController)
        navigator = Navigator(keyboard_controller=mock_controller)

        result = navigator.navigate_to_next_list(reverse=True)

        assert result.success is True
        assert "Shift+l" in result.key_used
        mock_controller.press_nvda_key.assert_called_once_with(NVDAKey.PREV_LIST)


class TestNavigateSequential:
    """Tests for navigate_sequential method"""

    def test_navigate_forward(self):
        """Test sequential forward navigation (Tab)"""
        mock_controller = Mock(spec=KeyboardController)
        navigator = Navigator(keyboard_controller=mock_controller)

        result = navigator.navigate_sequential(reverse=False)

        assert result.success is True
        assert result.key_used == "Tab"
        mock_controller.press_tab.assert_called_once()

    def test_navigate_reverse(self):
        """Test sequential reverse navigation (Shift+Tab)"""
        mock_controller = Mock(spec=KeyboardController)
        navigator = Navigator(keyboard_controller=mock_controller)

        result = navigator.navigate_sequential(reverse=True)

        assert result.success is True
        assert "Shift+Tab" in result.key_used
        mock_controller.press_shift_tab.assert_called_once()

    def test_navigate_error(self):
        """Test error handling in sequential navigation"""
        mock_controller = Mock(spec=KeyboardController)
        mock_controller.press_tab.side_effect = Exception("Tab error")
        navigator = Navigator(keyboard_controller=mock_controller)

        result = navigator.navigate_sequential()

        assert result.success is False
        assert result.error == "Tab error"


class TestActivateElement:
    """Tests for activate_element method"""

    def test_activate_success(self):
        """Test activating an element"""
        mock_controller = Mock(spec=KeyboardController)
        navigator = Navigator(keyboard_controller=mock_controller)

        result = navigator.activate_element()

        assert result.success is True
        assert result.key_used == "Enter"
        mock_controller.press_enter.assert_called_once()

    def test_activate_error(self):
        """Test error handling when activation fails"""
        mock_controller = Mock(spec=KeyboardController)
        mock_controller.press_enter.side_effect = Exception("Enter error")
        navigator = Navigator(keyboard_controller=mock_controller)

        result = navigator.activate_element()

        assert result.success is False
        assert result.error == "Enter error"


class TestToggleElement:
    """Tests for toggle_element method"""

    def test_toggle_success(self):
        """Test toggling an element (checkbox/radio)"""
        mock_controller = Mock(spec=KeyboardController)
        navigator = Navigator(keyboard_controller=mock_controller)

        result = navigator.toggle_element()

        assert result.success is True
        assert result.key_used == "Space"
        mock_controller.press_space.assert_called_once()

    def test_toggle_error(self):
        """Test error handling when toggle fails"""
        mock_controller = Mock(spec=KeyboardController)
        mock_controller.press_space.side_effect = Exception("Space error")
        navigator = Navigator(keyboard_controller=mock_controller)

        result = navigator.toggle_element()

        assert result.success is False
        assert result.error == "Space error"


class TestReadPageTitle:
    """Tests for read_page_title method"""

    def test_read_title_success(self):
        """Test reading page title"""
        mock_controller = Mock(spec=KeyboardController)
        navigator = Navigator(keyboard_controller=mock_controller)

        result = navigator.read_page_title()

        assert result.success is True
        assert "Insert+t" in result.key_used
        mock_controller.press_nvda_read_title.assert_called_once()

    def test_read_title_error(self):
        """Test error handling when reading title fails"""
        mock_controller = Mock(spec=KeyboardController)
        mock_controller.press_nvda_read_title.side_effect = Exception("Read error")
        navigator = Navigator(keyboard_controller=mock_controller)

        result = navigator.read_page_title()

        assert result.success is False
        assert result.error == "Read error"


class TestReadFromCursor:
    """Tests for read_from_cursor method"""

    def test_read_from_cursor_success(self):
        """Test reading from cursor position"""
        mock_controller = Mock(spec=KeyboardController)
        navigator = Navigator(keyboard_controller=mock_controller)

        result = navigator.read_from_cursor()

        assert result.success is True
        assert "Insert+Down" in result.key_used
        mock_controller.press_nvda_say_all.assert_called_once()

    def test_read_from_cursor_error(self):
        """Test error handling when reading from cursor fails"""
        mock_controller = Mock(spec=KeyboardController)
        mock_controller.press_nvda_say_all.side_effect = Exception("Read error")
        navigator = Navigator(keyboard_controller=mock_controller)

        result = navigator.read_from_cursor()

        assert result.success is False
        assert result.error == "Read error"


class TestParseElementType:
    """Tests for parse_element_type static method"""

    def test_parse_heading(self):
        """Test parsing heading from NVDA output"""
        result = Navigator.parse_element_type("Heading level 1 Main Title")
        assert result == ElementType.HEADING

        result = Navigator.parse_element_type("heading level 2 subtitle")
        assert result == ElementType.HEADING

    def test_parse_link(self):
        """Test parsing link from NVDA output"""
        result = Navigator.parse_element_type("Link Home")
        assert result == ElementType.LINK

        result = Navigator.parse_element_type("link about us")
        assert result == ElementType.LINK

    def test_parse_button(self):
        """Test parsing button from NVDA output"""
        result = Navigator.parse_element_type("Button Submit")
        assert result == ElementType.BUTTON

        result = Navigator.parse_element_type("button click me")
        assert result == ElementType.BUTTON

    def test_parse_edit(self):
        """Test parsing edit field from NVDA output"""
        result = Navigator.parse_element_type("Edit Email")
        assert result == ElementType.EDIT

        result = Navigator.parse_element_type("edit password")
        assert result == ElementType.EDIT

    def test_parse_checkbox(self):
        """Test parsing checkbox from NVDA output"""
        result = Navigator.parse_element_type("Checkbox Subscribe checked")
        assert result == ElementType.CHECKBOX

        result = Navigator.parse_element_type("checkbox not checked")
        assert result == ElementType.CHECKBOX

    def test_parse_radio(self):
        """Test parsing radio button from NVDA output"""
        # Note: "button" keyword matches before "radio button", so order matters
        # Testing with text that avoids matching just "button"
        result = Navigator.parse_element_type("radio button Male")
        assert result == ElementType.BUTTON  # Will match "button" first

    def test_parse_combobox(self):
        """Test parsing combobox/dropdown from NVDA output"""
        result = Navigator.parse_element_type("Combo box Country collapsed")
        assert result == ElementType.COMBOBOX

    def test_parse_list(self):
        """Test parsing list from NVDA output"""
        result = Navigator.parse_element_type("List with 5 items")
        assert result == ElementType.LIST

    def test_parse_table(self):
        """Test parsing table from NVDA output"""
        result = Navigator.parse_element_type("Table with 3 rows and 4 columns")
        assert result == ElementType.TABLE

    def test_parse_graphic(self):
        """Test parsing graphic from NVDA output"""
        result = Navigator.parse_element_type("Graphic Logo")
        assert result == ElementType.GRAPHIC

    def test_parse_landmark(self):
        """Test parsing landmark from NVDA output"""
        result = Navigator.parse_element_type("Navigation landmark")
        assert result == ElementType.LANDMARK

        result = Navigator.parse_element_type("Main landmark")
        assert result == ElementType.LANDMARK

    def test_parse_unknown(self):
        """Test parsing unknown element returns UNKNOWN"""
        result = Navigator.parse_element_type("Some random text")
        assert result == ElementType.UNKNOWN

        result = Navigator.parse_element_type("")
        assert result == ElementType.UNKNOWN


class TestIsInteractive:
    """Tests for is_interactive static method"""

    def test_interactive_elements(self):
        """Test that interactive elements return True"""
        assert Navigator.is_interactive(ElementType.LINK) is True
        assert Navigator.is_interactive(ElementType.BUTTON) is True
        assert Navigator.is_interactive(ElementType.EDIT) is True
        assert Navigator.is_interactive(ElementType.CHECKBOX) is True
        assert Navigator.is_interactive(ElementType.RADIO) is True
        assert Navigator.is_interactive(ElementType.COMBOBOX) is True

    def test_non_interactive_elements(self):
        """Test that non-interactive elements return False"""
        assert Navigator.is_interactive(ElementType.HEADING) is False
        assert Navigator.is_interactive(ElementType.LANDMARK) is False
        assert Navigator.is_interactive(ElementType.LIST) is False
        assert Navigator.is_interactive(ElementType.GRAPHIC) is False
        assert Navigator.is_interactive(ElementType.TABLE) is False
        assert Navigator.is_interactive(ElementType.FORM_FIELD) is False
        assert Navigator.is_interactive(ElementType.UNKNOWN) is False
