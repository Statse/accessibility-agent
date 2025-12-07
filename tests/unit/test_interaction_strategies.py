"""Tests for interaction strategies module."""

import pytest
from unittest.mock import Mock, MagicMock

from src.navigation.interaction_strategies import (
    InteractionResult,
    InteractionStrategy,
    FormFillingStrategy,
    LinkActivationStrategy,
    PageExplorationStrategy,
)
from src.navigation.navigator import ElementType, Navigator
from src.automation.keyboard_controller import KeyboardController


class TestInteractionResult:
    """Tests for InteractionResult model"""

    def test_create_successful_result(self):
        """Test creating a successful interaction result"""
        result = InteractionResult(
            success=True,
            action_taken="Activated link",
            element_type=ElementType.LINK,
            nvda_feedback="Link Home"
        )

        assert result.success is True
        assert result.action_taken == "Activated link"
        assert result.element_type == ElementType.LINK
        assert result.nvda_feedback == "Link Home"
        assert result.accessibility_issue is None

    def test_create_failed_result_with_issue(self):
        """Test creating a failed result with accessibility issue"""
        result = InteractionResult(
            success=False,
            action_taken="Focused form field",
            element_type=ElementType.EDIT,
            nvda_feedback="edit",
            accessibility_issue="Missing label"
        )

        assert result.success is False
        assert result.accessibility_issue == "Missing label"

    def test_default_element_type(self):
        """Test default element type is UNKNOWN"""
        result = InteractionResult(
            success=True,
            action_taken="Test"
        )

        assert result.element_type == ElementType.UNKNOWN


