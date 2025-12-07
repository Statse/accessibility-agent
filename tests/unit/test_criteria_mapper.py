"""Tests for WCAG criteria mapper module."""

import pytest
from src.wcag.criteria_mapper import (
    WCAGLevel,
    WCAGVersion,
    IssueSeverity,
    WCAGCriterion,
    get_criterion,
    get_criteria_by_level,
    get_criteria_by_principle,
    get_testable_criteria,
    get_severity_for_criterion,
    ALL_CRITERIA,
    CRITERION_1_1_1,
    CRITERION_2_1_2,
    CRITERION_4_1_2,
)


class TestEnums:
    """Tests for enum definitions"""

    def test_wcag_level_values(self):
        """Test WCAG Level enum values"""
        assert WCAGLevel.A == "A"
        assert WCAGLevel.AA == "AA"
        assert WCAGLevel.AAA == "AAA"

    def test_wcag_version_values(self):
        """Test WCAG Version enum values"""
        assert WCAGVersion.WCAG_2_0 == "2.0"
        assert WCAGVersion.WCAG_2_1 == "2.1"
        assert WCAGVersion.WCAG_2_2 == "2.2"

    def test_issue_severity_values(self):
        """Test IssueSeverity enum values"""
        assert IssueSeverity.CRITICAL == "critical"
        assert IssueSeverity.HIGH == "high"
        assert IssueSeverity.MEDIUM == "medium"
        assert IssueSeverity.LOW == "low"


class TestWCAGCriterion:
    """Tests for WCAGCriterion model"""

    def test_create_criterion(self):
        """Test creating a WCAG criterion"""
        criterion = WCAGCriterion(
            criterion_id="1.1.1",
            name="Non-text Content",
            level=WCAGLevel.A,
            version=WCAGVersion.WCAG_2_0,
            guideline="1.1",
            principle="Perceivable",
            description="All non-text content has a text alternative",
            detection_method="NVDA announces 'unlabeled graphic'"
        )

        assert criterion.criterion_id == "1.1.1"
        assert criterion.name == "Non-text Content"
        assert criterion.level == WCAGLevel.A
        assert criterion.version == WCAGVersion.WCAG_2_0
        assert criterion.guideline == "1.1"
        assert criterion.principle == "Perceivable"

    def test_criterion_is_frozen(self):
        """Test that WCAGCriterion instances are immutable"""
        criterion = CRITERION_1_1_1

        with pytest.raises((ValueError, AttributeError)):
            criterion.name = "Different Name"

    def test_get_full_name(self):
        """Test get_full_name method"""
        criterion = CRITERION_1_1_1

        full_name = criterion.get_full_name()

        assert "1.1.1" in full_name
        assert "Non-text Content" in full_name
        assert "Level A" in full_name


class TestPredefinedCriteria:
    """Tests for predefined WCAG criteria"""

    def test_criterion_1_1_1_exists(self):
        """Test 1.1.1 Non-text Content criterion"""
        assert CRITERION_1_1_1.criterion_id == "1.1.1"
        assert CRITERION_1_1_1.name == "Non-text Content"
        assert CRITERION_1_1_1.level == WCAGLevel.A
        assert CRITERION_1_1_1.principle == "Perceivable"

    def test_criterion_2_1_2_exists(self):
        """Test 2.1.2 No Keyboard Trap criterion"""
        assert CRITERION_2_1_2.criterion_id == "2.1.2"
        assert CRITERION_2_1_2.name == "No Keyboard Trap"
        assert CRITERION_2_1_2.level == WCAGLevel.A
        assert CRITERION_2_1_2.principle == "Operable"

    def test_criterion_4_1_2_exists(self):
        """Test 4.1.2 Name, Role, Value criterion"""
        assert CRITERION_4_1_2.criterion_id == "4.1.2"
        assert CRITERION_4_1_2.name == "Name, Role, Value"
        assert CRITERION_4_1_2.level == WCAGLevel.A
        assert CRITERION_4_1_2.principle == "Robust"

    def test_all_criteria_registry_populated(self):
        """Test that ALL_CRITERIA registry is populated"""
        assert len(ALL_CRITERIA) > 0
        assert "1.1.1" in ALL_CRITERIA
        assert "2.1.2" in ALL_CRITERIA
        assert "4.1.2" in ALL_CRITERIA

    def test_all_criteria_contains_expected_count(self):
        """Test that we have expected number of criteria"""
        # Should have at least 15 criteria as documented
        assert len(ALL_CRITERIA) >= 15


class TestGetCriterion:
    """Tests for get_criterion function"""

    def test_get_existing_criterion(self):
        """Test getting an existing criterion"""
        criterion = get_criterion("1.1.1")

        assert criterion is not None
        assert criterion.criterion_id == "1.1.1"
        assert criterion.name == "Non-text Content"

    def test_get_another_criterion(self):
        """Test getting another criterion"""
        criterion = get_criterion("2.1.2")

        assert criterion is not None
        assert criterion.criterion_id == "2.1.2"
        assert criterion.name == "No Keyboard Trap"

    def test_get_nonexistent_criterion(self):
        """Test getting a non-existent criterion returns None"""
        criterion = get_criterion("99.99.99")

        assert criterion is None

    def test_get_criterion_returns_same_instance(self):
        """Test that get_criterion returns reference from registry"""
        criterion1 = get_criterion("1.1.1")
        criterion2 = get_criterion("1.1.1")

        assert criterion1 is criterion2


