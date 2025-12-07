"""Data models for action-feedback correlation.

This module defines Pydantic models for:
- KeyboardAction: Represents a keyboard action with timestamp
- NVDAOutput: Represents NVDA screen reader output
- CorrelatedEvent: Links a keyboard action with its corresponding NVDA feedback
"""

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class KeyboardAction(BaseModel):
    """Represents a keyboard action performed by the agent.

    Attributes:
        timestamp: When the action was performed (with microsecond precision)
        key: The key that was pressed (e.g., "Tab", "Enter", "h")
        modifiers: List of modifier keys held (e.g., ["Ctrl", "Shift"])
        action_id: Unique identifier for this action (for correlation)
        context: Optional context about what the action was intended to do
    """

    model_config = ConfigDict(ser_json_timedelta="iso8601")

    timestamp: datetime = Field(default_factory=datetime.now)
    key: str
    modifiers: list[str] = Field(default_factory=list)
    action_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    context: Optional[str] = None


class NVDAOutput(BaseModel):
    """Represents output from the NVDA screen reader.

    Attributes:
        timestamp: When NVDA produced the output (with microsecond precision)
        text: The text that NVDA announced
        output_id: Unique identifier for this output
        raw_log_entry: Optional raw log entry from NVDA log file
    """

    model_config = ConfigDict(ser_json_timedelta="iso8601")

    timestamp: datetime = Field(default_factory=datetime.now)
    text: str
    output_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    raw_log_entry: Optional[str] = None


class CorrelatedEvent(BaseModel):
    """Links a keyboard action with its corresponding NVDA feedback.

    This is the core data structure for action-feedback correlation.
    It pairs each keyboard action with the NVDA output that resulted from it,
    including timing information and success status.

    Attributes:
        action: The keyboard action that was performed
        output: The NVDA output that resulted (None if timeout)
        latency_ms: Time in milliseconds between action and output
        success: True if output was received within timeout, False otherwise
        correlation_id: Unique identifier for this correlation
    """

    model_config = ConfigDict(ser_json_timedelta="iso8601")

    action: KeyboardAction
    output: Optional[NVDAOutput] = None
    latency_ms: float
    success: bool
    correlation_id: str = Field(default_factory=lambda: str(uuid.uuid4()))

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return self.model_dump(mode="json")
