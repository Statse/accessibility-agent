"""Decision engine for agent navigation and accessibility testing logic."""

import logging
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

logger = logging.getLogger(__name__)


class NavigationStrategy(str, Enum):
    """Navigation strategies for exploring web pages."""

    SEQUENTIAL_TAB = "sequential_tab"  # Tab through all elements
    HEADINGS_FIRST = "headings_first"  # Navigate headings (H key) first
    LANDMARKS = "landmarks"  # Navigate by ARIA landmarks (D key)
    LINKS = "links"  # Navigate by links (K key)
    FORMS = "forms"  # Navigate by form fields (F key)
    BUTTONS = "buttons"  # Navigate by buttons (B key)
    INTERACTIVE_ONLY = "interactive_only"  # Focus on interactive elements


class NavigationAction(str, Enum):
    """Possible navigation actions the agent can take."""

    TAB = "Tab"
    SHIFT_TAB = "Shift+Tab"
    ENTER = "Enter"
    SPACE = "Space"
    ESCAPE = "Escape"
    ARROW_DOWN = "ArrowDown"
    ARROW_UP = "ArrowUp"
    ARROW_LEFT = "ArrowLeft"
    ARROW_RIGHT = "ArrowRight"

    # NVDA navigation keys
    NEXT_HEADING = "h"
    PREV_HEADING = "H"  # Shift+h
    NEXT_LINK = "k"
    PREV_LINK = "K"  # Shift+k
    NEXT_LANDMARK = "d"
    PREV_LANDMARK = "D"  # Shift+d
    NEXT_FORM_FIELD = "f"
    PREV_FORM_FIELD = "F"  # Shift+f
    NEXT_BUTTON = "b"
    PREV_BUTTON = "B"  # Shift+b
    NEXT_LIST = "l"
    PREV_LIST = "L"  # Shift+l

    # NVDA special commands
    READ_TITLE = "Insert+t"
    SAY_ALL = "Insert+Down"


class AgentState(str, Enum):
    """Current state of the accessibility agent."""

    IDLE = "idle"  # Not started
    INITIALIZING = "initializing"  # Setting up browser, NVDA
    EXPLORING = "exploring"  # Actively navigating the page
    ANALYZING = "analyzing"  # Analyzing NVDA output for issues
    TESTING_INTERACTION = "testing_interaction"  # Testing interactive elements
    DETECTING_ISSUES = "detecting_issues"  # Focused issue detection mode
    STUCK = "stuck"  # Detected circular navigation or keyboard trap
    COMPLETED = "completed"  # Finished testing
    ERROR = "error"  # Encountered an error


class NavigationDecision(BaseModel):
    """Represents a decision made by the agent about what action to take.

    Attributes:
        action: The navigation action to perform
        reasoning: Why this action was chosen
        expected_outcome: What the agent expects to happen
        priority: Priority of this action (1-10, 10 = highest)
        strategy: The navigation strategy being used
    """

    model_config = ConfigDict(ser_json_timedelta="iso8601")

    action: NavigationAction
    reasoning: str
    expected_outcome: str
    priority: int = Field(default=5, ge=1, le=10)
    strategy: NavigationStrategy = NavigationStrategy.SEQUENTIAL_TAB