class TestGetCriteriaByLevel:
    """Tests for get_criteria_by_level function"""

    def test_get_level_a_criteria(self):
        """Test getting all Level A criteria"""
        criteria = get_criteria_by_level(WCAGLevel.A)

        assert len(criteria) > 0
        assert all(c.level == WCAGLevel.A for c in criteria)

    def test_get_level_aa_criteria(self):
        """Test getting all Level AA criteria"""
        criteria = get_criteria_by_level(WCAGLevel.AA)

        assert len(criteria) > 0
        assert all(c.level == WCAGLevel.AA for c in criteria)

    def test_get_level_aaa_criteria(self):
        """Test getting all Level AAA criteria"""
        criteria = get_criteria_by_level(WCAGLevel.AAA)

        # May be empty if no AAA criteria defined
        assert isinstance(criteria, list)
        if criteria:
            assert all(c.level == WCAGLevel.AAA for c in criteria)

    def test_level_a_contains_1_1_1(self):
        """Test Level A includes 1.1.1"""
        criteria = get_criteria_by_level(WCAGLevel.A)
        criterion_ids = [c.criterion_id for c in criteria]

        assert "1.1.1" in criterion_ids

    def test_level_a_contains_2_1_2(self):
        """Test Level A includes 2.1.2"""
        criteria = get_criteria_by_level(WCAGLevel.A)
        criterion_ids = [c.criterion_id for c in criteria]

        assert "2.1.2" in criterion_ids


class TestGetCriteriaByPrinciple:
    """Tests for get_criteria_by_principle function"""

    def test_get_perceivable_criteria(self):
        """Test getting Perceivable criteria"""
        criteria = get_criteria_by_principle("Perceivable")

        assert len(criteria) > 0
        assert all(c.principle == "Perceivable" for c in criteria)

    def test_get_operable_criteria(self):
        """Test getting Operable criteria"""
        criteria = get_criteria_by_principle("Operable")

        assert len(criteria) > 0
        assert all(c.principle == "Operable" for c in criteria)

    def test_get_understandable_criteria(self):
        """Test getting Understandable criteria"""
        criteria = get_criteria_by_principle("Understandable")

        assert len(criteria) > 0
        assert all(c.principle == "Understandable" for c in criteria)

    def test_get_robust_criteria(self):
        """Test getting Robust criteria"""
        criteria = get_criteria_by_principle("Robust")

        assert len(criteria) > 0
        assert all(c.principle == "Robust" for c in criteria)

    def test_perceivable_contains_1_1_1(self):
        """Test Perceivable includes 1.1.1"""
        criteria = get_criteria_by_principle("Perceivable")
        criterion_ids = [c.criterion_id for c in criteria]

        assert "1.1.1" in criterion_ids

    def test_operable_contains_2_1_2(self):
        """Test Operable includes 2.1.2"""
        criteria = get_criteria_by_principle("Operable")
        criterion_ids = [c.criterion_id for c in criteria]

        assert "2.1.2" in criterion_ids


class TestGetTestableCriteria:
    """Tests for get_testable_criteria function"""

    def test_get_testable_criteria_returns_list(self):
        """Test that get_testable_criteria returns a list"""
        criteria = get_testable_criteria()

        assert isinstance(criteria, list)
        assert len(criteria) > 0

    def test_testable_criteria_excludes_visual_only(self):
        """Test that visual-only criteria are excluded"""
        criteria = get_testable_criteria()
        criterion_ids = [c.criterion_id for c in criteria]

        # These require visual verification and should be excluded
        assert "1.4.3" not in criterion_ids  # Contrast
        assert "2.4.7" not in criterion_ids  # Focus Visible

    def test_testable_criteria_includes_screen_reader_testable(self):
        """Test that screen reader testable criteria are included"""
        criteria = get_testable_criteria()
        criterion_ids = [c.criterion_id for c in criteria]

        # These can be tested with screen reader
        assert "1.1.1" in criterion_ids  # Non-text Content
        assert "2.1.2" in criterion_ids  # No Keyboard Trap
        assert "3.3.2" in criterion_ids  # Labels or Instructions
        assert "4.1.2" in criterion_ids  # Name, Role, Value

    def test_testable_criteria_count(self):
        """Test that we have expected number of testable criteria"""
        criteria = get_testable_criteria()

        # Should have at least 11 testable criteria (15 total - 4 visual-only)
        assert len(criteria) >= 11


