"""Navigation module for web page exploration strategies."""

from .navigator import Navigator, NavigationResult, ElementType
from .interaction_strategies import (
    InteractionStrategy,
    FormFillingStrategy,
    LinkActivationStrategy,
    PageExplorationStrategy,
)

__all__ = [
    "Navigator",
    "NavigationResult",
    "ElementType",
    "InteractionStrategy",
    "FormFillingStrategy",
    "LinkActivationStrategy",
    "PageExplorationStrategy",
]
