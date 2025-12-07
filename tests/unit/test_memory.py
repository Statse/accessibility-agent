"""Tests for agent memory module."""

import pytest
from datetime import datetime, timedelta
from src.agent.memory import VisitedElement, AgentMemory


class TestVisitedElement:
    """Tests for VisitedElement model"""

    def test_create_basic_element(self):
        """Test creating a basic visited element"""
        element = VisitedElement(
            nvda_text="Login button",
            key_used="Tab",
            element_id="btn_login_1"
        )

        assert element.nvda_text == "Login button"
        assert element.key_used == "Tab"
        assert element.element_id == "btn_login_1"
        assert element.context is None
        assert element.is_interactive is False
        assert isinstance(element.timestamp, datetime)

    def test_create_element_with_all_fields(self):
        """Test creating element with all fields populated"""
        element = VisitedElement(
            nvda_text="Submit button",
            key_used="B",
            element_id="btn_submit_1",
            context="Form submission",
            is_interactive=True
        )

        assert element.nvda_text == "Submit button"
        assert element.key_used == "B"
        assert element.element_id == "btn_submit_1"
        assert element.context == "Form submission"
        assert element.is_interactive is True

    def test_timestamp_auto_generated(self):
        """Test that timestamp is automatically generated"""
        before = datetime.now()
        element = VisitedElement(
            nvda_text="Link",
            key_used="K",
            element_id="link_1"
        )
        after = datetime.now()

        assert before <= element.timestamp <= after

    def test_element_serialization(self):
        """Test JSON serialization"""
        element = VisitedElement(
            nvda_text="Heading level 1 Main Page",
            key_used="H",
            element_id="h1_main",
            is_interactive=False
        )

        data = element.model_dump()
        assert data["nvda_text"] == "Heading level 1 Main Page"
        assert data["key_used"] == "H"
        assert data["element_id"] == "h1_main"


class TestAgentMemoryInitialization:
    """Tests for AgentMemory initialization"""

    def test_create_default_memory(self):
        """Test creating memory with default settings"""
        memory = AgentMemory()

        assert memory.max_history == 1000
        assert memory.count_visits() == 0

    def test_create_memory_with_custom_max_history(self):
        """Test creating memory with custom max_history"""
        memory = AgentMemory(max_history=50)

        assert memory.max_history == 50
        assert memory.count_visits() == 0

    def test_create_memory_with_min_max_history(self):
        """Test creating memory with minimum valid max_history"""
        memory = AgentMemory(max_history=1)

        assert memory.max_history == 1

    def test_create_memory_with_invalid_max_history(self):
        """Test that invalid max_history raises ValueError"""
        with pytest.raises(ValueError, match="max_history must be >= 1"):
            AgentMemory(max_history=0)

        with pytest.raises(ValueError, match="max_history must be >= 1"):
            AgentMemory(max_history=-5)


class TestAddElement:
    """Tests for add_element method"""

    def test_add_basic_element(self):
        """Test adding a basic element"""
        memory = AgentMemory()

        element = memory.add_element(
            nvda_text="Home link",
            key_used="K",
            element_id="link_home"
        )

        assert element.nvda_text == "Home link"
        assert element.key_used == "K"
        assert element.element_id == "link_home"
        assert memory.count_visits() == 1

    def test_add_element_with_all_parameters(self):
        """Test adding element with all parameters"""
        memory = AgentMemory()

        element = memory.add_element(
            nvda_text="Email edit",
            key_used="F",
            element_id="input_email",
            context="Login form",
            is_interactive=True
        )

        assert element.nvda_text == "Email edit"
        assert element.key_used == "F"
        assert element.element_id == "input_email"
        assert element.context == "Login form"
        assert element.is_interactive is True
        assert memory.count_visits() == 1

    def test_add_multiple_elements(self):
        """Test adding multiple elements"""
        memory = AgentMemory()

        memory.add_element("Element 1", "Tab", "elem_1")
        memory.add_element("Element 2", "Tab", "elem_2")
        memory.add_element("Element 3", "Tab", "elem_3")

        assert memory.count_visits() == 3

    def test_add_duplicate_element_id(self):
        """Test adding same element ID multiple times"""
        memory = AgentMemory()

        memory.add_element("Button", "B", "btn_1")
        memory.add_element("Same button", "B", "btn_1")

        assert memory.count_visits() == 2
        assert memory.has_visited("btn_1")


