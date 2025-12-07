"""Interaction strategies for testing web elements."""

import logging
from abc import ABC, abstractmethod
from typing import Optional

from pydantic import BaseModel, ConfigDict

from ..automation.keyboard_controller import KeyboardController
from .navigator import ElementType, Navigator, NavigationResult

logger = logging.getLogger(__name__)


class InteractionResult(BaseModel):
    """Result of an interaction with an element.

    Attributes:
        success: Whether the interaction was successful
        action_taken: Description of what action was taken
        element_type: Type of element interacted with
        nvda_feedback: NVDA output after interaction (if available)
        accessibility_issue: Detected accessibility issue (if any)
    """

    model_config = ConfigDict(ser_json_timedelta="iso8601")

    success: bool
    action_taken: str
    element_type: ElementType = ElementType.UNKNOWN
    nvda_feedback: Optional[str] = None
    accessibility_issue: Optional[str] = None


class InteractionStrategy(ABC):
    """Base class for interaction strategies.

    Strategies define how the agent should interact with different
    types of elements to test their accessibility.
    """

    def __init__(
        self,
        navigator: Optional[Navigator] = None,
        keyboard_controller: Optional[KeyboardController] = None,
    ):
        """Initialize the interaction strategy.

        Args:
            navigator: Navigator for page navigation
            keyboard_controller: Keyboard controller for input
        """
        self.navigator = navigator or Navigator()
        self.keyboard_controller = keyboard_controller or KeyboardController()
        logger.info(f"{self.__class__.__name__} initialized")

    @abstractmethod
    def interact(self, nvda_output: str, element_type: ElementType) -> InteractionResult:
        """Interact with an element based on its type.

        Args:
            nvda_output: What NVDA announced for this element
            element_type: Type of element

        Returns:
            InteractionResult describing what happened
        """
        pass


class FormFillingStrategy(InteractionStrategy):
    """Strategy for testing form field accessibility.

    This strategy focuses on:
    - Checking for proper labels
    - Testing form field focus behavior
    - Detecting missing instructions
    - Testing error messages
    """

    def interact(self, nvda_output: str, element_type: ElementType) -> InteractionResult:
        """Interact with a form field to test accessibility.

        Args:
            nvda_output: NVDA output for the form field
            element_type: Type of form element

        Returns:
            InteractionResult with test outcome
        """
        logger.debug(f"Testing form field: '{nvda_output[:50]}...'")

        # Check if form field has a label
        nvda_lower = nvda_output.lower()

        if not nvda_output or nvda_output.strip() == "":
            return InteractionResult(
                success=False,
                action_taken="Focused form field",
                element_type=element_type,
                nvda_feedback=nvda_output,
                accessibility_issue="Form field has no label (NVDA silent) - WCAG 3.3.2 violation",
            )

        # Check for generic/unclear labels
        generic_labels = ["edit", "text field", "input", "field"]
        if any(label == nvda_lower.strip() for label in generic_labels):
            return InteractionResult(
                success=False,
                action_taken="Focused form field",
                element_type=element_type,
                nvda_feedback=nvda_output,
                accessibility_issue=f"Form field has generic label '{nvda_output}' - missing proper label",
            )

        # For edit fields, try typing to see if it works
        if element_type == ElementType.EDIT:
            try:
                # Type a test value
                test_text = "test"
                self.keyboard_controller.type_text(test_text)
                logger.debug(f"Typed test text: '{test_text}'")

                return InteractionResult(
                    success=True,
                    action_taken=f"Focused and typed test text in form field",
                    element_type=element_type,
                    nvda_feedback=nvda_output,
                )
            except Exception as e:
                return InteractionResult(
                    success=False,
                    action_taken="Attempted to type in form field",
                    element_type=element_type,
                    nvda_feedback=nvda_output,
                    accessibility_issue=f"Could not type in form field: {e}",
                )

        # For checkboxes/radios, toggle them
        elif element_type in [ElementType.CHECKBOX, ElementType.RADIO]:
            try:
                self.keyboard_controller.press_space()
                logger.debug("Toggled checkbox/radio button")

                return InteractionResult(
                    success=True,
                    action_taken="Toggled checkbox/radio button",
                    element_type=element_type,
                    nvda_feedback=nvda_output,
                )
            except Exception as e:
                return InteractionResult(
                    success=False,
                    action_taken="Attempted to toggle checkbox/radio",
                    element_type=element_type,
                    nvda_feedback=nvda_output,
                    accessibility_issue=f"Could not toggle element: {e}",
                )

        # For comboboxes, try opening with Alt+Down
        elif element_type == ElementType.COMBOBOX:
            try:
                self.keyboard_controller.press_key("Down", ["Alt"])
                logger.debug("Opened combobox")

                return InteractionResult(
                    success=True,
                    action_taken="Opened dropdown/combobox",
                    element_type=element_type,
                    nvda_feedback=nvda_output,
                )
            except Exception as e:
                return InteractionResult(
                    success=False,
                    action_taken="Attempted to open combobox",
                    element_type=element_type,
                    nvda_feedback=nvda_output,
                    accessibility_issue=f"Could not open combobox: {e}",
                )

        # Field has proper label
        return InteractionResult(
            success=True,
            action_taken="Verified form field has proper label",
            element_type=element_type,
            nvda_feedback=nvda_output,
        )


