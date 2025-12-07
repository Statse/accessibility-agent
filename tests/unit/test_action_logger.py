"""Unit tests for ActionLogger."""

from datetime import datetime, timedelta

import pytest

from src.correlation.action_logger import ActionLogger
from src.correlation.models import KeyboardAction


class TestActionLoggerInitialization:
    """Tests for ActionLogger initialization."""

    def test_create_default_logger(self) -> None:
        """Test creating ActionLogger with default settings."""
        logger = ActionLogger()

        assert logger.max_history == 1000
        assert logger.get_action_count() == 0

    def test_create_logger_with_custom_max_history(self) -> None:
        """Test creating ActionLogger with custom max_history."""
        logger = ActionLogger(max_history=50)

        assert logger.max_history == 50
        assert logger.get_action_count() == 0

    def test_create_logger_with_min_max_history(self) -> None:
        """Test creating ActionLogger with minimum max_history (1)."""
        logger = ActionLogger(max_history=1)

        assert logger.max_history == 1
        assert logger.get_action_count() == 0

    def test_create_logger_with_invalid_max_history(self) -> None:
        """Test that creating ActionLogger with invalid max_history raises ValueError."""
        with pytest.raises(ValueError, match="max_history must be >= 1"):
            ActionLogger(max_history=0)

        with pytest.raises(ValueError, match="max_history must be >= 1"):
            ActionLogger(max_history=-1)


class TestLogAction:
    """Tests for logging keyboard actions."""

    def test_log_basic_action(self) -> None:
        """Test logging a basic keyboard action."""
        logger = ActionLogger()
        action = logger.log_action("Tab")

        assert action.key == "Tab"
        assert action.modifiers == []
        assert action.context is None
        assert isinstance(action.timestamp, datetime)
        assert isinstance(action.action_id, str)
        assert logger.get_action_count() == 1

    def test_log_action_with_modifiers(self) -> None:
        """Test logging an action with modifier keys."""
        logger = ActionLogger()
        action = logger.log_action("F", modifiers=["Ctrl"])

        assert action.key == "F"
        assert action.modifiers == ["Ctrl"]
        assert logger.get_action_count() == 1

    def test_log_action_with_multiple_modifiers(self) -> None:
        """Test logging an action with multiple modifiers."""
        logger = ActionLogger()
        action = logger.log_action("c", modifiers=["Ctrl", "Shift"])

        assert action.key == "c"
        assert action.modifiers == ["Ctrl", "Shift"]

    def test_log_action_with_context(self) -> None:
        """Test logging an action with context."""
        logger = ActionLogger()
        action = logger.log_action("Enter", context="Submit login form")

        assert action.key == "Enter"
        assert action.context == "Submit login form"

    def test_log_action_with_all_parameters(self) -> None:
        """Test logging an action with all parameters."""
        logger = ActionLogger()
        action = logger.log_action(
            "s",
            modifiers=["Ctrl"],
            context="Save file",
        )

        assert action.key == "s"
        assert action.modifiers == ["Ctrl"]
        assert action.context == "Save file"

    def test_log_multiple_actions(self) -> None:
        """Test logging multiple actions."""
        logger = ActionLogger()

        action1 = logger.log_action("Tab")
        action2 = logger.log_action("Enter")
        action3 = logger.log_action("h")

        assert logger.get_action_count() == 3
        assert action1.action_id != action2.action_id != action3.action_id

    def test_log_action_timestamps_increase(self) -> None:
        """Test that action timestamps increase in order."""
        logger = ActionLogger()

        action1 = logger.log_action("Tab")
        action2 = logger.log_action("Tab")

        assert action2.timestamp >= action1.timestamp


class TestGetActionById:
    """Tests for retrieving actions by ID."""

    def test_get_action_by_id_found(self) -> None:
        """Test retrieving an action by its ID."""
        logger = ActionLogger()
        action = logger.log_action("Tab")

        retrieved = logger.get_action_by_id(action.action_id)

        assert retrieved is not None
        assert retrieved.action_id == action.action_id
        assert retrieved.key == "Tab"

    def test_get_action_by_id_not_found(self) -> None:
        """Test retrieving a non-existent action returns None."""
        logger = ActionLogger()
        logger.log_action("Tab")

        retrieved = logger.get_action_by_id("non-existent-id")

        assert retrieved is None

    def test_get_action_by_id_from_multiple_actions(self) -> None:
        """Test retrieving specific action from multiple logged actions."""
        logger = ActionLogger()

        action1 = logger.log_action("Tab")
        action2 = logger.log_action("Enter")
        action3 = logger.log_action("h")

        retrieved = logger.get_action_by_id(action2.action_id)

        assert retrieved is not None
        assert retrieved.action_id == action2.action_id
        assert retrieved.key == "Enter"


