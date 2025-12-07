"""Action logger for tracking keyboard actions with timestamps.

This module provides ActionLogger for recording keyboard actions
performed by the agent, storing them in memory for correlation
with NVDA output.
"""

import logging
from collections import deque
from datetime import datetime, timedelta
from typing import Optional

from .models import KeyboardAction

logger = logging.getLogger(__name__)


class ActionLogger:
    """Logs keyboard actions with timestamps for correlation.

    This logger maintains an in-memory buffer of keyboard actions
    performed by the agent. Actions are stored with precise timestamps
    and can be retrieved for correlation with NVDA output.

    Attributes:
        max_history: Maximum number of actions to keep in memory
        _actions: Deque storing recent keyboard actions
    """

    def __init__(self, max_history: int = 1000) -> None:
        """Initialize the action logger.

        Args:
            max_history: Maximum number of actions to keep in memory.
                Older actions are automatically removed when limit is reached.
                Default is 1000 actions.

        Raises:
            ValueError: If max_history is less than 1.
        """
        if max_history < 1:
            raise ValueError(f"max_history must be >= 1, got {max_history}")

        self.max_history = max_history
        self._actions: deque[KeyboardAction] = deque(maxlen=max_history)
        logger.info(f"ActionLogger initialized with max_history={max_history}")

    def log_action(
        self,
        key: str,
        modifiers: Optional[list[str]] = None,
        context: Optional[str] = None,
    ) -> KeyboardAction:
        """Log a keyboard action with timestamp.

        Args:
            key: The key that was pressed (e.g., "Tab", "Enter", "h")
            modifiers: List of modifier keys held (e.g., ["Ctrl", "Shift"])
            context: Optional context about the action's purpose

        Returns:
            The created KeyboardAction with unique ID and timestamp
        """
        if modifiers is None:
            modifiers = []

        action = KeyboardAction(
            key=key,
            modifiers=modifiers,
            context=context,
        )

        self._actions.append(action)
        logger.debug(
            f"Logged action: {action.key} "
            f"(modifiers={action.modifiers}, id={action.action_id[:8]}...)"
        )

        return action

    def get_action_by_id(self, action_id: str) -> Optional[KeyboardAction]:
        """Retrieve an action by its ID.

        Args:
            action_id: The unique ID of the action to retrieve

        Returns:
            The KeyboardAction if found, None otherwise
        """
        for action in self._actions:
            if action.action_id == action_id:
                return action
        return None

    def get_actions_after(
        self, timestamp: datetime, max_results: Optional[int] = None
    ) -> list[KeyboardAction]:
        """Get all actions that occurred after a given timestamp.

        Args:
            timestamp: Return actions after this time
            max_results: Maximum number of actions to return (None = all)

        Returns:
            List of KeyboardActions after the timestamp, in chronological order
        """
        matching_actions = [
            action for action in self._actions if action.timestamp > timestamp
        ]

        if max_results is not None:
            matching_actions = matching_actions[:max_results]

        return matching_actions

    def get_actions_before(
        self, timestamp: datetime, max_results: Optional[int] = None
    ) -> list[KeyboardAction]:
        """Get all actions that occurred before a given timestamp.

        Args:
            timestamp: Return actions before this time
            max_results: Maximum number of actions to return (None = all)

        Returns:
            List of KeyboardActions before the timestamp, in chronological order
        """
        matching_actions = [
            action for action in self._actions if action.timestamp < timestamp
        ]

        if max_results is not None:
            # Get the most recent N actions
            matching_actions = matching_actions[-max_results:]

        return matching_actions

    def get_actions_in_range(
        self, start: datetime, end: datetime
    ) -> list[KeyboardAction]:
        """Get all actions within a time range.

        Args:
            start: Start of time range (inclusive)
            end: End of time range (inclusive)

        Returns:
            List of KeyboardActions within the range, in chronological order
        """
        return [
            action
            for action in self._actions
            if start <= action.timestamp <= end
        ]

    def get_most_recent_action(self) -> Optional[KeyboardAction]:
        """Get the most recently logged action.

        Returns:
            The most recent KeyboardAction, or None if no actions logged
        """
        if not self._actions:
            return None
        return self._actions[-1]

    def get_action_count(self) -> int:
        """Get the total number of actions currently in memory.

        Returns:
            Number of actions in the buffer
        """
        return len(self._actions)

    def clear(self) -> None:
        """Clear all logged actions from memory."""
        count = len(self._actions)
        self._actions.clear()
        logger.info(f"Cleared {count} actions from action logger")

    def get_actions_in_last_seconds(self, seconds: float) -> list[KeyboardAction]:
        """Get all actions from the last N seconds.

        Args:
            seconds: Number of seconds to look back

        Returns:
            List of KeyboardActions from the last N seconds
        """
        cutoff = datetime.now() - timedelta(seconds=seconds)
        return self.get_actions_after(cutoff)

    def get_all_actions(self) -> list[KeyboardAction]:
        """Get all actions currently in memory.

        Returns:
            List of all KeyboardActions in chronological order
        """
        return list(self._actions)