class TestFormFillingStrategy:
    """Tests for FormFillingStrategy"""

    def test_initialization(self):
        """Test strategy initialization"""
        strategy = FormFillingStrategy()

        assert strategy.navigator is not None
        assert strategy.keyboard_controller is not None

    def test_initialization_with_dependencies(self):
        """Test initialization with custom dependencies"""
        mock_nav = Mock(spec=Navigator)
        mock_kb = Mock(spec=KeyboardController)

        strategy = FormFillingStrategy(
            navigator=mock_nav,
            keyboard_controller=mock_kb
        )

        assert strategy.navigator is mock_nav
        assert strategy.keyboard_controller is mock_kb

    def test_empty_nvda_output_detects_missing_label(self):
        """Test that empty NVDA output is flagged as missing label"""
        strategy = FormFillingStrategy()

        result = strategy.interact("", ElementType.EDIT)

        assert result.success is False
        assert "no label" in result.accessibility_issue.lower()
        assert "3.3.2" in result.accessibility_issue

    def test_whitespace_only_nvda_output_detects_missing_label(self):
        """Test that whitespace-only output is flagged as missing label"""
        strategy = FormFillingStrategy()

        result = strategy.interact("   ", ElementType.EDIT)

        assert result.success is False
        assert "no label" in result.accessibility_issue.lower()

    def test_generic_label_detected(self):
        """Test that generic labels are detected"""
        strategy = FormFillingStrategy()

        # Test various generic labels
        generic_labels = ["edit", "text field", "input", "field"]

        for label in generic_labels:
            result = strategy.interact(label, ElementType.EDIT)
            assert result.success is False
            assert "generic label" in result.accessibility_issue.lower()

    def test_proper_label_accepted(self):
        """Test that proper labels are accepted"""
        mock_kb = Mock(spec=KeyboardController)
        strategy = FormFillingStrategy(keyboard_controller=mock_kb)

        result = strategy.interact("Email address edit", ElementType.EDIT)

        assert result.success is True
        mock_kb.type_text.assert_called_once_with("test")

    def test_edit_field_typing_success(self):
        """Test successful typing in edit field"""
        mock_kb = Mock(spec=KeyboardController)
        strategy = FormFillingStrategy(keyboard_controller=mock_kb)

        result = strategy.interact("Username edit", ElementType.EDIT)

        assert result.success is True
        assert "typed test text" in result.action_taken.lower()
        mock_kb.type_text.assert_called_once()

    def test_edit_field_typing_error(self):
        """Test error handling when typing fails"""
        mock_kb = Mock(spec=KeyboardController)
        mock_kb.type_text.side_effect = Exception("Keyboard error")
        strategy = FormFillingStrategy(keyboard_controller=mock_kb)

        result = strategy.interact("Email edit", ElementType.EDIT)

        assert result.success is False
        assert "could not type" in result.accessibility_issue.lower()

    def test_checkbox_toggle_success(self):
        """Test successful checkbox toggle"""
        mock_kb = Mock(spec=KeyboardController)
        strategy = FormFillingStrategy(keyboard_controller=mock_kb)

        result = strategy.interact("Subscribe checkbox not checked", ElementType.CHECKBOX)

        assert result.success is True
        assert "toggled" in result.action_taken.lower()
        mock_kb.press_space.assert_called_once()

    def test_radio_toggle_success(self):
        """Test successful radio button toggle"""
        mock_kb = Mock(spec=KeyboardController)
        strategy = FormFillingStrategy(keyboard_controller=mock_kb)

        result = strategy.interact("Male radio button", ElementType.RADIO)

        assert result.success is True
        assert "toggled" in result.action_taken.lower()
        mock_kb.press_space.assert_called_once()

    def test_checkbox_toggle_error(self):
        """Test error handling when toggle fails"""
        mock_kb = Mock(spec=KeyboardController)
        mock_kb.press_space.side_effect = Exception("Space key error")
        strategy = FormFillingStrategy(keyboard_controller=mock_kb)

        result = strategy.interact("Subscribe checkbox", ElementType.CHECKBOX)

        assert result.success is False
        assert "could not toggle" in result.accessibility_issue.lower()

    def test_combobox_open_success(self):
        """Test successful combobox opening"""
        mock_kb = Mock(spec=KeyboardController)
        strategy = FormFillingStrategy(keyboard_controller=mock_kb)

        result = strategy.interact("Country combo box collapsed", ElementType.COMBOBOX)

        assert result.success is True
        assert "opened" in result.action_taken.lower()
        mock_kb.press_key.assert_called_once_with("Down", ["Alt"])

    def test_combobox_open_error(self):
        """Test error handling when combobox open fails"""
        mock_kb = Mock(spec=KeyboardController)
        mock_kb.press_key.side_effect = Exception("Key error")
        strategy = FormFillingStrategy(keyboard_controller=mock_kb)

        result = strategy.interact("Country combo box", ElementType.COMBOBOX)

        assert result.success is False
        assert "could not open" in result.accessibility_issue.lower()

    def test_form_field_with_proper_label(self):
        """Test form field with proper descriptive label"""
        strategy = FormFillingStrategy()

        result = strategy.interact("First name edit required", ElementType.FORM_FIELD)

        assert result.success is True
        assert "proper label" in result.action_taken.lower()


class TestLinkActivationStrategy:
    """Tests for LinkActivationStrategy"""

    def test_initialization(self):
        """Test strategy initialization"""
        strategy = LinkActivationStrategy()

        assert strategy.navigator is not None
        assert strategy.keyboard_controller is not None

    def test_generic_link_text_click_here(self):
        """Test detection of generic 'click here' link text"""
        strategy = LinkActivationStrategy()

        result = strategy.interact("link click here", ElementType.LINK)

        assert result.success is False
        assert "unclear text" in result.accessibility_issue.lower()
        assert "2.4.4" in result.accessibility_issue

    def test_generic_link_text_read_more(self):
        """Test detection of 'read more' link text"""
        strategy = LinkActivationStrategy()

        result = strategy.interact("link read more", ElementType.LINK)

        assert result.success is False
        assert "unclear text" in result.accessibility_issue.lower()

    def test_generic_link_text_here(self):
        """Test detection of 'here' link text"""
        strategy = LinkActivationStrategy()

        result = strategy.interact("link here", ElementType.LINK)

        assert result.success is False
        assert "unclear text" in result.accessibility_issue.lower()

    def test_empty_link_text(self):
        """Test detection of empty link text"""
        strategy = LinkActivationStrategy()

        result = strategy.interact("", ElementType.LINK)

        assert result.success is False
        assert "no text" in result.accessibility_issue.lower()

    def test_descriptive_link_text_validation(self):
        """Test validation of link with descriptive text"""
        strategy = LinkActivationStrategy()

        result = strategy.interact("link Contact Us", ElementType.LINK)

        assert result.success is True
        assert "verified link" in result.action_taken.lower()

    def test_link_missing_role(self):
        """Test detection of element without proper link role"""
        strategy = LinkActivationStrategy()

        result = strategy.interact("Contact Us", ElementType.LINK)

        assert result.success is False
        assert "not be properly marked" in result.accessibility_issue.lower()

    def test_activate_link_success(self):
        """Test successful link activation with Enter key"""
        mock_kb = Mock(spec=KeyboardController)
        strategy = LinkActivationStrategy(keyboard_controller=mock_kb)

        result = strategy.activate_link("link About Us")

        assert result.success is True
        assert "activated link" in result.action_taken.lower()
        mock_kb.press_enter.assert_called_once()

    def test_activate_link_error(self):
        """Test error handling when link activation fails"""
        mock_kb = Mock(spec=KeyboardController)
        mock_kb.press_enter.side_effect = Exception("Enter key error")
        strategy = LinkActivationStrategy(keyboard_controller=mock_kb)

        result = strategy.activate_link("link About")

        assert result.success is False
        assert "could not activate" in result.accessibility_issue.lower()


