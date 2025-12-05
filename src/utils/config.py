"""Configuration management for the accessibility agent.

Loads settings from YAML files and environment variables,
with Pydantic validation.
"""

import os
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv
from pydantic import BaseModel, Field, field_validator


class NVDAConfig(BaseModel):
    """NVDA screen reader configuration."""

    log_path: str = Field(default="%TEMP%\\nvda.log")
    speech_viewer: bool = Field(default=True)
    log_level: str = Field(default="debug")
    response_timeout: float = Field(default=2.0)

    @field_validator("log_path")
    @classmethod
    def expand_env_vars(cls, v: str) -> str:
        """Expand environment variables in path."""
        return os.path.expandvars(v)


class BrowserConfig(BaseModel):
    """Browser configuration."""

    default: str = Field(default="auto")
    path: str | None = Field(default=None)
    headless: bool = Field(default=False)
    startup_timeout: float = Field(default=10.0)


class KeyboardConfig(BaseModel):
    """Keyboard control configuration."""

    delay_between_keys: float = Field(default=0.1)
    nvda_response_timeout: float = Field(default=2.0)
    retry_on_timeout: int = Field(default=1)
    initial_delay: float = Field(default=2.0)


class AgentConfig(BaseModel):
    """AI agent configuration."""

    model: str = Field(default="openai:gpt-4")
    max_actions: int = Field(default=100)
    exploration_depth: int = Field(default=3)
    temperature: float = Field(default=0.7)
    enable_memory: bool = Field(default=True)


class WCAGConfig(BaseModel):
    """WCAG compliance testing configuration."""

    version: str = Field(default="2.1")
    conformance_levels: list[str] = Field(default=["A", "AA", "AAA"])
    min_severity: str = Field(default="low")
    focus_areas: list[str] = Field(
        default=[
            "keyboard_navigation",
            "labels_and_names",
            "heading_structure",
            "link_text",
            "form_fields",
            "landmarks",
        ]
    )


class ReportingConfig(BaseModel):
    """Report generation configuration."""

    output_dir: str = Field(default="./reports")
    template: str = Field(default="default")
    include_screenshots: bool = Field(default=False)
    filename_format: str = Field(default="accessibility_report_{timestamp}.html")
    include_evidence: bool = Field(default=True)
    include_recommendations: bool = Field(default=True)


class LoggingConfig(BaseModel):
    """Logging configuration."""

    level: str = Field(default="INFO")
    format: str = Field(default="json")
    file: str = Field(default="./logs/agent.log")
    console: bool = Field(default=True)
    console_format: str = Field(default="text")
    rotate_size_mb: int = Field(default=10)
    backup_count: int = Field(default=5)


class AdvancedConfig(BaseModel):
    """Advanced configuration options."""

    debug_mode: bool = Field(default=False)
    correlation_window: float = Field(default=3.0)
    enable_playwright: bool = Field(default=False)


class Settings(BaseModel):
    """Main settings container."""

    nvda: NVDAConfig = Field(default_factory=NVDAConfig)
    browser: BrowserConfig = Field(default_factory=BrowserConfig)
    keyboard: KeyboardConfig = Field(default_factory=KeyboardConfig)
    agent: AgentConfig = Field(default_factory=AgentConfig)
    wcag: WCAGConfig = Field(default_factory=WCAGConfig)
    reporting: ReportingConfig = Field(default_factory=ReportingConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    advanced: AdvancedConfig = Field(default_factory=AdvancedConfig)


def load_config(config_path: str | Path | None = None) -> Settings:
    """Load configuration from YAML file and environment variables.

    Args:
        config_path: Path to YAML config file. If None, uses default config/settings.yaml

    Returns:
        Settings object with loaded configuration.

    Raises:
        FileNotFoundError: If config file not found.
        ValueError: If config validation fails.

    Example:
        >>> settings = load_config("config/settings.yaml")
        >>> print(settings.agent.model)
        'openai:gpt-4'
        >>> print(settings.nvda.log_path)
        'C:\\Users\\...\\AppData\\Local\\Temp\\nvda.log'
    """
    # Load environment variables from .env file
    load_dotenv()

    # Determine config file path
    if config_path is None:
        project_root = Path(__file__).parent.parent.parent
        config_path = project_root / "config" / "settings.yaml"
    else:
        config_path = Path(config_path)

    # Load YAML config
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path, "r", encoding="utf-8") as f:
        config_data: dict[str, Any] = yaml.safe_load(f)

    # Override with environment variables
    # Check for OPENAI_API_KEY (required for agent)
    if not os.getenv("OPENAI_API_KEY"):
        raise ValueError(
            "OPENAI_API_KEY environment variable not set. "
            "Please add it to your .env file or set it in your environment."
        )

    # Override model if specified in env
    if os.getenv("OPENAI_MODEL"):
        if "agent" not in config_data:
            config_data["agent"] = {}
        config_data["agent"]["model"] = os.getenv("OPENAI_MODEL")

    # Override NVDA log path if specified in env
    if os.getenv("NVDA_LOG_PATH"):
        if "nvda" not in config_data:
            config_data["nvda"] = {}
        config_data["nvda"]["log_path"] = os.getenv("NVDA_LOG_PATH")

    # Create and validate settings
    try:
        settings = Settings(**config_data)
    except Exception as e:
        raise ValueError(f"Config validation failed: {e}") from e

    return settings


def get_settings() -> Settings:
    """Get settings singleton.

    Returns:
        Settings instance loaded from default config file.

    Example:
        >>> settings = get_settings()
        >>> logger = get_logger("agent", **settings.logging.model_dump())
    """
    if not hasattr(get_settings, "_settings"):
        get_settings._settings = load_config()  # type: ignore
    return get_settings._settings  # type: ignore
