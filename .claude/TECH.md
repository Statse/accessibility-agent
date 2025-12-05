# TECH.md - Project Technical Standards

**Project:** Agentic Accessibility Testing Environment
**Purpose:** AI agent simulating screen reader user (NVDA) to test websites and generate WCAG compliance reports

## Language & Runtime

- **Language:** Python 3.11+
- **Virtual Environment:** venv (standard library)
- **Package Manager:** pip
- **Python Path:** System Python or pyenv for version management

## Core Dependencies

### AI & Agent Framework
- **Pydantic AI:** https://ai.pydantic.dev/ - Agent orchestration and decision-making
- **Pydantic:** 2.x - Data validation and settings management

### Windows Desktop Automation
- **pynput:** Keyboard and mouse control at OS level (preferred over pyautogui for reliability)
- **pywin32:** Windows API access for COM objects and system integration
- **pywinauto:** Windows UI Automation API access (optional, for advanced element inspection)

### Browser & Web
- **Default Browser:** Chrome/Edge (user's installed browser, not headless)
- **Browser Launch:** subprocess + Windows shell commands
- **Page Analysis (optional):** Playwright in headed mode for DOM inspection and axe-core integration

### Screen Reader Integration
- **Screen Reader:** NVDA (installed on system)
- **Integration Method:** Log file parsing (real-time monitoring)
- **NVDA Setup Required:**
  - Enable logging: NVDA Preferences → Tools → Log level: Debug
  - Enable speech viewer: NVDA → Tools → Speech Viewer
  - Log file location: `%TEMP%\nvda.log` or configured path

### Logging & Monitoring
- **Logging:** Python logging module with structured logs (JSON format)
- **Log Levels:** DEBUG, INFO, WARNING, ERROR
- **Log Storage:** Local files + console output
- **Action Correlation:** Custom logger to correlate keyboard actions with NVDA output

### WCAG Validation
- **WCAG Version:** WCAG 2.1/2.2
- **Conformance Levels:** A, AA, AAA (all levels)
- **Validation Strategy:**
  - Behavioral testing via screen reader simulation
  - Optional: axe-core integration via Playwright for automated checks
  - Manual issue detection based on agent's experience
  - Success criteria mapping to WCAG guidelines

### Report Generation
- **Template Engine:** Jinja2
- **Output Format:** HTML (primary for Jenkins integration)
- **Report Structure:**
  - Executive summary
  - Issue list by severity (Critical, High, Medium, Low)
  - WCAG criteria categorization (A, AA, AAA)
  - Evidence (screenshots, logs, keyboard sequences)
  - Recommendations
- **CI/CD Integration:** HTML artifacts for Jenkins, exit codes for pass/fail

## Testing

- **Unit Tests:** pytest
- **Integration Tests:** pytest with fixtures for NVDA and browser
- **Test Coverage Target:** 80%+
- **Mocking:** unittest.mock for external dependencies (NVDA, keyboard)
- **TDD Approach:** Write failing tests first for complex logic (agent decisions, parsers)

## Code Style & Conventions

- **Linter:** pylint + flake8
- **Formatter:** black (line length: 100)
- **Type Checker:** mypy (strict mode)
- **Import Sorting:** isort
- **Docstring Style:** Google style

### Naming Conventions
- **Modules:** snake_case (e.g., `nvda_parser.py`, `keyboard_controller.py`)
- **Classes:** PascalCase (e.g., `NVDALogParser`, `AccessibilityAgent`)
- **Functions/Methods:** snake_case (e.g., `parse_log_entry`, `send_keystroke`)
- **Constants:** UPPER_SNAKE_CASE (e.g., `NVDA_LOG_PATH`, `MAX_RETRIES`)
- **Private:** Leading underscore (e.g., `_internal_method`)

### Type Hints
- **Required:** All function signatures must have type hints
- **Return types:** Always specify return types
- **Collections:** Use `list[str]`, `dict[str, int]` (Python 3.11+ syntax)
- **Optional:** Use `Optional[T]` or `T | None`

### Git Commit Style
- **Format:** Conventional Commits
- **Types:** `feat:`, `fix:`, `refactor:`, `test:`, `docs:`, `chore:`
- **Example:** `feat: add NVDA log parser with real-time monitoring`

## Project Structure

```
accessibility-agent/
├── src/
│   ├── agent/              # Pydantic AI agent implementation
│   │   ├── __init__.py
│   │   ├── accessibility_agent.py
│   │   └── decision_engine.py
│   ├── automation/         # Keyboard/mouse control
│   │   ├── __init__.py
│   │   ├── keyboard_controller.py
│   │   └── browser_launcher.py
│   ├── screen_reader/      # NVDA integration
│   │   ├── __init__.py
│   │   ├── nvda_parser.py
│   │   └── output_monitor.py
│   ├── navigation/         # Web navigation strategies
│   │   ├── __init__.py
│   │   ├── navigator.py
│   │   └── interaction_strategies.py
│   ├── wcag/               # WCAG analysis
│   │   ├── __init__.py
│   │   ├── validator.py
│   │   ├── issue_detector.py
│   │   └── criteria_mapper.py
│   ├── reporting/          # Report generation
│   │   ├── __init__.py
│   │   ├── html_generator.py
│   │   └── templates/
│   │       └── report.html.jinja2
│   ├── utils/              # Utilities
│   │   ├── __init__.py
│   │   ├── logger.py
│   │   └── config.py
│   └── main.py             # Entry point
├── tests/                  # Test suite
│   ├── unit/
│   ├── integration/
│   └── fixtures/
├── logs/                   # Application logs
├── reports/                # Generated reports
├── config/                 # Configuration files
│   └── settings.yaml
├── requirements.txt        # Dependencies
├── requirements-dev.txt    # Dev dependencies
├── pyproject.toml          # Black, isort, mypy config
├── pytest.ini              # Pytest config
└── README.md               # Project documentation
```

## Development Commands

```bash
# Setup
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Run agent
python src/main.py --url https://example.com

# Testing
pytest                          # Run all tests
pytest tests/unit/              # Run unit tests
pytest --cov=src --cov-report=html  # With coverage

# Linting & Formatting
black src/ tests/               # Format code
isort src/ tests/               # Sort imports
flake8 src/ tests/              # Lint
pylint src/ tests/              # Lint (strict)
mypy src/                       # Type check
```

## Common Patterns

### Error Handling
```python
try:
    result = operation()
except SpecificException as e:
    logger.error(f"Operation failed: {e}")
    raise
```

### Logging
```python
import logging

logger = logging.getLogger(__name__)
logger.info("Action performed", extra={"action": "tab", "element": "button"})
```

### Agent Decision Pattern
```python
from pydantic_ai import Agent

agent = Agent(
    model="openai:gpt-4",
    system_prompt="You are an accessibility testing agent...",
)

result = agent.run_sync("Navigate to login form")
```

### NVDA Output Correlation
```python
# Log keyboard action
logger.info("Keyboard action", extra={"key": "Tab", "timestamp": time.time()})

# Wait for NVDA response
nvda_output = nvda_monitor.get_output_after(timestamp, timeout=2.0)

# Correlate
logger.info("NVDA response", extra={"output": nvda_output, "correlated": True})
```

## Windows-Specific Considerations

- **File Paths:** Use `pathlib.Path` for cross-platform compatibility
- **Line Endings:** CRLF (`\r\n`) for Windows
- **NVDA Installation:** Assume NVDA installed at default location or in PATH
- **Browser:** Detect default browser via registry or use configurable path
- **COM Objects:** Use `pythoncom.CoInitialize()` when needed

## Configuration

Use `config/settings.yaml` for:
- NVDA log file path
- Browser executable path
- Keyboard delay settings
- Report output directory
- WCAG conformance level targets
- Timeout settings

## CI/CD Integration (Jenkins)

- **HTML Reports:** Generate in `reports/` directory
- **Exit Codes:** 0 = pass, 1 = issues found, 2 = error
- **Artifacts:** Publish `reports/*.html` as Jenkins artifacts
- **JUnit XML:** Optional pytest JUnit XML for test result integration

## Security & Best Practices

- **No Hardcoded Credentials:** Use environment variables or secure config
- **Input Validation:** Validate URLs and user inputs
- **Safe Keyboard Input:** Sanitize any user-provided text before sending keystrokes
- **Resource Cleanup:** Always close browser, stop NVDA monitoring on exit
- **Exception Handling:** Catch and log all exceptions, graceful degradation