class TestGetActionsAfter:
    """Tests for getting actions after a timestamp."""

    def test_get_actions_after_with_results(self) -> None:
        """Test getting actions after a timestamp."""
        logger = ActionLogger()

        action1 = logger.log_action("Tab")
        cutoff = datetime.now()
        action2 = logger.log_action("Enter")
        action3 = logger.log_action("h")

        actions = logger.get_actions_after(cutoff)

        assert len(actions) == 2
        assert actions[0].action_id == action2.action_id
        assert actions[1].action_id == action3.action_id

    def test_get_actions_after_no_results(self) -> None:
        """Test getting actions after a future timestamp returns empty list."""
        logger = ActionLogger()

        logger.log_action("Tab")
        logger.log_action("Enter")

        future = datetime.now() + timedelta(hours=1)
        actions = logger.get_actions_after(future)

        assert len(actions) == 0

    def test_get_actions_after_with_max_results(self) -> None:
        """Test getting actions after timestamp with max_results limit."""
        logger = ActionLogger()

        action1 = logger.log_action("Tab")
        cutoff = datetime.now()
        action2 = logger.log_action("Enter")
        action3 = logger.log_action("h")
        action4 = logger.log_action("k")

        actions = logger.get_actions_after(cutoff, max_results=2)

        assert len(actions) == 2
        assert actions[0].action_id == action2.action_id
        assert actions[1].action_id == action3.action_id


class TestGetActionsBefore:
    """Tests for getting actions before a timestamp."""

    def test_get_actions_before_with_results(self) -> None:
        """Test getting actions before a timestamp."""
        logger = ActionLogger()

        action1 = logger.log_action("Tab")
        action2 = logger.log_action("Enter")
        cutoff = datetime.now()
        action3 = logger.log_action("h")

        actions = logger.get_actions_before(cutoff)

        assert len(actions) == 2
        assert actions[0].action_id == action1.action_id
        assert actions[1].action_id == action2.action_id

    def test_get_actions_before_no_results(self) -> None:
        """Test getting actions before a past timestamp returns empty list."""
        logger = ActionLogger()

        past = datetime.now() - timedelta(hours=1)

        logger.log_action("Tab")
        logger.log_action("Enter")

        actions = logger.get_actions_before(past)

        assert len(actions) == 0

    def test_get_actions_before_with_max_results(self) -> None:
        """Test getting actions before timestamp with max_results limit."""
        logger = ActionLogger()

        action1 = logger.log_action("Tab")
        action2 = logger.log_action("Enter")
        action3 = logger.log_action("h")
        cutoff = datetime.now()
        action4 = logger.log_action("k")

        # Should get the most recent N actions before cutoff
        actions = logger.get_actions_before(cutoff, max_results=2)

        assert len(actions) == 2
        assert actions[0].action_id == action2.action_id
        assert actions[1].action_id == action3.action_id


class TestGetActionsInRange:
    """Tests for getting actions within a time range."""

    def test_get_actions_in_range_with_results(self) -> None:
        """Test getting actions within a time range."""
        logger = ActionLogger()

        action1 = logger.log_action("Tab")
        start = datetime.now()
        action2 = logger.log_action("Enter")
        action3 = logger.log_action("h")
        end = datetime.now()
        action4 = logger.log_action("k")

        actions = logger.get_actions_in_range(start, end)

        assert len(actions) == 2
        assert actions[0].action_id == action2.action_id
        assert actions[1].action_id == action3.action_id

    def test_get_actions_in_range_no_results(self) -> None:
        """Test getting actions in range with no matching actions."""
        logger = ActionLogger()

        logger.log_action("Tab")

        past_start = datetime.now() - timedelta(hours=2)
        past_end = datetime.now() - timedelta(hours=1)

        actions = logger.get_actions_in_range(past_start, past_end)

        assert len(actions) == 0

    def test_get_actions_in_range_inclusive(self) -> None:
        """Test that range is inclusive on both ends."""
        logger = ActionLogger()

        action1 = logger.log_action("Tab")
        start = action1.timestamp
        action2 = logger.log_action("Enter")
        end = action2.timestamp

        actions = logger.get_actions_in_range(start, end)

        assert len(actions) == 2


class TestGetMostRecentAction:
    """Tests for getting the most recent action."""

    def test_get_most_recent_action_with_actions(self) -> None:
        """Test getting most recent action."""
        logger = ActionLogger()

        logger.log_action("Tab")
        logger.log_action("Enter")
        action3 = logger.log_action("h")

        most_recent = logger.get_most_recent_action()

        assert most_recent is not None
        assert most_recent.action_id == action3.action_id

    def test_get_most_recent_action_empty_logger(self) -> None:
        """Test getting most recent action from empty logger returns None."""
        logger = ActionLogger()

        most_recent = logger.get_most_recent_action()

        assert most_recent is None


