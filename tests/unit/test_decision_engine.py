"""Tests for agent decision engine module."""

import pytest
from src.agent.decision_engine import (
    NavigationStrategy,
    NavigationAction,
    AgentState,
    NavigationDecision,
    DecisionEngine,
)


class TestEnums:
    """Tests for enum definitions"""

    def test_navigation_strategy_values(self):
        """Test NavigationStrategy enum values"""
        assert NavigationStrategy.SEQUENTIAL_TAB == "sequential_tab"
        assert NavigationStrategy.HEADINGS_FIRST == "headings_first"
        assert NavigationStrategy.LANDMARKS == "landmarks"
        assert NavigationStrategy.LINKS == "links"
        assert NavigationStrategy.FORMS == "forms"
        assert NavigationStrategy.BUTTONS == "buttons"
        assert NavigationStrategy.INTERACTIVE_ONLY == "interactive_only"

    def test_navigation_action_values(self):
        """Test NavigationAction enum has expected actions"""
        assert NavigationAction.TAB == "Tab"
        assert NavigationAction.ENTER == "Enter"
        assert NavigationAction.NEXT_HEADING == "h"
        assert NavigationAction.PREV_HEADING == "H"
        assert NavigationAction.NEXT_LINK == "k"
        assert NavigationAction.READ_TITLE == "Insert+t"

    def test_agent_state_values(self):
        """Test AgentState enum values"""
        assert AgentState.IDLE == "idle"
        assert AgentState.EXPLORING == "exploring"
        assert AgentState.STUCK == "stuck"
        assert AgentState.COMPLETED == "completed"
        assert AgentState.ERROR == "error"


class TestNavigationDecision:
    """Tests for NavigationDecision model"""

    def test_create_basic_decision(self):
        """Test creating a basic navigation decision"""
        decision = NavigationDecision(
            action=NavigationAction.TAB,
            reasoning="Move to next element",
            expected_outcome="Next element is announced"
        )

        assert decision.action == NavigationAction.TAB
        assert decision.reasoning == "Move to next element"
        assert decision.expected_outcome == "Next element is announced"
        assert decision.priority == 5  # Default
        assert decision.strategy == NavigationStrategy.SEQUENTIAL_TAB  # Default

    def test_create_decision_with_all_fields(self):
        """Test creating decision with all fields"""
        decision = NavigationDecision(
            action=NavigationAction.NEXT_HEADING,
            reasoning="Explore page structure",
            expected_outcome="Next heading announced",
            priority=9,
            strategy=NavigationStrategy.HEADINGS_FIRST
        )

        assert decision.action == NavigationAction.NEXT_HEADING
        assert decision.reasoning == "Explore page structure"
        assert decision.expected_outcome == "Next heading announced"
        assert decision.priority == 9
        assert decision.strategy == NavigationStrategy.HEADINGS_FIRST

    def test_priority_validation(self):
        """Test priority must be between 1 and 10"""
        # Valid priorities
        NavigationDecision(
            action=NavigationAction.TAB,
            reasoning="Test",
            expected_outcome="Test",
            priority=1
        )
        NavigationDecision(
            action=NavigationAction.TAB,
            reasoning="Test",
            expected_outcome="Test",
            priority=10
        )

        # Invalid priorities
        with pytest.raises(ValueError):
            NavigationDecision(
                action=NavigationAction.TAB,
                reasoning="Test",
                expected_outcome="Test",
                priority=0
            )

        with pytest.raises(ValueError):
            NavigationDecision(
                action=NavigationAction.TAB,
                reasoning="Test",
                expected_outcome="Test",
                priority=11
            )