class LinkActivationStrategy(InteractionStrategy):
    """Strategy for testing link accessibility.

    This strategy focuses on:
    - Checking for clear link text
    - Avoiding generic "click here" links
    - Testing link activation
    - Verifying link destinations are announced
    """

    def interact(self, nvda_output: str, element_type: ElementType) -> InteractionResult:
        """Interact with a link to test accessibility.

        Args:
            nvda_output: NVDA output for the link
            element_type: Type of element (should be LINK)

        Returns:
            InteractionResult with test outcome
        """
        logger.debug(f"Testing link: '{nvda_output[:50]}...'")

        nvda_lower = nvda_output.lower()

        # Check if link has no text
        if not nvda_output or nvda_output.strip() == "":
            return InteractionResult(
                success=False,
                action_taken="Focused link",
                element_type=element_type,
                nvda_feedback=nvda_output,
                accessibility_issue="Link has no text (NVDA silent) - WCAG 2.4.4 violation",
            )

        # Check for poor link text
        poor_link_texts = [
            "click here",
            "read more",
            "more",
            "link",
            "here",
            "this",
            "more info",
            "click",
        ]

        link_text = nvda_lower.replace("link", "").strip()

        if link_text in poor_link_texts:
            return InteractionResult(
                success=False,
                action_taken="Focused link",
                element_type=element_type,
                nvda_feedback=nvda_output,
                accessibility_issue=f"Link has unclear text '{link_text}' - WCAG 2.4.4 violation",
            )

        # Check if "link" is announced (good accessibility)
        if "link" not in nvda_lower:
            return InteractionResult(
                success=False,
                action_taken="Focused link",
                element_type=element_type,
                nvda_feedback=nvda_output,
                accessibility_issue="Element may not be properly marked as link (role missing)",
            )

        # Link has good text and proper role
        return InteractionResult(
            success=True,
            action_taken="Verified link has clear text and proper role",
            element_type=element_type,
            nvda_feedback=nvda_output,
        )

    def activate_link(self, nvda_output: str) -> InteractionResult:
        """Activate a link (press Enter).

        This is used when the agent wants to follow a link.

        Args:
            nvda_output: NVDA output for the link

        Returns:
            InteractionResult with activation outcome
        """
        try:
            self.keyboard_controller.press_enter()
            logger.info(f"Activated link: '{nvda_output[:50]}...'")

            return InteractionResult(
                success=True,
                action_taken="Activated link with Enter",
                element_type=ElementType.LINK,
                nvda_feedback=nvda_output,
            )
        except Exception as e:
            return InteractionResult(
                success=False,
                action_taken="Attempted to activate link",
                element_type=ElementType.LINK,
                nvda_feedback=nvda_output,
                accessibility_issue=f"Could not activate link: {e}",
            )