class TestGetSeverityForCriterion:
    """Tests for get_severity_for_criterion function"""

    def test_keyboard_trap_is_critical(self):
        """Test 2.1.2 (keyboard trap) is CRITICAL"""
        severity = get_severity_for_criterion("2.1.2")

        assert severity == IssueSeverity.CRITICAL

    def test_missing_alt_text_is_high(self):
        """Test 1.1.1 (missing alt text) is HIGH"""
        severity = get_severity_for_criterion("1.1.1")

        assert severity == IssueSeverity.HIGH

    def test_keyboard_accessibility_is_high(self):
        """Test 2.1.1 (keyboard) is HIGH"""
        severity = get_severity_for_criterion("2.1.1")

        assert severity == IssueSeverity.HIGH

    def test_form_labels_is_high(self):
        """Test 3.3.2 (form labels) is HIGH"""
        severity = get_severity_for_criterion("3.3.2")

        assert severity == IssueSeverity.HIGH

    def test_name_role_value_is_high(self):
        """Test 4.1.2 (name/role/value) is HIGH"""
        severity = get_severity_for_criterion("4.1.2")

        assert severity == IssueSeverity.HIGH

    def test_link_purpose_is_medium(self):
        """Test 2.4.4 (link purpose) is MEDIUM"""
        severity = get_severity_for_criterion("2.4.4")

        assert severity == IssueSeverity.MEDIUM

    def test_headings_labels_is_medium(self):
        """Test 2.4.6 (headings and labels) is MEDIUM"""
        severity = get_severity_for_criterion("2.4.6")

        assert severity == IssueSeverity.MEDIUM

    def test_bypass_blocks_is_medium(self):
        """Test 2.4.1 (bypass blocks) is MEDIUM"""
        severity = get_severity_for_criterion("2.4.1")

        assert severity == IssueSeverity.MEDIUM

    def test_unknown_criterion_defaults_to_low(self):
        """Test unknown criterion defaults to LOW severity"""
        severity = get_severity_for_criterion("99.99.99")

        assert severity == IssueSeverity.LOW


class TestCriteriaIntegrity:
    """Tests for overall criteria registry integrity"""

    def test_all_criteria_have_unique_ids(self):
        """Test that all criteria have unique IDs"""
        ids = list(ALL_CRITERIA.keys())

        assert len(ids) == len(set(ids))

    def test_all_criteria_values_match_keys(self):
        """Test that criterion objects match their registry keys"""
        for criterion_id, criterion in ALL_CRITERIA.items():
            assert criterion.criterion_id == criterion_id

    def test_all_criteria_have_required_fields(self):
        """Test that all criteria have all required fields"""
        for criterion in ALL_CRITERIA.values():
            assert criterion.criterion_id
            assert criterion.name
            assert criterion.level
            assert criterion.version
            assert criterion.guideline
            assert criterion.principle
            assert criterion.description
            assert criterion.detection_method

    def test_all_principles_are_valid(self):
        """Test that all criteria have valid principles"""
        valid_principles = {"Perceivable", "Operable", "Understandable", "Robust"}

        for criterion in ALL_CRITERIA.values():
            assert criterion.principle in valid_principles

    def test_all_levels_are_valid(self):
        """Test that all criteria have valid levels"""
        valid_levels = {WCAGLevel.A, WCAGLevel.AA, WCAGLevel.AAA}

        for criterion in ALL_CRITERIA.values():
            assert criterion.level in valid_levels

    def test_criterion_ids_follow_pattern(self):
        """Test that criterion IDs follow X.Y.Z pattern"""
        import re

        pattern = re.compile(r'^\d+\.\d+\.\d+$')

        for criterion_id in ALL_CRITERIA.keys():
            assert pattern.match(criterion_id), f"Invalid ID format: {criterion_id}"

    def test_guidelines_match_criteria(self):
        """Test that guideline numbers match first two parts of criterion ID"""
        for criterion in ALL_CRITERIA.values():
            # Guideline should be first two parts of criterion_id
            expected_guideline = ".".join(criterion.criterion_id.split(".")[:2])
            assert criterion.guideline == expected_guideline


class TestCriteriaByVersion:
    """Tests for criteria by WCAG version"""

    def test_wcag_2_0_criteria_exist(self):
        """Test that WCAG 2.0 criteria exist"""
        wcag_2_0_criteria = [
            c for c in ALL_CRITERIA.values() if c.version == WCAGVersion.WCAG_2_0
        ]

        assert len(wcag_2_0_criteria) > 0

    def test_wcag_2_1_criteria_exist(self):
        """Test that WCAG 2.1 criteria exist"""
        wcag_2_1_criteria = [
            c for c in ALL_CRITERIA.values() if c.version == WCAGVersion.WCAG_2_1
        ]

        # May or may not have 2.1-specific criteria
        assert isinstance(wcag_2_1_criteria, list)

    def test_criterion_versions_are_valid(self):
        """Test that all criteria have valid versions"""
        valid_versions = {WCAGVersion.WCAG_2_0, WCAGVersion.WCAG_2_1, WCAGVersion.WCAG_2_2}

        for criterion in ALL_CRITERIA.values():
            assert criterion.version in valid_versions