class TestPageExplorationStrategy:
    """Tests for PageExplorationStrategy"""

    def test_initialization(self):
        """Test strategy initialization"""
        strategy = PageExplorationStrategy()

        assert strategy.navigator is not None
        assert strategy.keyboard_controller is not None
        assert strategy.elements_visited == []
        assert strategy.issues_found == []

    def test_interact_with_proper_heading(self):
        """Test interaction with properly formatted heading"""
        strategy = PageExplorationStrategy()

        result = strategy.interact("Heading level 1 Main Title", ElementType.HEADING)

        assert result.success is True
        assert "navigated to heading" in result.action_taken.lower()
        assert len(strategy.elements_visited) == 1

    def test_interact_with_heading_missing_level(self):
        """Test detection of heading without level information"""
        strategy = PageExplorationStrategy()

        result = strategy.interact("Main Title", ElementType.HEADING)

        assert result.success is False
        assert "missing level" in result.accessibility_issue.lower()
        assert len(strategy.issues_found) == 1

    def test_interact_with_unlabeled_graphic(self):
        """Test detection of unlabeled graphic"""
        strategy = PageExplorationStrategy()

        result = strategy.interact("unlabeled graphic", ElementType.GRAPHIC)

        assert result.success is False
        assert "no alt text" in result.accessibility_issue.lower()
        assert "1.1.1" in result.accessibility_issue

    def test_interact_with_generic_graphic(self):
        """Test detection of generic graphic label"""
        strategy = PageExplorationStrategy()

        result = strategy.interact("graphic", ElementType.GRAPHIC)

        assert result.success is False
        assert "no alt text" in result.accessibility_issue.lower()

    def test_interact_with_generic_element(self):
        """Test interaction with other element types"""
        strategy = PageExplorationStrategy()

        result = strategy.interact("Button Submit", ElementType.BUTTON)

        assert result.success is True
        assert "navigated to button" in result.action_taken.lower()
        assert len(strategy.elements_visited) == 1

    def test_explore_headings_success(self):
        """Test exploring multiple headings"""
        mock_nav = Mock(spec=Navigator)
        # Return success for 3 headings, then fail
        mock_nav.navigate_to_next_heading.side_effect = [
            Mock(success=True),
            Mock(success=True),
            Mock(success=True),
            Mock(success=False),
        ]
        strategy = PageExplorationStrategy(navigator=mock_nav)

        results = strategy.explore_headings(max_headings=5)

        assert len(results) == 3
        assert all(r.element_type == ElementType.HEADING for r in results)
        assert mock_nav.navigate_to_next_heading.call_count == 4

    def test_explore_links_success(self):
        """Test exploring multiple links"""
        mock_nav = Mock(spec=Navigator)
        # Return success for 2 links, then fail
        mock_nav.navigate_to_next_link.side_effect = [
            Mock(success=True),
            Mock(success=True),
            Mock(success=False),
        ]
        strategy = PageExplorationStrategy(navigator=mock_nav)

        results = strategy.explore_links(max_links=5)

        assert len(results) == 2
        assert all(r.element_type == ElementType.LINK for r in results)
        assert mock_nav.navigate_to_next_link.call_count == 3

    def test_explore_forms_success(self):
        """Test exploring multiple form fields"""
        mock_nav = Mock(spec=Navigator)
        # Return success for 4 fields, then fail
        mock_nav.navigate_to_next_form_field.side_effect = [
            Mock(success=True),
            Mock(success=True),
            Mock(success=True),
            Mock(success=True),
            Mock(success=False),
        ]
        strategy = PageExplorationStrategy(navigator=mock_nav)

        results = strategy.explore_forms(max_fields=10)

        assert len(results) == 4
        assert all(r.element_type == ElementType.FORM_FIELD for r in results)
        assert mock_nav.navigate_to_next_form_field.call_count == 5

    def test_get_exploration_summary(self):
        """Test getting exploration summary"""
        strategy = PageExplorationStrategy()

        # Simulate some exploration
        strategy.interact("Heading level 1 Main", ElementType.HEADING)
        strategy.interact("unlabeled graphic", ElementType.GRAPHIC)
        strategy.interact("Button Submit", ElementType.BUTTON)

        summary = strategy.get_exploration_summary()

        assert summary["elements_visited"] == 3
        assert summary["issues_found"] == 1

    def test_reset_exploration_state(self):
        """Test resetting exploration state"""
        strategy = PageExplorationStrategy()

        # Add some state
        strategy.interact("Heading level 1 Main", ElementType.HEADING)
        strategy.interact("unlabeled graphic", ElementType.GRAPHIC)

        assert len(strategy.elements_visited) > 0
        assert len(strategy.issues_found) > 0

        # Reset
        strategy.reset()

        assert len(strategy.elements_visited) == 0
        assert len(strategy.issues_found) == 0