class TestHasVisited:
    """Tests for has_visited method"""

    def test_has_visited_returns_true_for_existing_element(self):
        """Test that has_visited returns True for visited elements"""
        memory = AgentMemory()
        memory.add_element("Link", "K", "link_1")

        assert memory.has_visited("link_1") is True

    def test_has_visited_returns_false_for_new_element(self):
        """Test that has_visited returns False for unvisited elements"""
        memory = AgentMemory()
        memory.add_element("Link", "K", "link_1")

        assert memory.has_visited("link_2") is False

    def test_has_visited_empty_memory(self):
        """Test has_visited on empty memory"""
        memory = AgentMemory()

        assert memory.has_visited("any_id") is False

    def test_has_visited_after_multiple_adds(self):
        """Test has_visited with multiple elements"""
        memory = AgentMemory()

        memory.add_element("Element 1", "Tab", "elem_1")
        memory.add_element("Element 2", "Tab", "elem_2")
        memory.add_element("Element 3", "Tab", "elem_3")

        assert memory.has_visited("elem_1") is True
        assert memory.has_visited("elem_2") is True
        assert memory.has_visited("elem_3") is True
        assert memory.has_visited("elem_4") is False


class TestGetRecentElements:
    """Tests for get_recent_elements method"""

    def test_get_recent_elements_empty_memory(self):
        """Test getting recent elements from empty memory"""
        memory = AgentMemory()

        recent = memory.get_recent_elements(5)

        assert recent == []

    def test_get_recent_elements_less_than_count(self):
        """Test getting recent when fewer elements than requested"""
        memory = AgentMemory()

        memory.add_element("Element 1", "Tab", "elem_1")
        memory.add_element("Element 2", "Tab", "elem_2")

        recent = memory.get_recent_elements(5)

        assert len(recent) == 2
        assert recent[0].element_id == "elem_2"  # Newest first
        assert recent[1].element_id == "elem_1"

    def test_get_recent_elements_exact_count(self):
        """Test getting exact number of recent elements"""
        memory = AgentMemory()

        for i in range(5):
            memory.add_element(f"Element {i}", "Tab", f"elem_{i}")

        recent = memory.get_recent_elements(5)

        assert len(recent) == 5
        assert recent[0].element_id == "elem_4"  # Newest first
        assert recent[4].element_id == "elem_0"  # Oldest last

    def test_get_recent_elements_more_than_count(self):
        """Test getting recent when more elements exist"""
        memory = AgentMemory()

        for i in range(10):
            memory.add_element(f"Element {i}", "Tab", f"elem_{i}")

        recent = memory.get_recent_elements(3)

        assert len(recent) == 3
        assert recent[0].element_id == "elem_9"
        assert recent[1].element_id == "elem_8"
        assert recent[2].element_id == "elem_7"

    def test_get_recent_elements_default_count(self):
        """Test default count of 10"""
        memory = AgentMemory()

        for i in range(15):
            memory.add_element(f"Element {i}", "Tab", f"elem_{i}")

        recent = memory.get_recent_elements()

        assert len(recent) == 10


