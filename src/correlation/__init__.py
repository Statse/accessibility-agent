"""Correlation module for matching keyboard actions with NVDA output."""

from .models import KeyboardAction, NVDAOutput, CorrelatedEvent
from .action_logger import ActionLogger
from .correlator import FeedbackCorrelator
from .formatter import CorrelationFormatter

__all__ = [
    "KeyboardAction",
    "NVDAOutput",
    "CorrelatedEvent",
    "ActionLogger",
    "FeedbackCorrelator",
    "CorrelationFormatter",
]
