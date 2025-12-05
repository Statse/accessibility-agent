# Quickstart Guide

## Prerequisites

- **Python 3.11+** installed
- **Windows OS** (required for Windows registry browser detection and NVDA)
- **NVDA screen reader** installed (optional for now, required for full agent functionality)

## Setup

### 1. Create and activate virtual environment

```bash
# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Verify activation (should show venv path)
where python
```

### 2. Install dependencies

```bash
# Install core dependencies
pip install -r requirements.txt

# Install dev dependencies (for testing)
pip install -r requirements-dev.txt
```

### 3. Verify installation

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=src --cov-report=term-missing

# Run specific module tests
pytest tests/unit/test_keyboard_controller.py -v
pytest tests/unit/test_browser_launcher.py -v
```

## Current Implementation Status

✅ **Phase 1**: Project Foundation - Complete
✅ **Phase 2**: NVDA Integration - Complete
✅ **Phase 3**: Keyboard Control - Complete
⏳ **Phase 4**: Action-Feedback Correlation - Not started
⏳ **Phase 5**: Pydantic AI Agent - Not started
⏳ **Phase 9**: Main Entry Point & CLI - Not started

## What You Can Test Now

### 1. Keyboard Controller

The keyboard controller can send OS-level keystrokes:

```python
from src.automation.keyboard_controller import KeyboardController, NVDAKey

# Initialize controller with 0.5 second delay between keys
controller = KeyboardController(delay=0.5)

# Press basic keys
controller.press_tab()
controller.press_enter()
controller.press_space()

# Press NVDA navigation keys
controller.press_nvda_key(NVDAKey.NEXT_HEADING)  # H key
controller.press_nvda_key(NVDAKey.PREV_LINK)     # Shift+K

# Press key combinations
controller.press_ctrl_f()  # Ctrl+F
controller.press_combination(["ctrl", "shift", "t"])  # Ctrl+Shift+T

# Type text
controller.type_text("example@email.com")
```

### 2. Browser Launcher

The browser launcher can detect and open your default browser:

```python
from src.automation.browser_launcher import BrowserLauncher

# Get browser info
info = BrowserLauncher.get_browser_info()
print(f"Default browser: {info['name']} at {info['path']}")

# Launch URL in default browser
launcher = BrowserLauncher()
launcher.launch_url("https://example.com")

# Launch with explicit browser path
launcher = BrowserLauncher(browser_path="C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe")
launcher.launch_url("https://example.com", new_window=True)
```

### 3. Run Demo Script

See `demo.py` for a simple demonstration of the keyboard and browser modules working together.

```bash
python demo.py
```

## Configuration

Edit `config/settings.yaml` to customize:

- Keyboard delay between keystrokes
- NVDA log file path
- Browser executable path
- Logging settings

## Next Steps

To have a fully functional accessibility testing agent, we need to complete:

1. **Phase 5**: Implement Pydantic AI agent with decision-making logic
2. **Phase 4**: Implement action-feedback correlation (keyboard actions → NVDA output)
3. **Phase 6**: Implement web navigation strategies
4. **Phase 7**: Implement WCAG validation and issue detection
5. **Phase 8**: Implement HTML report generation
6. **Phase 9**: Implement main CLI entry point

## Troubleshooting

### "No module named pynput"
```bash
pip install -r requirements.txt
```

### "pytest not found"
```bash
pip install -r requirements-dev.txt
```

### Tests failing
```bash
# Run tests with verbose output to see what's failing
pytest -v

# Run a specific test
pytest tests/unit/test_keyboard_controller.py::TestKeyboardController::test_press_tab -v
```

### Permission errors with keyboard control
- Run your terminal/IDE as administrator on Windows
- Some applications may block simulated keyboard input for security

## Documentation

- **PLAN.md** - Full project roadmap with all 12 phases
- **WIKI.md** - Architecture, specs, and implementation notes
- **TECH.md** - Technical standards and coding conventions
- **CLAUDE.md** - Agent personas and workflow