class PageExplorationStrategy(InteractionStrategy):
    """Strategy for overall page exploration.

    This strategy coordinates different navigation methods to
    systematically explore a page and identify accessibility issues.
    """

    def __init__(
        self,
        navigator: Optional[Navigator] = None,
        keyboard_controller: Optional[KeyboardController] = None,
    ):
        """Initialize the page exploration strategy.

        Args:
            navigator: Navigator for page navigation
            keyboard_controller: Keyboard controller for input
        """
        super().__init__(navigator, keyboard_controller)
        self.elements_visited: list[str] = []
        self.issues_found: list[str] = []

    def interact(self, nvda_output: str, element_type: ElementType) -> InteractionResult:
        """Default interaction for page exploration.

        This method is called for elements that don't have specific
        interaction strategies.

        Args:
            nvda_output: NVDA output for the element
            element_type: Type of element

        Returns:
            InteractionResult with exploration outcome
        """
        # Record the visit
        self.elements_visited.append(nvda_output)

        # Check for common issues
        nvda_lower = nvda_output.lower()

        # Check for unlabeled graphics
        if element_type == ElementType.GRAPHIC:
            if "unlabeled" in nvda_lower or nvda_output.strip() == "graphic":
                issue = "Graphic has no alt text - WCAG 1.1.1 violation"
                self.issues_found.append(issue)

                return InteractionResult(
                    success=False,
                    action_taken="Encountered graphic",
                    element_type=element_type,
                    nvda_feedback=nvda_output,
                    accessibility_issue=issue,
                )

        # Check for missing headings structure
        if element_type == ElementType.HEADING:
            # Extract heading level if present
            if "heading level" in nvda_lower:
                return InteractionResult(
                    success=True,
                    action_taken="Navigated to heading",
                    element_type=element_type,
                    nvda_feedback=nvda_output,
                )
            else:
                issue = "Heading missing level information"
                self.issues_found.append(issue)

                return InteractionResult(
                    success=False,
                    action_taken="Encountered heading",
                    element_type=element_type,
                    nvda_feedback=nvda_output,
                    accessibility_issue=issue,
                )

        # Element seems fine
        return InteractionResult(
            success=True,
            action_taken=f"Navigated to {element_type.value}",
            element_type=element_type,
            nvda_feedback=nvda_output,
        )

    def explore_headings(self, max_headings: int = 20) -> list[InteractionResult]:
        """Explore page headings structure.

        Args:
            max_headings: Maximum number of headings to explore

        Returns:
            List of InteractionResult for each heading
        """
        results = []
        heading_levels = []

        for i in range(max_headings):
            nav_result = self.navigator.navigate_to_next_heading()

            if not nav_result.success:
                # No more headings
                break

            # In real usage, we'd get NVDA output here
            # For now, create a placeholder result
            interaction_result = InteractionResult(
                success=True,
                action_taken=f"Explored heading {i+1}",
                element_type=ElementType.HEADING,
            )

            results.append(interaction_result)

        logger.info(f"Explored {len(results)} headings")
        return results

    def explore_links(self, max_links: int = 50) -> list[InteractionResult]:
        """Explore page links.

        Args:
            max_links: Maximum number of links to explore

        Returns:
            List of InteractionResult for each link
        """
        results = []

        for i in range(max_links):
            nav_result = self.navigator.navigate_to_next_link()

            if not nav_result.success:
                # No more links
                break

            interaction_result = InteractionResult(
                success=True,
                action_taken=f"Explored link {i+1}",
                element_type=ElementType.LINK,
            )

            results.append(interaction_result)

        logger.info(f"Explored {len(results)} links")
        return results

    def explore_forms(self, max_fields: int = 20) -> list[InteractionResult]:
        """Explore form fields on the page.

        Args:
            max_fields: Maximum number of form fields to explore

        Returns:
            List of InteractionResult for each form field
        """
        results = []

        for i in range(max_fields):
            nav_result = self.navigator.navigate_to_next_form_field()

            if not nav_result.success:
                # No more form fields
                break

            interaction_result = InteractionResult(
                success=True,
                action_taken=f"Explored form field {i+1}",
                element_type=ElementType.FORM_FIELD,
            )

            results.append(interaction_result)

        logger.info(f"Explored {len(results)} form fields")
        return results

    def get_exploration_summary(self) -> dict:
        """Get summary of page exploration.

        Returns:
            Dictionary with exploration statistics
        """
        return {
            "elements_visited": len(self.elements_visited),
            "issues_found": len(self.issues_found),
            "issues": self.issues_found,
        }

    def reset(self) -> None:
        """Reset exploration state."""
        self.elements_visited.clear()
        self.issues_found.clear()
        logger.info("Page exploration state reset")
