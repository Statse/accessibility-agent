"""Feedback correlator for matching keyboard actions with NVDA output.

This module provides the core correlation logic for matching keyboard actions
(from ActionLogger) with NVDA screen reader output (from OutputMonitor).
"""

import logging
import time
from collections import deque
from datetime import datetime, timedelta
from typing import Callable, Optional

from .action_logger import ActionLogger
from .models import CorrelatedEvent, KeyboardAction, NVDAOutput

logger = logging.getLogger(__name__)


class FeedbackCorrelator:
    """Correlates keyboard actions with NVDA feedback output.

    This class implements the action-feedback correlation algorithm:
    1. Receives keyboard actions from ActionLogger
    2. Receives NVDA output events
    3. Matches each action with the first output after it
    4. Handles timeouts for actions with no corresponding output
    5. Stores correlated events for analysis

    Attributes:
        action_logger: ActionLogger instance for retrieving keyboard actions
        correlation_timeout: Seconds to wait for NVDA output after action
        max_history: Maximum number of correlated events to keep in memory
    """

    def __init__(
        self,
        action_logger: ActionLogger,
        correlation_timeout: float = 2.0,
        max_history: int = 1000,
    ) -> None:
        """Initialize the feedback correlator.

        Args:
            action_logger: ActionLogger instance to retrieve keyboard actions from
            correlation_timeout: Seconds to wait for NVDA output after action.
                Default is 2.0 seconds.
            max_history: Maximum number of correlated events to keep in memory.
                Older events are automatically removed. Default is 1000.

        Raises:
            ValueError: If correlation_timeout is negative or max_history < 1.
        """
        if correlation_timeout < 0:
            raise ValueError(
                f"correlation_timeout must be >= 0, got {correlation_timeout}"
            )
        if max_history < 1:
            raise ValueError(f"max_history must be >= 1, got {max_history}")

        self.action_logger = action_logger
        self.correlation_timeout = correlation_timeout
        self.max_history = max_history

        # Buffers for pending correlation
        self._pending_outputs: deque[NVDAOutput] = deque()
        self._pending_actions: deque[KeyboardAction] = deque()

        # Completed correlations
        self._correlated_events: deque[CorrelatedEvent] = deque(maxlen=max_history)

        # Callbacks
        self._on_correlation_callback: Optional[Callable[[CorrelatedEvent], None]] = None
        self._on_timeout_callback: Optional[Callable[[CorrelatedEvent], None]] = None

        logger.info(
            f"FeedbackCorrelator initialized "
            f"(timeout={correlation_timeout}s, max_history={max_history})"
        )

    def on_correlation(
        self, callback: Callable[[CorrelatedEvent], None]
    ) -> None:
        """Register callback for successful correlations.

        Args:
            callback: Function called when action is correlated with output
        """
        self._on_correlation_callback = callback

    def on_timeout(
        self, callback: Callable[[CorrelatedEvent], None]
    ) -> None:
        """Register callback for correlation timeouts.

        Args:
            callback: Function called when action times out without output
        """
        self._on_timeout_callback = callback

    def add_nvda_output(self, output: NVDAOutput) -> None:
        """Add NVDA output for correlation.

        This method should be called whenever new NVDA output is detected.
        The output will be correlated with pending actions.

        Args:
            output: NVDAOutput instance with text and timestamp
        """
        self._pending_outputs.append(output)
        logger.debug(
            f"Added NVDA output: '{output.text[:50]}...' "
            f"(id={output.output_id[:8]}...)"
        )

        # Try to correlate immediately
        self._process_correlations()

    def correlate_action(
        self, action: KeyboardAction, wait: bool = False
    ) -> Optional[CorrelatedEvent]:
        """Correlate a specific action with NVDA output.

        Args:
            action: KeyboardAction to correlate
            wait: If True, wait up to correlation_timeout for output.
                If False, attempt immediate correlation only.

        Returns:
            CorrelatedEvent if correlation successful or timeout,
            None if wait=False and no output available yet
        """
        # Add to pending actions
        self._pending_actions.append(action)

        if wait:
            # Wait for output or timeout
            start_time = time.time()
            while time.time() - start_time < self.correlation_timeout:
                self._process_correlations()

                # Check if this action was correlated
                for event in self._correlated_events:
                    if event.action.action_id == action.action_id:
                        return event

                time.sleep(0.05)  # Poll every 50ms

            # Timeout
            return self._create_timeout_event(action)
        else:
            # Try immediate correlation
            self._process_correlations()

            # Check if correlated
            for event in self._correlated_events:
                if event.action.action_id == action.action_id:
                    return event

            return None

    def _process_correlations(self) -> None:
        """Process pending actions and outputs to create correlations."""
        actions_to_remove: list[KeyboardAction] = []
        now = datetime.now()

        for action in self._pending_actions:
            # Find first output after this action
            matching_output: Optional[NVDAOutput] = None

            for output in self._pending_outputs:
                if output.timestamp > action.timestamp:
                    matching_output = output
                    break

            if matching_output:
                # Successfully correlated
                event = self._create_correlation_event(action, matching_output)
                self._correlated_events.append(event)
                actions_to_remove.append(action)
                self._pending_outputs.remove(matching_output)

                logger.debug(
                    f"Correlated: {action.key} → '{matching_output.text[:30]}...' "
                    f"(latency={event.latency_ms:.1f}ms)"
                )

                if self._on_correlation_callback:
                    self._on_correlation_callback(event)

            else:
                # Check if timeout
                elapsed = (now - action.timestamp).total_seconds()

                if elapsed > self.correlation_timeout:
                    # Timeout - no output detected
                    event = self._create_timeout_event(action)
                    self._correlated_events.append(event)
                    actions_to_remove.append(action)

                    logger.warning(
                        f"Correlation timeout: {action.key} "
                        f"(waited {elapsed:.1f}s, no NVDA output)"
                    )

                    if self._on_timeout_callback:
                        self._on_timeout_callback(event)

        # Remove processed actions
        for action in actions_to_remove:
            self._pending_actions.remove(action)

    def _create_correlation_event(
        self, action: KeyboardAction, output: NVDAOutput
    ) -> CorrelatedEvent:
        """Create a successful correlation event.

        Args:
            action: The keyboard action
            output: The NVDA output that resulted from the action

        Returns:
            CorrelatedEvent with success=True
        """
        latency_ms = (output.timestamp - action.timestamp).total_seconds() * 1000

        return CorrelatedEvent(
            action=action,
            output=output,
            latency_ms=latency_ms,
            success=True,
        )

    def _create_timeout_event(self, action: KeyboardAction) -> CorrelatedEvent:
        """Create a timeout correlation event.

        Args:
            action: The keyboard action that timed out

        Returns:
            CorrelatedEvent with success=False and output=None
        """
        elapsed_ms = (
            datetime.now() - action.timestamp
        ).total_seconds() * 1000

        return CorrelatedEvent(
            action=action,
            output=None,
            latency_ms=elapsed_ms,
            success=False,
        )

    def get_all_events(self) -> list[CorrelatedEvent]:
        """Get all correlated events in chronological order.

        Returns:
            List of all CorrelatedEvents
        """
        return list(self._correlated_events)

    def get_successful_events(self) -> list[CorrelatedEvent]:
        """Get all successful correlations (action had NVDA output).

        Returns:
            List of CorrelatedEvents where success=True
        """
        return [event for event in self._correlated_events if event.success]

    def get_timeout_events(self) -> list[CorrelatedEvent]:
        """Get all timeout events (action had no NVDA output).

        Timeout events may indicate accessibility issues (unlabeled elements).

        Returns:
            List of CorrelatedEvents where success=False
        """
        return [event for event in self._correlated_events if not event.success]

    def get_events_in_range(
        self, start: datetime, end: datetime
    ) -> list[CorrelatedEvent]:
        """Get all events within a time range.

        Args:
            start: Start of time range (inclusive)
            end: End of time range (inclusive)

        Returns:
            List of CorrelatedEvents within the range
        """
        return [
            event
            for event in self._correlated_events
            if start <= event.action.timestamp <= end
        ]

    def get_events_in_last_seconds(self, seconds: float) -> list[CorrelatedEvent]:
        """Get all events from the last N seconds.

        Args:
            seconds: Number of seconds to look back

        Returns:
            List of CorrelatedEvents from the last N seconds
        """
        cutoff = datetime.now() - timedelta(seconds=seconds)
        return [
            event
            for event in self._correlated_events
            if event.action.timestamp >= cutoff
        ]

    def get_statistics(self) -> dict[str, int | float]:
        """Get correlation statistics.

        Returns:
            Dictionary with correlation metrics:
            - total_events: Total number of correlated events
            - successful_correlations: Number of successful correlations
            - timeouts: Number of timeout events
            - timeout_rate: Percentage of events that timed out
            - average_latency_ms: Average latency for successful correlations
            - pending_actions: Number of actions awaiting correlation
            - pending_outputs: Number of NVDA outputs awaiting correlation
        """
        total = len(self._correlated_events)
        successful = len(self.get_successful_events())
        timeouts = len(self.get_timeout_events())

        timeout_rate = (timeouts / total * 100) if total > 0 else 0.0

        # Calculate average latency for successful correlations
        successful_events = self.get_successful_events()
        avg_latency = 0.0
        if successful_events:
            avg_latency = sum(e.latency_ms for e in successful_events) / len(
                successful_events
            )

        return {
            "total_events": total,
            "successful_correlations": successful,
            "timeouts": timeouts,
            "timeout_rate": timeout_rate,
            "average_latency_ms": avg_latency,
            "pending_actions": len(self._pending_actions),
            "pending_outputs": len(self._pending_outputs),
        }

    def clear(self) -> None:
        """Clear all correlation data from memory."""
        event_count = len(self._correlated_events)
        self._correlated_events.clear()
        self._pending_actions.clear()
        self._pending_outputs.clear()

        logger.info(
            f"Cleared correlation data "
            f"({event_count} events, "
            f"{len(self._pending_actions)} pending actions, "
            f"{len(self._pending_outputs)} pending outputs)"
        )

    def force_correlate_pending(self) -> list[CorrelatedEvent]:
        """Force correlation of all pending actions (mark as timeout if no output).

        This is useful when shutting down or when you want to finalize all correlations.

        Returns:
            List of newly created CorrelatedEvents (timeouts)
        """
        new_events: list[CorrelatedEvent] = []

        for action in list(self._pending_actions):
            event = self._create_timeout_event(action)
            self._correlated_events.append(event)
            new_events.append(event)
            self._pending_actions.remove(action)

            logger.debug(f"Force-correlated (timeout): {action.key}")

        return new_events
