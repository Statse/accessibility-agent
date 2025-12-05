"""Pytest configuration and shared fixtures."""

import os
import sys
from pathlib import Path

import pytest

# Add src to path for imports
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))


@pytest.fixture
def project_root() -> Path:
    """Return the project root directory."""
    return PROJECT_ROOT


@pytest.fixture
def test_data_dir(project_root: Path) -> Path:
    """Return the test data directory."""
    return project_root / "tests" / "fixtures"


@pytest.fixture
def temp_config_file(tmp_path: Path) -> Path:
    """Create a temporary config file for testing."""
    config_file = tmp_path / "test_settings.yaml"
    config_file.write_text(
        """
nvda:
  log_path: "test.log"
  speech_viewer: true
  log_level: "debug"

browser:
  default: "auto"
  headless: false

keyboard:
  delay_between_keys: 0.05
  nvda_response_timeout: 1.0

agent:
  model: "openai:gpt-4"
  max_actions: 50

wcag:
  version: "2.1"
  conformance_levels: ["A", "AA"]

reporting:
  output_dir: "./test_reports"

logging:
  level: "DEBUG"
  format: "json"
"""
    )
    return config_file


@pytest.fixture
def mock_env_vars(monkeypatch: pytest.MonkeyPatch) -> None:
    """Set up mock environment variables for testing."""
    monkeypatch.setenv("OPENAI_API_KEY", "test-api-key-12345")