class TestDecisionEngineInitialization:
    """Tests for DecisionEngine initialization"""

    def test_create_default_engine(self):
        """Test creating engine with defaults"""
        engine = DecisionEngine()

        assert engine.current_state == AgentState.IDLE
        assert engine.current_strategy == NavigationStrategy.HEADINGS_FIRST
        assert engine.actions_taken == 0
        assert engine.max_actions == 100
        assert engine.stuck_threshold == 5

    def test_create_engine_with_custom_strategy(self):
        """Test creating engine with custom initial strategy"""
        engine = DecisionEngine(initial_strategy=NavigationStrategy.SEQUENTIAL_TAB)

        assert engine.current_strategy == NavigationStrategy.SEQUENTIAL_TAB

    def test_create_engine_with_custom_max_actions(self):
        """Test creating engine with custom max_actions"""
        engine = DecisionEngine(max_actions=50)

        assert engine.max_actions == 50

    def test_create_engine_with_custom_stuck_threshold(self):
        """Test creating engine with custom stuck_threshold"""
        engine = DecisionEngine(stuck_threshold=10)

        assert engine.stuck_threshold == 10

    def test_create_engine_with_all_custom_parameters(self):
        """Test creating engine with all custom parameters"""
        engine = DecisionEngine(
            initial_strategy=NavigationStrategy.LANDMARKS,
            max_actions=200,
            stuck_threshold=8
        )

        assert engine.current_strategy == NavigationStrategy.LANDMARKS
        assert engine.max_actions == 200
        assert engine.stuck_threshold == 8

    def test_invalid_max_actions(self):
        """Test that invalid max_actions raises ValueError"""
        with pytest.raises(ValueError, match="max_actions must be >= 1"):
            DecisionEngine(max_actions=0)

        with pytest.raises(ValueError, match="max_actions must be >= 1"):
            DecisionEngine(max_actions=-10)

    def test_invalid_stuck_threshold(self):
        """Test that invalid stuck_threshold raises ValueError"""
        with pytest.raises(ValueError, match="stuck_threshold must be >= 1"):
            DecisionEngine(stuck_threshold=0)

        with pytest.raises(ValueError, match="stuck_threshold must be >= 1"):
            DecisionEngine(stuck_threshold=-5)


class TestStateManagement:
    """Tests for state management methods"""

    def test_set_state(self):
        """Test setting agent state"""
        engine = DecisionEngine()

        assert engine.current_state == AgentState.IDLE

        engine.set_state(AgentState.EXPLORING)
        assert engine.current_state == AgentState.EXPLORING

        engine.set_state(AgentState.STUCK)
        assert engine.current_state == AgentState.STUCK

    def test_set_state_multiple_transitions(self):
        """Test multiple state transitions"""
        engine = DecisionEngine()

        states = [
            AgentState.INITIALIZING,
            AgentState.EXPLORING,
            AgentState.ANALYZING,
            AgentState.COMPLETED
        ]

        for state in states:
            engine.set_state(state)
            assert engine.current_state == state


class TestStrategyManagement:
    """Tests for strategy management methods"""

    def test_set_strategy(self):
        """Test setting navigation strategy"""
        engine = DecisionEngine()

        assert engine.current_strategy == NavigationStrategy.HEADINGS_FIRST

        engine.set_strategy(NavigationStrategy.SEQUENTIAL_TAB)
        assert engine.current_strategy == NavigationStrategy.SEQUENTIAL_TAB

        engine.set_strategy(NavigationStrategy.LINKS)
        assert engine.current_strategy == NavigationStrategy.LINKS

    def test_set_strategy_multiple_times(self):
        """Test changing strategy multiple times"""
        engine = DecisionEngine()

        strategies = [
            NavigationStrategy.LANDMARKS,
            NavigationStrategy.FORMS,
            NavigationStrategy.BUTTONS,
            NavigationStrategy.SEQUENTIAL_TAB
        ]

        for strategy in strategies:
            engine.set_strategy(strategy)
            assert engine.current_strategy == strategy


class TestActionCounting:
    """Tests for action counting methods"""

    def test_increment_actions(self):
        """Test incrementing action counter"""
        engine = DecisionEngine()

        assert engine.actions_taken == 0

        engine.increment_actions()
        assert engine.actions_taken == 1

        engine.increment_actions()
        assert engine.actions_taken == 2

    def test_increment_actions_multiple_times(self):
        """Test incrementing multiple times"""
        engine = DecisionEngine()

        for i in range(10):
            engine.increment_actions()

        assert engine.actions_taken == 10

    def test_has_reached_max_actions_false(self):
        """Test has_reached_max_actions returns False when under limit"""
        engine = DecisionEngine(max_actions=10)

        engine.actions_taken = 5
        assert engine.has_reached_max_actions() is False

        engine.actions_taken = 9
        assert engine.has_reached_max_actions() is False

    def test_has_reached_max_actions_true_at_limit(self):
        """Test has_reached_max_actions returns True at limit"""
        engine = DecisionEngine(max_actions=10)

        engine.actions_taken = 10
        assert engine.has_reached_max_actions() is True

    def test_has_reached_max_actions_true_over_limit(self):
        """Test has_reached_max_actions returns True over limit"""
        engine = DecisionEngine(max_actions=10)

        engine.actions_taken = 15
        assert engine.has_reached_max_actions() is True


