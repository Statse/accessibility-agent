"""Main accessibility testing agent powered by Pydantic AI."""

import hashlib
import logging
from typing import Optional

from pydantic_ai import Agent, RunContext

from ..automation.keyboard_controller import KeyboardController, NVDAKey
from ..correlation.action_logger import ActionLogger
from ..correlation.correlator import FeedbackCorrelator
from ..correlation.models import NVDAOutput
from .decision_engine import (
    AgentState,
    DecisionEngine,
    NavigationAction,
    NavigationDecision,
    NavigationStrategy,
)
from .memory import AgentMemory, VisitedElement

logger = logging.getLogger(__name__)


# System prompt for the accessibility testing agent
SCREEN_READER_USER_PERSONA = """You are an experienced screen reader user who is blind and relies on NVDA (NonVisual Desktop Access) to navigate websites.

Your goal is to thoroughly explore a website and identify accessibility issues that would prevent screen reader users from successfully using the site.

**Your capabilities:**
- You can send keyboard commands (Tab, Enter, arrow keys, NVDA shortcuts like h/k/d/f/b)
- You receive feedback from NVDA about what is announced
- You understand WCAG 2.1/2.2 accessibility guidelines
- You can detect missing labels, poor structure, keyboard traps, and other accessibility barriers

**Your navigation strategy:**
1. Start by reading the page title (Insert+T) to understand context
2. Check for skip links at the top (Tab once)
3. Explore headings structure (h key) to understand page layout
4. Navigate through interactive elements (Tab, k for links, b for buttons, f for forms)
5. Test form interactions (labels, error messages)
6. Identify any elements you cannot reach or understand
7. Document all accessibility issues you encounter

**Important notes:**
- You cannot see the page. You rely entirely on NVDA's audio output.
- If NVDA is silent or unclear, that's an accessibility issue.
- If you get stuck in the same elements repeatedly, that's a keyboard trap (WCAG 2.1.2 violation).
- Missing labels, unclear link text, and unlabeled images are critical issues.
- You have limited actions (typically 100), so be strategic in your exploration.

**Decision-making:**
- Prioritize exploring unique elements over revisiting known ones
- When encountering silence (no NVDA output), note it as a potential issue
- When stuck, try different navigation strategies (headings, landmarks, forms)
- Balance between thorough exploration and efficient navigation
"""


class AccessibilityAgentDependencies:
    """Dependencies for the Pydantic AI agent.

    This class holds all the components the agent needs to function,
    which are passed to the agent's tools as dependencies.

    Attributes:
        keyboard_controller: For sending keyboard input
        decision_engine: For making navigation decisions
        memory: For tracking visited elements
        action_logger: For logging keyboard actions
        correlator: For correlating actions with NVDA output
    """

    def __init__(
        self,
        keyboard_controller: KeyboardController,
        decision_engine: DecisionEngine,
        memory: AgentMemory,
        action_logger: ActionLogger,
        correlator: FeedbackCorrelator,
    ):
        self.keyboard_controller = keyboard_controller
        self.decision_engine = decision_engine
        self.memory = memory
        self.action_logger = action_logger
        self.correlator = correlator