class TestGetAllElements:
    """Tests for get_all_elements method"""

    def test_get_all_elements_empty(self):
        """Test getting all elements from empty memory"""
        memory = AgentMemory()

        all_elements = memory.get_all_elements()

        assert all_elements == []

    def test_get_all_elements_returns_copy(self):
        """Test that get_all_elements returns a copy"""
        memory = AgentMemory()
        memory.add_element("Element", "Tab", "elem_1")

        all_elements = memory.get_all_elements()
        all_elements.clear()

        assert memory.count_visits() == 1  # Original unchanged

    def test_get_all_elements_chronological_order(self):
        """Test that elements are in chronological order"""
        memory = AgentMemory()

        for i in range(5):
            memory.add_element(f"Element {i}", "Tab", f"elem_{i}")

        all_elements = memory.get_all_elements()

        assert len(all_elements) == 5
        assert all_elements[0].element_id == "elem_0"  # Oldest first
        assert all_elements[4].element_id == "elem_4"  # Newest last


class TestGetInteractiveElements:
    """Tests for get_interactive_elements method"""

    def test_get_interactive_elements_empty(self):
        """Test getting interactive elements from empty memory"""
        memory = AgentMemory()

        interactive = memory.get_interactive_elements()

        assert interactive == []

    def test_get_interactive_elements_none_interactive(self):
        """Test when no elements are interactive"""
        memory = AgentMemory()

        memory.add_element("Heading", "H", "h1_1", is_interactive=False)
        memory.add_element("Paragraph", "Down", "p_1", is_interactive=False)

        interactive = memory.get_interactive_elements()

        assert interactive == []

    def test_get_interactive_elements_all_interactive(self):
        """Test when all elements are interactive"""
        memory = AgentMemory()

        memory.add_element("Button", "B", "btn_1", is_interactive=True)
        memory.add_element("Link", "K", "link_1", is_interactive=True)

        interactive = memory.get_interactive_elements()

        assert len(interactive) == 2

    def test_get_interactive_elements_mixed(self):
        """Test filtering interactive from non-interactive"""
        memory = AgentMemory()

        memory.add_element("Heading", "H", "h1_1", is_interactive=False)
        memory.add_element("Button", "B", "btn_1", is_interactive=True)
        memory.add_element("Paragraph", "Down", "p_1", is_interactive=False)
        memory.add_element("Link", "K", "link_1", is_interactive=True)

        interactive = memory.get_interactive_elements()

        assert len(interactive) == 2
        assert interactive[0].element_id == "btn_1"
        assert interactive[1].element_id == "link_1"


class TestCountVisits:
    """Tests for count_visits method"""

    def test_count_visits_empty(self):
        """Test count on empty memory"""
        memory = AgentMemory()

        assert memory.count_visits() == 0

    def test_count_visits_after_adds(self):
        """Test count increases with additions"""
        memory = AgentMemory()

        assert memory.count_visits() == 0

        memory.add_element("Element 1", "Tab", "elem_1")
        assert memory.count_visits() == 1

        memory.add_element("Element 2", "Tab", "elem_2")
        assert memory.count_visits() == 2

    def test_count_visits_with_duplicates(self):
        """Test count includes duplicate element IDs"""
        memory = AgentMemory()

        memory.add_element("Button", "B", "btn_1")
        memory.add_element("Same button again", "B", "btn_1")

        assert memory.count_visits() == 2


class TestClear:
    """Tests for clear method"""

    def test_clear_empty_memory(self):
        """Test clearing already empty memory"""
        memory = AgentMemory()

        memory.clear()

        assert memory.count_visits() == 0

    def test_clear_removes_all_elements(self):
        """Test clearing removes all visited elements"""
        memory = AgentMemory()

        for i in range(10):
            memory.add_element(f"Element {i}", "Tab", f"elem_{i}")

        assert memory.count_visits() == 10

        memory.clear()

        assert memory.count_visits() == 0
        assert memory.get_all_elements() == []

    def test_clear_removes_from_has_visited(self):
        """Test clearing resets has_visited checks"""
        memory = AgentMemory()

        memory.add_element("Element", "Tab", "elem_1")
        assert memory.has_visited("elem_1") is True

        memory.clear()

        assert memory.has_visited("elem_1") is False

    def test_clear_allows_reuse(self):
        """Test memory can be reused after clearing"""
        memory = AgentMemory()

        memory.add_element("Element 1", "Tab", "elem_1")
        memory.clear()
        memory.add_element("Element 2", "Tab", "elem_2")

        assert memory.count_visits() == 1
        assert memory.has_visited("elem_2") is True
        assert memory.has_visited("elem_1") is False