class TestGetActionCount:
    """Tests for getting action count."""

    def test_get_action_count_empty(self) -> None:
        """Test getting count from empty logger."""
        logger = ActionLogger()

        assert logger.get_action_count() == 0

    def test_get_action_count_with_actions(self) -> None:
        """Test getting count with actions logged."""
        logger = ActionLogger()

        logger.log_action("Tab")
        assert logger.get_action_count() == 1

        logger.log_action("Enter")
        assert logger.get_action_count() == 2

        logger.log_action("h")
        assert logger.get_action_count() == 3


class TestClear:
    """Tests for clearing the action logger."""

    def test_clear_empty_logger(self) -> None:
        """Test clearing an empty logger."""
        logger = ActionLogger()

        logger.clear()

        assert logger.get_action_count() == 0

    def test_clear_logger_with_actions(self) -> None:
        """Test clearing a logger with actions."""
        logger = ActionLogger()

        logger.log_action("Tab")
        logger.log_action("Enter")
        logger.log_action("h")

        assert logger.get_action_count() == 3

        logger.clear()

        assert logger.get_action_count() == 0
        assert logger.get_most_recent_action() is None


class TestGetActionsInLastSeconds:
    """Tests for getting actions in the last N seconds."""

    def test_get_actions_in_last_seconds_with_results(self) -> None:
        """Test getting actions from the last N seconds."""
        logger = ActionLogger()

        action1 = logger.log_action("Tab")
        action2 = logger.log_action("Enter")

        # Get actions from last 10 seconds
        actions = logger.get_actions_in_last_seconds(10)

        assert len(actions) >= 2  # At least our 2 actions

    def test_get_actions_in_last_seconds_no_results(self) -> None:
        """Test getting actions from last 0 seconds returns empty."""
        logger = ActionLogger()

        logger.log_action("Tab")

        # Get actions from last 0 seconds (should be empty or very few)
        actions = logger.get_actions_in_last_seconds(0)

        # Due to timing, this might be 0 or 1
        assert len(actions) <= 1


class TestGetAllActions:
    """Tests for getting all actions."""

    def test_get_all_actions_empty(self) -> None:
        """Test getting all actions from empty logger."""
        logger = ActionLogger()

        actions = logger.get_all_actions()

        assert len(actions) == 0

    def test_get_all_actions_with_actions(self) -> None:
        """Test getting all actions."""
        logger = ActionLogger()

        action1 = logger.log_action("Tab")
        action2 = logger.log_action("Enter")
        action3 = logger.log_action("h")

        actions = logger.get_all_actions()

        assert len(actions) == 3
        assert actions[0].action_id == action1.action_id
        assert actions[1].action_id == action2.action_id
        assert actions[2].action_id == action3.action_id

    def test_get_all_actions_returns_copy(self) -> None:
        """Test that get_all_actions returns a copy, not the internal buffer."""
        logger = ActionLogger()

        logger.log_action("Tab")
        actions1 = logger.get_all_actions()

        logger.log_action("Enter")
        actions2 = logger.get_all_actions()

        # Original list should not be affected
        assert len(actions1) == 1
        assert len(actions2) == 2


class TestBufferOverflow:
    """Tests for buffer overflow behavior when max_history is reached."""

    def test_buffer_respects_max_history(self) -> None:
        """Test that buffer doesn't exceed max_history."""
        logger = ActionLogger(max_history=3)

        logger.log_action("Tab")
        logger.log_action("Enter")
        logger.log_action("h")

        assert logger.get_action_count() == 3

        # Add 4th action - should remove oldest
        action4 = logger.log_action("k")

        assert logger.get_action_count() == 3
        assert logger.get_most_recent_action().action_id == action4.action_id

    def test_buffer_fifo_behavior(self) -> None:
        """Test that buffer follows FIFO when max_history is reached."""
        logger = ActionLogger(max_history=3)

        action1 = logger.log_action("Tab")
        action2 = logger.log_action("Enter")
        action3 = logger.log_action("h")
        action4 = logger.log_action("k")

        # First action should be gone
        assert logger.get_action_by_id(action1.action_id) is None

        # Other 3 should still be there
        assert logger.get_action_by_id(action2.action_id) is not None
        assert logger.get_action_by_id(action3.action_id) is not None
        assert logger.get_action_by_id(action4.action_id) is not None

    def test_buffer_overflow_with_min_history(self) -> None:
        """Test buffer with minimum max_history of 1."""
        logger = ActionLogger(max_history=1)

        action1 = logger.log_action("Tab")
        assert logger.get_action_count() == 1

        action2 = logger.log_action("Enter")
        assert logger.get_action_count() == 1

        # Only most recent action should remain
        assert logger.get_action_by_id(action1.action_id) is None
        assert logger.get_action_by_id(action2.action_id) is not None