class TestDecideNextAction:
    """Tests for decide_next_action method"""

    def test_circular_navigation_triggers_escape(self):
        """Test that circular navigation triggers ESCAPE action"""
        engine = DecisionEngine()
        engine.set_state(AgentState.EXPLORING)

        decision = engine.decide_next_action(is_circular=True)

        assert decision.action == NavigationAction.ESCAPE
        assert "circular navigation" in decision.reasoning.lower()
        assert decision.priority == 10
        assert engine.current_state == AgentState.STUCK

    def test_circular_navigation_only_triggers_once(self):
        """Test circular detection doesn't trigger again if already stuck"""
        engine = DecisionEngine()
        engine.set_state(AgentState.STUCK)
        engine.set_strategy(NavigationStrategy.SEQUENTIAL_TAB)

        decision = engine.decide_next_action(is_circular=True)

        # Should not return ESCAPE again, should use strategy
        assert decision.action == NavigationAction.TAB

    def test_max_actions_reached_triggers_completion(self):
        """Test that reaching max actions triggers completion"""
        engine = DecisionEngine(max_actions=5)
        engine.actions_taken = 5

        decision = engine.decide_next_action()

        assert decision.action == NavigationAction.ESCAPE
        assert "maximum action limit" in decision.reasoning.lower()
        assert decision.priority == 10
        assert engine.current_state == AgentState.COMPLETED

    def test_headings_first_strategy(self):
        """Test decision making with headings-first strategy"""
        engine = DecisionEngine(initial_strategy=NavigationStrategy.HEADINGS_FIRST)

        # When on a heading
        decision = engine.decide_next_action(nvda_output="Heading level 1 Main Page")

        assert decision.action == NavigationAction.NEXT_HEADING
        assert decision.strategy == NavigationStrategy.HEADINGS_FIRST
        assert "heading" in decision.reasoning.lower()

    def test_headings_first_switches_to_sequential(self):
        """Test headings-first switches to sequential when no headings"""
        engine = DecisionEngine(initial_strategy=NavigationStrategy.HEADINGS_FIRST)

        # When not on a heading
        decision = engine.decide_next_action(nvda_output="Some link text")

        assert decision.action == NavigationAction.TAB
        assert engine.current_strategy == NavigationStrategy.SEQUENTIAL_TAB
        assert "finished exploring headings" in decision.reasoning.lower()

    def test_sequential_tab_strategy(self):
        """Test decision making with sequential tab strategy"""
        engine = DecisionEngine(initial_strategy=NavigationStrategy.SEQUENTIAL_TAB)

        decision = engine.decide_next_action(nvda_output="Login button")

        assert decision.action == NavigationAction.TAB
        assert decision.strategy == NavigationStrategy.SEQUENTIAL_TAB

    def test_landmarks_strategy(self):
        """Test decision making with landmarks strategy"""
        engine = DecisionEngine(initial_strategy=NavigationStrategy.LANDMARKS)

        decision = engine.decide_next_action(nvda_output="Navigation landmark")

        assert decision.action == NavigationAction.NEXT_LANDMARK
        assert decision.strategy == NavigationStrategy.LANDMARKS

    def test_links_strategy(self):
        """Test decision making with links strategy"""
        engine = DecisionEngine(initial_strategy=NavigationStrategy.LINKS)

        decision = engine.decide_next_action(nvda_output="Home link")

        assert decision.action == NavigationAction.NEXT_LINK
        assert decision.strategy == NavigationStrategy.LINKS

    def test_forms_strategy(self):
        """Test decision making with forms strategy"""
        engine = DecisionEngine(initial_strategy=NavigationStrategy.FORMS)

        decision = engine.decide_next_action(nvda_output="Email edit")

        assert decision.action == NavigationAction.NEXT_FORM_FIELD
        assert decision.strategy == NavigationStrategy.FORMS

    def test_buttons_strategy(self):
        """Test decision making with buttons strategy"""
        engine = DecisionEngine(initial_strategy=NavigationStrategy.BUTTONS)

        decision = engine.decide_next_action(nvda_output="Submit button")

        assert decision.action == NavigationAction.NEXT_BUTTON
        assert decision.strategy == NavigationStrategy.BUTTONS

    def test_decision_with_no_nvda_output(self):
        """Test decision making with no NVDA output"""
        engine = DecisionEngine(initial_strategy=NavigationStrategy.SEQUENTIAL_TAB)

        decision = engine.decide_next_action(nvda_output=None)

        assert isinstance(decision, NavigationDecision)
        assert decision.action == NavigationAction.TAB

    def test_decision_with_empty_nvda_output(self):
        """Test decision making with empty NVDA output"""
        engine = DecisionEngine(initial_strategy=NavigationStrategy.SEQUENTIAL_TAB)

        decision = engine.decide_next_action(nvda_output="")

        assert isinstance(decision, NavigationDecision)
        assert decision.action == NavigationAction.TAB

    def test_has_visited_before_parameter(self):
        """Test has_visited_before parameter is passed to strategies"""
        engine = DecisionEngine(initial_strategy=NavigationStrategy.SEQUENTIAL_TAB)

        # Should still work with has_visited_before
        decision = engine.decide_next_action(
            nvda_output="Element",
            has_visited_before=True
        )

        assert isinstance(decision, NavigationDecision)


