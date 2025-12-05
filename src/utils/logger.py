"""Structured logging utility for the accessibility agent.

Provides JSON and text logging with support for correlation IDs,
structured extra fields, and action-feedback tracking.
"""

import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from logging.handlers import RotatingFileHandler


class JSONFormatter(logging.Formatter):
    """Custom formatter that outputs logs in JSON format."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON.

        Args:
            record: The log record to format.

        Returns:
            JSON-formatted log string.
        """
        log_data: dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields if present
        if hasattr(record, "extra_fields"):
            log_data.update(record.extra_fields)

        return json.dumps(log_data)


class StructuredLogger:
    """Structured logger with support for JSON and text formats."""

    def __init__(
        self,
        name: str,
        log_file: str | Path | None = None,
        level: str = "INFO",
        format_type: str = "json",
        console: bool = True,
        console_format: str = "text",
        rotate_size_mb: int = 10,
        backup_count: int = 5,
    ):
        """Initialize structured logger.

        Args:
            name: Logger name.
            log_file: Path to log file. If None, only console logging.
            level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
            format_type: Format for file logging ("json" or "text").
            console: Enable console logging.
            console_format: Format for console logging ("json" or "text").
            rotate_size_mb: Max log file size in MB before rotation.
            backup_count: Number of backup log files to keep.
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, level.upper()))
        self.logger.handlers.clear()

        # File handler with rotation
        if log_file:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)

            file_handler = RotatingFileHandler(
                log_path,
                maxBytes=rotate_size_mb * 1024 * 1024,
                backupCount=backup_count,
            )
            file_handler.setLevel(getattr(logging, level.upper()))

            if format_type == "json":
                file_handler.setFormatter(JSONFormatter())
            else:
                file_handler.setFormatter(
                    logging.Formatter(
                        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
                    )
                )

            self.logger.addHandler(file_handler)

        # Console handler
        if console:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(getattr(logging, level.upper()))

            if console_format == "json":
                console_handler.setFormatter(JSONFormatter())
            else:
                console_handler.setFormatter(
                    logging.Formatter(
                        "%(asctime)s - %(levelname)s - %(message)s",
                        datefmt="%Y-%m-%d %H:%M:%S",
                    )
                )

            self.logger.addHandler(console_handler)

    def debug(self, message: str, **extra: Any) -> None:
        """Log debug message with optional extra fields."""
        self._log(logging.DEBUG, message, extra)

    def info(self, message: str, **extra: Any) -> None:
        """Log info message with optional extra fields."""
        self._log(logging.INFO, message, extra)

    def warning(self, message: str, **extra: Any) -> None:
        """Log warning message with optional extra fields."""
        self._log(logging.WARNING, message, extra)

    def error(self, message: str, **extra: Any) -> None:
        """Log error message with optional extra fields."""
        self._log(logging.ERROR, message, extra)

    def critical(self, message: str, **extra: Any) -> None:
        """Log critical message with optional extra fields."""
        self._log(logging.CRITICAL, message, extra)

    def _log(self, level: int, message: str, extra: dict[str, Any]) -> None:
        """Internal method to log with extra fields.

        Args:
            level: Log level.
            message: Log message.
            extra: Extra structured fields to include.
        """
        # Create a new LogRecord with extra fields
        record = self.logger.makeRecord(
            self.logger.name,
            level,
            "(unknown file)",
            0,
            message,
            (),
            None,
        )

        # Attach extra fields
        if extra:
            record.extra_fields = extra  # type: ignore

        self.logger.handle(record)


def get_logger(
    name: str,
    log_file: str | Path | None = None,
    level: str = "INFO",
    format_type: str = "json",
    console: bool = True,
    console_format: str = "text",
) -> StructuredLogger:
    """Get or create a structured logger.

    Args:
        name: Logger name.
        log_file: Path to log file.
        level: Log level.
        format_type: Format for file logging.
        console: Enable console logging.
        console_format: Format for console logging.

    Returns:
        Structured logger instance.

    Example:
        >>> logger = get_logger("accessibility_agent")
        >>> logger.info("Starting agent", url="https://example.com")
        >>> logger.debug("Keyboard action", key="Tab", timestamp=time.time())
    """
    return StructuredLogger(
        name=name,
        log_file=log_file,
        level=level,
        format_type=format_type,
        console=console,
        console_format=console_format,
    )