class AccessibilityAgent:
    """AI-powered accessibility testing agent.

    This agent uses Pydantic AI to make intelligent decisions about how to
    navigate a website and identify accessibility issues, simulating an
    experienced screen reader user.

    Attributes:
        keyboard_controller: Keyboard control interface
        decision_engine: Decision-making logic
        memory: Agent memory for visited elements
        action_logger: Logs keyboard actions
        correlator: Correlates actions with NVDA output
        agent: Pydantic AI agent instance
        current_url: URL being tested
    """

    def __init__(
        self,
        keyboard_controller: Optional[KeyboardController] = None,
        decision_engine: Optional[DecisionEngine] = None,
        memory: Optional[AgentMemory] = None,
        action_logger: Optional[ActionLogger] = None,
        correlator: Optional[FeedbackCorrelator] = None,
        model: str = "openai:gpt-4",
    ):
        """Initialize the accessibility agent.

        Args:
            keyboard_controller: Keyboard controller (creates new if None)
            decision_engine: Decision engine (creates new if None)
            memory: Agent memory (creates new if None)
            action_logger: Action logger (creates new if None)
            correlator: Feedback correlator (creates new if None)
            model: Pydantic AI model to use (default: openai:gpt-4)
        """
        # Initialize components
        self.keyboard_controller = keyboard_controller or KeyboardController()
        self.decision_engine = decision_engine or DecisionEngine()
        self.memory = memory or AgentMemory()
        self.action_logger = action_logger or ActionLogger()

        # Correlator needs action_logger
        if correlator is None:
            self.correlator = FeedbackCorrelator(self.action_logger)
        else:
            self.correlator = correlator

        # Create dependencies bundle
        self.deps = AccessibilityAgentDependencies(
            keyboard_controller=self.keyboard_controller,
            decision_engine=self.decision_engine,
            memory=self.memory,
            action_logger=self.action_logger,
            correlator=self.correlator,
        )

        # Create Pydantic AI agent
        self.agent: Agent[AccessibilityAgentDependencies, str] = Agent(
            model=model,
            system_prompt=SCREEN_READER_USER_PERSONA,
            deps_type=AccessibilityAgentDependencies,
        )

        # Register tools
        self._register_tools()

        self.current_url: Optional[str] = None

        logger.info(f"AccessibilityAgent initialized with model={model}")

    def _register_tools(self) -> None:
        """Register tools that the agent can use."""

        @self.agent.tool
        async def press_key(
            ctx: RunContext[AccessibilityAgentDependencies], key: str
        ) -> str:
            """Press a keyboard key and wait for NVDA response.

            Args:
                ctx: Run context with dependencies
                key: The key to press (e.g., 'Tab', 'Enter', 'h', 'Insert+t')

            Returns:
                NVDA output text, or description of what happened
            """
            deps = ctx.deps
            logger.info(f"Agent pressing key: {key}")

            # Parse key and modifiers
            modifiers = []
            actual_key = key

            if "+" in key:
                parts = key.split("+")
                modifiers = parts[:-1]
                actual_key = parts[-1]

            # Log the action
            action = deps.action_logger.log_action(
                actual_key, modifiers=modifiers, context=f"Agent decision: {key}"
            )

            # Press the key
            try:
                if key == "Tab":
                    deps.keyboard_controller.press_tab()
                elif key == "Shift+Tab":
                    deps.keyboard_controller.press_shift_tab()
                elif key == "Enter":
                    deps.keyboard_controller.press_enter()
                elif key == "Space":
                    deps.keyboard_controller.press_space()
                elif key == "Escape":
                    deps.keyboard_controller.press_escape()
                elif key in ["h", "k", "d", "f", "b", "l"]:
                    # NVDA navigation keys
                    nvda_key = NVDAKey(key.upper() if key.isupper() else key.lower())
                    deps.keyboard_controller.press_nvda_key(nvda_key)
                elif key == "Insert+t":
                    deps.keyboard_controller.press_nvda_read_title()
                elif key == "Insert+Down":
                    deps.keyboard_controller.press_nvda_say_all()
                else:
                    # Generic key press
                    deps.keyboard_controller.press_key(actual_key, modifiers)

                # Increment action counter
                deps.decision_engine.increment_actions()

                # Wait for NVDA output (this would come from output monitor in real usage)
                # For now, return a placeholder
                return f"Key '{key}' pressed successfully. Waiting for NVDA output..."

            except Exception as e:
                logger.error(f"Error pressing key '{key}': {e}")
                return f"Error pressing key '{key}': {str(e)}"

        @self.agent.tool
        async def get_decision(
            ctx: RunContext[AccessibilityAgentDependencies],
            nvda_output: str = "",
        ) -> dict:
            """Get navigation decision based on current context.

            Args:
                ctx: Run context with dependencies
                nvda_output: Latest NVDA output

            Returns:
                Dictionary with decision details
            """
            deps = ctx.deps

            # Check memory
            element_id = self._hash_element(nvda_output)
            has_visited = deps.memory.has_visited(element_id)
            is_circular = deps.memory.detect_circular_navigation()

            # Get decision from engine
            decision = deps.decision_engine.decide_next_action(
                nvda_output=nvda_output,
                is_circular=is_circular,
                has_visited_before=has_visited,
            )

            return {
                "action": decision.action,
                "reasoning": decision.reasoning,
                "expected_outcome": decision.expected_outcome,
                "priority": decision.priority,
                "strategy": decision.strategy,
                "has_visited_before": has_visited,
                "is_circular_navigation": is_circular,
            }

        @self.agent.tool
        async def add_to_memory(
            ctx: RunContext[AccessibilityAgentDependencies],
            nvda_text: str,
            key_used: str,
            is_interactive: bool = False,
        ) -> str:
            """Add visited element to memory.

            Args:
                ctx: Run context with dependencies
                nvda_text: What NVDA announced
                key_used: The key pressed to reach this element
                is_interactive: Whether this is an interactive element

            Returns:
                Confirmation message
            """
            deps = ctx.deps

            element_id = self._hash_element(nvda_text)
            deps.memory.add_element(
                nvda_text=nvda_text,
                key_used=key_used,
                element_id=element_id,
                is_interactive=is_interactive,
            )

            return f"Added element to memory (ID: {element_id[:8]}...)"

        @self.agent.tool
        async def get_navigation_summary(
            ctx: RunContext[AccessibilityAgentDependencies],
        ) -> dict:
            """Get summary of navigation so far.

            Args:
                ctx: Run context with dependencies

            Returns:
                Dictionary with navigation statistics
            """
            deps = ctx.deps
            return deps.memory.get_navigation_summary()

    @staticmethod
    def _hash_element(nvda_text: str) -> str:
        """Create a unique hash for an element based on NVDA text.

        Args:
            nvda_text: NVDA output text

        Returns:
            SHA256 hash of the text
        """
        return hashlib.sha256(nvda_text.encode()).hexdigest()

    async def explore_page(self, url: str, max_actions: int = 50) -> dict:
        """Explore a web page and identify accessibility issues.

        Args:
            url: URL to test
            max_actions: Maximum number of actions to take

        Returns:
            Dictionary with exploration results
        """
        self.current_url = url
        self.decision_engine.max_actions = max_actions
        self.decision_engine.set_state(AgentState.INITIALIZING)

        logger.info(f"Starting page exploration: {url}")

        prompt = f"""Explore the website at {url} and identify accessibility issues.

Start by:
1. Reading the page title (Insert+t)
2. Checking for skip links (Tab once)
3. Exploring the heading structure (press 'h' to navigate headings)
4. Testing interactive elements

Report any accessibility issues you find, especially:
- Missing labels or alt text (NVDA is silent)
- Keyboard traps (stuck in same elements)
- Unclear link text ("click here", "read more")
- Missing form field labels

You have {max_actions} actions available. Be strategic."""

        try:
            # Run the agent
            result = await self.agent.run(prompt, deps=self.deps)

            return {
                "success": True,
                "result": result.data,
                "actions_taken": self.decision_engine.actions_taken,
                "navigation_summary": self.memory.get_navigation_summary(),
            }

        except Exception as e:
            logger.error(f"Error during page exploration: {e}")
            return {
                "success": False,
                "error": str(e),
                "actions_taken": self.decision_engine.actions_taken,
            }

    def add_nvda_output(self, text: str, timestamp=None) -> None:
        """Add NVDA output for correlation.

        This should be called by the output monitor when new NVDA output is detected.

        Args:
            text: NVDA output text
            timestamp: Optional timestamp (uses now() if not provided)
        """
        output = NVDAOutput(text=text)
        if timestamp:
            output.timestamp = timestamp

        self.correlator.add_nvda_output(output)
        logger.debug(f"NVDA output added: '{text[:50]}...'")

    def get_correlation_summary(self) -> dict:
        """Get summary of action-feedback correlations.

        Returns:
            Dictionary with correlation statistics
        """
        return self.correlator.get_statistics()

    def reset(self) -> None:
        """Reset the agent to initial state."""
        self.decision_engine.reset()
        self.memory.clear()
        self.action_logger.clear()
        self.correlator.clear()
        logger.info("AccessibilityAgent reset to initial state")