class DecisionEngine:
    """Makes decisions about which navigation actions to take.

    The decision engine analyzes the current state, NVDA output, and
    navigation history to decide what the agent should do next.

    Attributes:
        current_state: Current state of the agent
        current_strategy: Current navigation strategy
        actions_taken: Count of actions taken so far
        max_actions: Maximum actions before stopping (prevent infinite loops)
        stuck_threshold: Number of repeated actions before considering stuck
    """

    def __init__(
        self,
        initial_strategy: NavigationStrategy = NavigationStrategy.HEADINGS_FIRST,
        max_actions: int = 100,
        stuck_threshold: int = 5,
    ) -> None:
        """Initialize the decision engine.

        Args:
            initial_strategy: Strategy to start with
            max_actions: Maximum number of actions before stopping
            stuck_threshold: Number of repeated actions before considering stuck

        Raises:
            ValueError: If max_actions or stuck_threshold are invalid
        """
        if max_actions < 1:
            raise ValueError(f"max_actions must be >= 1, got {max_actions}")
        if stuck_threshold < 1:
            raise ValueError(f"stuck_threshold must be >= 1, got {stuck_threshold}")

        self.current_state = AgentState.IDLE
        self.current_strategy = initial_strategy
        self.actions_taken = 0
        self.max_actions = max_actions
        self.stuck_threshold = stuck_threshold

        logger.info(
            f"DecisionEngine initialized "
            f"(strategy={initial_strategy}, max_actions={max_actions})"
        )

    def set_state(self, new_state: AgentState) -> None:
        """Update the agent's current state.

        Args:
            new_state: The new state to transition to
        """
        old_state = self.current_state
        self.current_state = new_state
        logger.info(f"State transition: {old_state} → {new_state}")

    def set_strategy(self, new_strategy: NavigationStrategy) -> None:
        """Update the navigation strategy.

        Args:
            new_strategy: The new strategy to use
        """
        old_strategy = self.current_strategy
        self.current_strategy = new_strategy
        logger.info(f"Strategy changed: {old_strategy} → {new_strategy}")

    def increment_actions(self) -> None:
        """Increment the action counter."""
        self.actions_taken += 1
        logger.debug(f"Actions taken: {self.actions_taken}/{self.max_actions}")

    def has_reached_max_actions(self) -> bool:
        """Check if the agent has reached the maximum action limit.

        Returns:
            True if max actions reached, False otherwise
        """
        return self.actions_taken >= self.max_actions

    def decide_next_action(
        self,
        nvda_output: Optional[str] = None,
        is_circular: bool = False,
        has_visited_before: bool = False,
    ) -> NavigationDecision:
        """Decide what action to take next based on context.

        Args:
            nvda_output: Latest NVDA output text
            is_circular: Whether circular navigation was detected
            has_visited_before: Whether current element was visited before

        Returns:
            NavigationDecision with the chosen action and reasoning
        """
        # Check if stuck in circular navigation
        if is_circular and self.current_state != AgentState.STUCK:
            self.set_state(AgentState.STUCK)
            return NavigationDecision(
                action=NavigationAction.ESCAPE,
                reasoning="Detected circular navigation (keyboard trap). Attempting to escape.",
                expected_outcome="Exit the keyboard trap and resume navigation",
                priority=10,
                strategy=self.current_strategy,
            )

        # Check if max actions reached
        if self.has_reached_max_actions():
            self.set_state(AgentState.COMPLETED)
            return NavigationDecision(
                action=NavigationAction.ESCAPE,
                reasoning=f"Reached maximum action limit ({self.max_actions}). Stopping exploration.",
                expected_outcome="Complete the testing session",
                priority=10,
                strategy=self.current_strategy,
            )

        # Strategy-based navigation
        if self.current_strategy == NavigationStrategy.HEADINGS_FIRST:
            return self._decide_headings_first(nvda_output, has_visited_before)
        elif self.current_strategy == NavigationStrategy.SEQUENTIAL_TAB:
            return self._decide_sequential_tab(nvda_output, has_visited_before)
        elif self.current_strategy == NavigationStrategy.LANDMARKS:
            return self._decide_landmarks(nvda_output, has_visited_before)
        elif self.current_strategy == NavigationStrategy.LINKS:
            return self._decide_links(nvda_output, has_visited_before)
        elif self.current_strategy == NavigationStrategy.FORMS:
            return self._decide_forms(nvda_output, has_visited_before)
        elif self.current_strategy == NavigationStrategy.BUTTONS:
            return self._decide_buttons(nvda_output, has_visited_before)
        else:
            # Default to sequential tab
            return self._decide_sequential_tab(nvda_output, has_visited_before)

    def _decide_headings_first(
        self, nvda_output: Optional[str], has_visited: bool
    ) -> NavigationDecision:
        """Decide next action using headings-first strategy.

        This strategy navigates through all headings first to understand
        the page structure, then switches to sequential tab navigation.
        """
        if nvda_output and "heading" in nvda_output.lower():
            # Currently on a heading, move to next
            return NavigationDecision(
                action=NavigationAction.NEXT_HEADING,
                reasoning="Navigate to next heading to map page structure",
                expected_outcome="NVDA announces the next heading level and text",
                priority=8,
                strategy=NavigationStrategy.HEADINGS_FIRST,
            )
        else:
            # No more headings, switch to sequential tab
            self.set_strategy(NavigationStrategy.SEQUENTIAL_TAB)
            return NavigationDecision(
                action=NavigationAction.TAB,
                reasoning="Finished exploring headings, switching to sequential navigation",
                expected_outcome="NVDA announces the next focusable element",
                priority=7,
                strategy=NavigationStrategy.SEQUENTIAL_TAB,
            )

    def _decide_sequential_tab(
        self, nvda_output: Optional[str], has_visited: bool
    ) -> NavigationDecision:
        """Decide next action using sequential tab strategy."""
        if has_visited:
            # Already visited, but continue for completeness
            return NavigationDecision(
                action=NavigationAction.TAB,
                reasoning="Continue sequential navigation (element already visited)",
                expected_outcome="NVDA announces the next element",
                priority=5,
                strategy=NavigationStrategy.SEQUENTIAL_TAB,
            )
        else:
            return NavigationDecision(
                action=NavigationAction.TAB,
                reasoning="Navigate to next element sequentially",
                expected_outcome="NVDA announces the next focusable element",
                priority=6,
                strategy=NavigationStrategy.SEQUENTIAL_TAB,
            )

    def _decide_landmarks(
        self, nvda_output: Optional[str], has_visited: bool
    ) -> NavigationDecision:
        """Decide next action using landmarks strategy."""
        return NavigationDecision(
            action=NavigationAction.NEXT_LANDMARK,
            reasoning="Navigate by ARIA landmarks to understand page regions",
            expected_outcome="NVDA announces the next landmark (navigation, main, banner, etc.)",
            priority=7,
            strategy=NavigationStrategy.LANDMARKS,
        )

    def _decide_links(
        self, nvda_output: Optional[str], has_visited: bool
    ) -> NavigationDecision:
        """Decide next action using links strategy."""
        return NavigationDecision(
            action=NavigationAction.NEXT_LINK,
            reasoning="Navigate to next link to test link accessibility",
            expected_outcome="NVDA announces link text and destination",
            priority=7,
            strategy=NavigationStrategy.LINKS,
        )

    def _decide_forms(
        self, nvda_output: Optional[str], has_visited: bool
    ) -> NavigationDecision:
        """Decide next action using forms strategy."""
        return NavigationDecision(
            action=NavigationAction.NEXT_FORM_FIELD,
            reasoning="Navigate to next form field to test form accessibility",
            expected_outcome="NVDA announces form field label and type",
            priority=8,
            strategy=NavigationStrategy.FORMS,
        )

    def _decide_buttons(
        self, nvda_output: Optional[str], has_visited: bool
    ) -> NavigationDecision:
        """Decide next action using buttons strategy."""
        return NavigationDecision(
            action=NavigationAction.NEXT_BUTTON,
            reasoning="Navigate to next button to test button accessibility",
            expected_outcome="NVDA announces button label and role",
            priority=7,
            strategy=NavigationStrategy.BUTTONS,
        )

    def should_test_interaction(self, nvda_output: Optional[str]) -> bool:
        """Determine if the current element should be interacted with.

        Args:
            nvda_output: Latest NVDA output

        Returns:
            True if the element should be tested for interaction, False otherwise
        """
        if not nvda_output:
            return False

        nvda_lower = nvda_output.lower()

        # Test interactive elements
        interactive_indicators = [
            "button",
            "link",
            "edit",  # Input field
            "checkbox",
            "radio button",
            "combo box",  # Dropdown
            "menu",
        ]

        return any(indicator in nvda_lower for indicator in interactive_indicators)

    def reset(self) -> None:
        """Reset the decision engine to initial state."""
        self.current_state = AgentState.IDLE
        self.actions_taken = 0
        logger.info("DecisionEngine reset to initial state")
