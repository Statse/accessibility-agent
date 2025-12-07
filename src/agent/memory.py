"""Agent memory for tracking visited elements and actions."""

import logging
from collections import deque
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

logger = logging.getLogger(__name__)


class VisitedElement(BaseModel):
    """Represents an element that was visited by the agent.

    Attributes:
        timestamp: When the element was visited
        nvda_text: What NVDA announced for this element
        key_used: The key pressed to reach this element
        element_id: Unique identifier (hash of NVDA text + context)
        context: Optional context about why this element was visited
        is_interactive: Whether this element is interactive (button, link, form field)
    """

    model_config = ConfigDict(ser_json_timedelta="iso8601")

    timestamp: datetime = Field(default_factory=datetime.now)
    nvda_text: str
    key_used: str
    element_id: str
    context: Optional[str] = None
    is_interactive: bool = False


class AgentMemory:
    """Manages agent's memory of visited elements and actions taken.

    This memory helps the agent:
    - Avoid revisiting the same elements
    - Track navigation history
    - Identify patterns in page structure
    - Detect potential accessibility issues (e.g., circular navigation)

    Attributes:
        max_history: Maximum number of elements to remember
        _visited_elements: Deque of visited elements
        _element_ids_seen: Set of element IDs for quick lookup
    """

    def __init__(self, max_history: int = 1000) -> None:
        """Initialize agent memory.

        Args:
            max_history: Maximum number of elements to remember.
                Older elements are automatically removed when limit is reached.

        Raises:
            ValueError: If max_history is less than 1.
        """
        if max_history < 1:
            raise ValueError(f"max_history must be >= 1, got {max_history}")

        self.max_history = max_history
        self._visited_elements: deque[VisitedElement] = deque(maxlen=max_history)
        self._element_ids_seen: set[str] = set()

        logger.info(f"AgentMemory initialized with max_history={max_history}")

    def add_element(
        self,
        nvda_text: str,
        key_used: str,
        element_id: str,
        context: Optional[str] = None,
        is_interactive: bool = False,
    ) -> VisitedElement:
        """Add a visited element to memory.

        Args:
            nvda_text: What NVDA announced for this element
            key_used: The key pressed to reach this element
            element_id: Unique identifier for the element
            context: Optional context about why this element was visited
            is_interactive: Whether this element is interactive

        Returns:
            The created VisitedElement
        """
        element = VisitedElement(
            nvda_text=nvda_text,
            key_used=key_used,
            element_id=element_id,
            context=context,
            is_interactive=is_interactive,
        )

        self._visited_elements.append(element)
        self._element_ids_seen.add(element_id)

        logger.debug(f"Added element to memory: {element_id} ('{nvda_text[:50]}...')")

        return element

    def has_visited(self, element_id: str) -> bool:
        """Check if an element has been visited before.

        Args:
            element_id: Unique identifier for the element

        Returns:
            True if the element has been visited, False otherwise
        """
        return element_id in self._element_ids_seen

    def get_recent_elements(self, count: int = 10) -> list[VisitedElement]:
        """Get the most recently visited elements.

        Args:
            count: Number of recent elements to return

        Returns:
            List of VisitedElement in reverse chronological order (newest first)
        """
        elements = list(self._visited_elements)
        return elements[-count:][::-1]  # Reverse to get newest first

    def get_all_elements(self) -> list[VisitedElement]:
        """Get all visited elements in chronological order.

        Returns:
            List of all VisitedElement
        """
        return list(self._visited_elements)

    def get_interactive_elements(self) -> list[VisitedElement]:
        """Get all visited interactive elements (buttons, links, forms).

        Returns:
            List of interactive VisitedElement
        """
        return [elem for elem in self._visited_elements if elem.is_interactive]

    def count_visits(self) -> int:
        """Get the total number of elements visited.

        Returns:
            Total count of visited elements
        """
        return len(self._visited_elements)

    def clear(self) -> None:
        """Clear all memory of visited elements."""
        count = len(self._visited_elements)
        self._visited_elements.clear()
        self._element_ids_seen.clear()
        logger.info(f"Cleared agent memory ({count} elements removed)")

    def detect_circular_navigation(self, window_size: int = 5) -> bool:
        """Detect if the agent is stuck in circular navigation.

        This checks if the same element IDs are appearing repeatedly
        in the recent navigation history, which might indicate a keyboard trap
        or inefficient navigation.

        Args:
            window_size: Number of recent elements to check for patterns

        Returns:
            True if circular navigation is detected, False otherwise
        """
        if len(self._visited_elements) < window_size:
            return False

        recent = self.get_recent_elements(window_size)
        element_ids = [elem.element_id for elem in recent]

        # If all IDs are the same, we're stuck
        if len(set(element_ids)) == 1:
            logger.warning(
                f"Circular navigation detected: stuck on element '{recent[0].nvda_text[:50]}...'"
            )
            return True

        # If more than 50% are the same element, likely circular
        most_common_id = max(set(element_ids), key=element_ids.count)
        repeat_count = element_ids.count(most_common_id)

        if repeat_count > window_size * 0.5:
            logger.warning(
                f"Possible circular navigation: element appears {repeat_count}/{window_size} times"
            )
            return True

        return False

    def get_navigation_summary(self) -> dict[str, int]:
        """Get summary statistics about navigation.

        Returns:
            Dictionary with navigation statistics:
            - total_elements: Total elements visited
            - interactive_elements: Count of interactive elements
            - unique_elements: Count of unique elements
            - repeat_rate: Percentage of repeated elements
        """
        total = len(self._visited_elements)
        interactive = len(self.get_interactive_elements())
        unique = len(self._element_ids_seen)
        repeat_rate = ((total - unique) / total * 100) if total > 0 else 0.0

        return {
            "total_elements": total,
            "interactive_elements": interactive,
            "unique_elements": unique,
            "repeat_rate": repeat_rate,
        }