class TestStrategyIntegration:
    """Integration tests for strategies"""

    def test_form_strategy_complete_workflow(self):
        """Test complete form interaction workflow"""
        mock_kb = Mock(spec=KeyboardController)
        strategy = FormFillingStrategy(keyboard_controller=mock_kb)

        # Test multiple field types
        fields = [
            ("Email address edit", ElementType.EDIT),
            ("Subscribe checkbox", ElementType.CHECKBOX),
            ("Country combo box", ElementType.COMBOBOX),
        ]

        for nvda_output, elem_type in fields:
            result = strategy.interact(nvda_output, elem_type)
            assert result.success is True

    def test_link_strategy_complete_workflow(self):
        """Test complete link interaction workflow"""
        strategy = LinkActivationStrategy()

        # Good link (validates text)
        result1 = strategy.interact("link About Us", ElementType.LINK)
        assert result1.success is True

        # Bad link (generic text)
        result2 = strategy.interact("link click here", ElementType.LINK)
        assert result2.success is False

    def test_exploration_strategy_multiple_element_types(self):
        """Test exploration across different element types"""
        strategy = PageExplorationStrategy()

        elements = [
            ("Heading level 1 Home", ElementType.HEADING),
            ("Link Contact", ElementType.LINK),
            ("Button Submit", ElementType.BUTTON),
        ]

        for nvda_output, elem_type in elements:
            result = strategy.interact(nvda_output, elem_type)
            assert result.success is True

        summary = strategy.get_exploration_summary()
        assert summary["elements_visited"] == 3

    def test_full_page_exploration_workflow(self):
        """Test complete page exploration workflow"""
        mock_nav = Mock(spec=Navigator)

        # Simulate finding 2 headings, 1 link, 1 form
        mock_nav.navigate_to_next_heading.side_effect = [
            Mock(success=True),
            Mock(success=True),
            Mock(success=False),
        ]
        mock_nav.navigate_to_next_link.side_effect = [
            Mock(success=True),
            Mock(success=False),
        ]
        mock_nav.navigate_to_next_form_field.side_effect = [
            Mock(success=True),
            Mock(success=False),
        ]

        strategy = PageExplorationStrategy(navigator=mock_nav)

        # Explore different element types
        heading_results = strategy.explore_headings()
        link_results = strategy.explore_links()
        form_results = strategy.explore_forms()

        assert len(heading_results) == 2
        assert len(link_results) == 1
        assert len(form_results) == 1