class TestDetectCircularNavigation:
    """Tests for detect_circular_navigation method"""

    def test_detect_circular_empty_memory(self):
        """Test circular detection on empty memory"""
        memory = AgentMemory()

        assert memory.detect_circular_navigation() is False

    def test_detect_circular_insufficient_history(self):
        """Test when history is less than window size"""
        memory = AgentMemory()

        memory.add_element("Element", "Tab", "elem_1")
        memory.add_element("Element", "Tab", "elem_2")

        assert memory.detect_circular_navigation(window_size=5) is False

    def test_detect_circular_all_same_element(self):
        """Test detection when stuck on same element"""
        memory = AgentMemory()

        for i in range(5):
            memory.add_element("Same element", "Tab", "elem_stuck")

        assert memory.detect_circular_navigation(window_size=5) is True

    def test_detect_circular_majority_same_element(self):
        """Test detection when >50% are same element"""
        memory = AgentMemory()

        memory.add_element("Element A", "Tab", "elem_a")
        memory.add_element("Element B", "Tab", "elem_b")
        memory.add_element("Element B", "Tab", "elem_b")
        memory.add_element("Element B", "Tab", "elem_b")
        memory.add_element("Element B", "Tab", "elem_b")

        # 4 out of 5 are elem_b (80%)
        assert memory.detect_circular_navigation(window_size=5) is True

    def test_detect_circular_exactly_50_percent(self):
        """Test when exactly 50% are same (should not trigger)"""
        memory = AgentMemory()

        memory.add_element("Element A", "Tab", "elem_a")
        memory.add_element("Element A", "Tab", "elem_a")
        memory.add_element("Element B", "Tab", "elem_b")
        memory.add_element("Element B", "Tab", "elem_b")

        # 2 out of 4 are same (50%), needs >50%
        assert memory.detect_circular_navigation(window_size=4) is False

    def test_detect_circular_diverse_elements(self):
        """Test when elements are diverse (no circular)"""
        memory = AgentMemory()

        for i in range(5):
            memory.add_element(f"Element {i}", "Tab", f"elem_{i}")

        assert memory.detect_circular_navigation(window_size=5) is False

    def test_detect_circular_custom_window_size(self):
        """Test with different window sizes"""
        memory = AgentMemory()

        # Add pattern: A, A, A, B, C
        # Recent 3 elements (newest first): C, B, A - diverse, no circular
        # Recent 5 elements: C, B, A, A, A - 3/5 A's (60%) = circular
        memory.add_element("A", "Tab", "a")
        memory.add_element("A", "Tab", "a")
        memory.add_element("A", "Tab", "a")
        memory.add_element("B", "Tab", "b")
        memory.add_element("C", "Tab", "c")

        # Window of 3 (most recent: C, B, A): diverse, no circular
        assert memory.detect_circular_navigation(window_size=3) is False

        # Window of 5 (all elements, newest first: C, B, A, A, A): 3/5 A's (60%) = circular
        assert memory.detect_circular_navigation(window_size=5) is True