class TestStrategyTransitions:
    """Tests for strategy transition logic"""

    def test_strategy_preserved_across_decisions(self):
        """Test that strategy is preserved across multiple decisions"""
        engine = DecisionEngine(initial_strategy=NavigationStrategy.LINKS)

        decision1 = engine.decide_next_action(nvda_output="Link 1")
        decision2 = engine.decide_next_action(nvda_output="Link 2")
        decision3 = engine.decide_next_action(nvda_output="Link 3")

        assert decision1.strategy == NavigationStrategy.LINKS
        assert decision2.strategy == NavigationStrategy.LINKS
        assert decision3.strategy == NavigationStrategy.LINKS
        assert engine.current_strategy == NavigationStrategy.LINKS

    def test_manual_strategy_change_affects_decisions(self):
        """Test that manually changing strategy affects future decisions"""
        engine = DecisionEngine(initial_strategy=NavigationStrategy.HEADINGS_FIRST)

        decision1 = engine.decide_next_action(nvda_output="Heading level 1")
        assert decision1.action == NavigationAction.NEXT_HEADING

        # Manually change strategy
        engine.set_strategy(NavigationStrategy.BUTTONS)

        decision2 = engine.decide_next_action(nvda_output="Submit button")
        assert decision2.action == NavigationAction.NEXT_BUTTON
        assert decision2.strategy == NavigationStrategy.BUTTONS


class TestIntegrationScenarios:
    """Integration tests for realistic scenarios"""

    def test_complete_exploration_workflow(self):
        """Test a complete exploration workflow"""
        engine = DecisionEngine(max_actions=10)

        # Start exploring
        engine.set_state(AgentState.EXPLORING)

        # Take several actions
        for i in range(5):
            decision = engine.decide_next_action(nvda_output=f"Element {i}")
            assert isinstance(decision, NavigationDecision)
            engine.increment_actions()

        assert engine.actions_taken == 5
        assert engine.current_state == AgentState.EXPLORING

        # Continue until max
        for i in range(5):
            decision = engine.decide_next_action(nvda_output=f"Element {i}")
            engine.increment_actions()

        # Next decision should trigger completion
        decision = engine.decide_next_action()
        assert decision.action == NavigationAction.ESCAPE
        assert engine.current_state == AgentState.COMPLETED

    def test_stuck_recovery_attempt(self):
        """Test stuck detection and recovery"""
        engine = DecisionEngine()
        engine.set_state(AgentState.EXPLORING)

        # Trigger stuck state
        decision = engine.decide_next_action(is_circular=True)
        assert engine.current_state == AgentState.STUCK
        assert decision.action == NavigationAction.ESCAPE

        # After escape, continue navigation
        engine.set_state(AgentState.EXPLORING)
        decision = engine.decide_next_action(is_circular=False)
        assert isinstance(decision, NavigationDecision)

    def test_strategy_progression(self):
        """Test progressing through different strategies"""
        engine = DecisionEngine(initial_strategy=NavigationStrategy.HEADINGS_FIRST)

        # Start with headings
        decision1 = engine.decide_next_action(nvda_output="Heading level 1")
        assert decision1.action == NavigationAction.NEXT_HEADING

        # No more headings, should switch
        decision2 = engine.decide_next_action(nvda_output="Some link")
        assert engine.current_strategy == NavigationStrategy.SEQUENTIAL_TAB
        assert decision2.action == NavigationAction.TAB

        # Manually switch to links
        engine.set_strategy(NavigationStrategy.LINKS)
        decision3 = engine.decide_next_action(nvda_output="Another link")
        assert decision3.action == NavigationAction.NEXT_LINK