class TestGetNavigationSummary:
    """Tests for get_navigation_summary method"""

    def test_navigation_summary_empty(self):
        """Test summary on empty memory"""
        memory = AgentMemory()

        summary = memory.get_navigation_summary()

        assert summary["total_elements"] == 0
        assert summary["interactive_elements"] == 0
        assert summary["unique_elements"] == 0
        assert summary["repeat_rate"] == 0.0

    def test_navigation_summary_all_unique(self):
        """Test summary when all elements are unique"""
        memory = AgentMemory()

        for i in range(5):
            memory.add_element(f"Element {i}", "Tab", f"elem_{i}")

        summary = memory.get_navigation_summary()

        assert summary["total_elements"] == 5
        assert summary["interactive_elements"] == 0
        assert summary["unique_elements"] == 5
        assert summary["repeat_rate"] == 0.0

    def test_navigation_summary_with_repeats(self):
        """Test summary with repeated elements"""
        memory = AgentMemory()

        memory.add_element("Button", "B", "btn_1", is_interactive=True)
        memory.add_element("Link", "K", "link_1", is_interactive=True)
        memory.add_element("Button", "B", "btn_1", is_interactive=True)  # Repeat
        memory.add_element("Heading", "H", "h1_1")
        memory.add_element("Button", "B", "btn_1", is_interactive=True)  # Repeat

        summary = memory.get_navigation_summary()

        assert summary["total_elements"] == 5
        assert summary["interactive_elements"] == 4  # 3 btn_1 visits + 1 link_1 visit (counts all visits)
        assert summary["unique_elements"] == 3  # btn_1, link_1, h1_1
        assert summary["repeat_rate"] == 40.0  # (5 - 3) / 5 * 100 = 40%

    def test_navigation_summary_all_interactive(self):
        """Test summary when all elements are interactive"""
        memory = AgentMemory()

        memory.add_element("Button 1", "B", "btn_1", is_interactive=True)
        memory.add_element("Link 1", "K", "link_1", is_interactive=True)
        memory.add_element("Button 2", "B", "btn_2", is_interactive=True)

        summary = memory.get_navigation_summary()

        assert summary["total_elements"] == 3
        assert summary["interactive_elements"] == 3

    def test_navigation_summary_high_repeat_rate(self):
        """Test summary with high repeat rate"""
        memory = AgentMemory()

        # Add same element 5 times
        for i in range(5):
            memory.add_element("Same element", "Tab", "stuck")

        summary = memory.get_navigation_summary()

        assert summary["total_elements"] == 5
        assert summary["unique_elements"] == 1
        assert summary["repeat_rate"] == 80.0  # (5 - 1) / 5 * 100


class TestBufferOverflow:
    """Tests for buffer overflow behavior"""

    def test_buffer_respects_max_history(self):
        """Test that buffer doesn't exceed max_history"""
        memory = AgentMemory(max_history=3)

        for i in range(10):
            memory.add_element(f"Element {i}", "Tab", f"elem_{i}")

        assert memory.count_visits() == 3

    def test_buffer_fifo_behavior(self):
        """Test that oldest elements are removed first"""
        memory = AgentMemory(max_history=3)

        memory.add_element("Element 0", "Tab", "elem_0")
        memory.add_element("Element 1", "Tab", "elem_1")
        memory.add_element("Element 2", "Tab", "elem_2")
        memory.add_element("Element 3", "Tab", "elem_3")  # Should remove elem_0

        all_elements = memory.get_all_elements()

        assert len(all_elements) == 3
        assert all_elements[0].element_id == "elem_1"
        assert all_elements[1].element_id == "elem_2"
        assert all_elements[2].element_id == "elem_3"

    def test_buffer_overflow_preserves_has_visited(self):
        """Test that has_visited still works after overflow"""
        memory = AgentMemory(max_history=3)

        for i in range(5):
            memory.add_element(f"Element {i}", "Tab", f"elem_{i}")

        # elem_0 and elem_1 should be gone from deque
        # but still in _element_ids_seen
        assert memory.has_visited("elem_0") is True
        assert memory.has_visited("elem_1") is True
        assert memory.has_visited("elem_2") is True
        assert memory.has_visited("elem_3") is True
        assert memory.has_visited("elem_4") is True

    def test_buffer_overflow_navigation_summary(self):
        """Test navigation summary after overflow"""
        memory = AgentMemory(max_history=3)

        for i in range(5):
            memory.add_element(f"Element {i}", "Tab", f"elem_{i}", is_interactive=True)

        summary = memory.get_navigation_summary()

        assert summary["total_elements"] == 3  # Only 3 in buffer
        assert summary["unique_elements"] == 5  # All tracked in set
        assert summary["interactive_elements"] == 3  # Only 3 in buffer
