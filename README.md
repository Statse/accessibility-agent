# Agentic Accessibility Testing Environment

AI agent simulating a screen reader user to test websites and generate WCAG compliance reports.

## 🤖 LLM Provider Support

The accessibility agent supports multiple LLM providers:

- **OpenAI** (GPT-4, GPT-3.5-turbo) - Cloud-based, high quality
- **Ollama** (Llama 3.2, Mistral, Qwen, etc.) - Local, private, free

### Quick Setup: Ollama (Local LLM)

For private, cost-free testing with local models:

```bash
# 1. Install Ollama
# Download from https://ollama.com

# 2. Pull a model
ollama pull llama3.2

# 3. Configure provider
echo "LLM_PROVIDER=ollama" >> .env
echo "LLM_MODEL=llama3.2" >> .env

# 4. Test integration
python test_ollama.py
```

See [docs/OLLAMA_SETUP.md](docs/OLLAMA_SETUP.md) for detailed setup instructions.

### Quick Setup: OpenAI

```bash
# Set your API key in .env
echo "OPENAI_API_KEY=sk-your-key-here" >> .env
echo "LLM_PROVIDER=openai" >> .env
```

## 🚀 Quick Start

```bash
# 1. Clone the repository
git clone <repository-url>
cd accessibility-agent

# 2. Create and activate virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# 3. Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# 4. Test that everything works
python test_components.py

# 5. Run the test suite
pytest
```

## 📋 Current Status

### ✅ Completed Phases

- **Phase 1: Project Foundation** - Complete
  - Project structure, configuration, utilities
- **Phase 2: NVDA Integration** - Complete
  - Log parsing, output monitoring
- **Phase 3: Keyboard Control** - Complete
  - OS-level keyboard automation, browser launching

### 🔜 Upcoming Phases

- **Phase 4**: Action-Feedback Correlation
- **Phase 5**: Pydantic AI Agent
- **Phase 6**: Web Navigation Strategies
- **Phase 7**: WCAG Analysis
- **Phase 8**: HTML Report Generation
- **Phase 9**: Main Entry Point & CLI

## 🧪 Testing

### Safe Component Test (No Keystrokes)

```bash
python test_components.py
```

This validates all components without sending any keyboard input.

### Full Test Suite

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific tests
pytest tests/unit/test_keyboard_controller.py -v
pytest tests/unit/test_browser_launcher.py -v
```

### Interactive Demo (Sends Keystrokes!)

```bash
python demo.py
```

**Warning**: This will actually send keyboard inputs and open your browser!

## 📦 Components

### Keyboard Controller

```python
from src.automation.keyboard_controller import KeyboardController, NVDAKey

# Initialize with configurable delay
controller = KeyboardController(delay=0.5)

# Basic keys
controller.press_tab()
controller.press_enter()
controller.press_space()

# NVDA shortcuts
controller.press_nvda_key(NVDAKey.NEXT_HEADING)  # H
controller.press_nvda_key(NVDAKey.PREV_LINK)     # Shift+K

# Combinations
controller.press_ctrl_f()
controller.press_combination(["ctrl", "shift", "t"])

# Type text
controller.type_text("example@email.com")
```

### Browser Launcher

```python
from src.automation.browser_launcher import BrowserLauncher

# Detect default browser
info = BrowserLauncher.get_browser_info()
print(f"Browser: {info['name']} at {info['path']}")

# Launch URL
launcher = BrowserLauncher()
launcher.launch_url("https://example.com")

# Use specific browser
launcher = BrowserLauncher(browser_path="C:\\...\\chrome.exe")
launcher.launch_url("https://example.com", new_window=True)
```

### Logger

```python
from src.utils.logger import get_logger

logger = get_logger(__name__)
logger.info("Starting test", extra={"url": "example.com"})
```

### Configuration

```python
from src.utils.config import get_settings

settings = get_settings()
print(f"Keyboard delay: {settings.keyboard.delay_between_keys}s")
print(f"NVDA log: {settings.nvda.log_path}")
```

## 🔧 Configuration

Edit `config/settings.yaml` to customize:

```yaml
keyboard:
  delay_between_keys: 0.1
  nvda_response_timeout: 2.0

browser:
  default: "auto"  # or path to browser

nvda:
  log_path: "%TEMP%\\nvda.log"
  log_level: "debug"

logging:
  level: "INFO"
  format: "json"
```

## 📚 Documentation

- **[QUICKSTART.md](QUICKSTART.md)** - Detailed setup and usage guide
- **[.claude/PLAN.md](.claude/PLAN.md)** - Complete project roadmap
- **[.claude/WIKI.md](.claude/WIKI.md)** - Architecture and implementation notes
- **[.claude/TECH.md](.claude/TECH.md)** - Technical standards and conventions

## 🏗️ Architecture

```
accessibility-agent/
├── src/
│   ├── automation/       # Keyboard control, browser launching
│   ├── screen_reader/    # NVDA integration
│   ├── agent/            # AI agent (Phase 5)
│   ├── navigation/       # Navigation strategies (Phase 6)
│   ├── wcag/             # WCAG validation (Phase 7)
│   ├── reporting/        # Report generation (Phase 8)
│   └── utils/            # Logging, config
├── tests/
│   ├── unit/             # Unit tests
│   └── integration/      # Integration tests
├── config/
│   └── settings.yaml     # Configuration
└── .claude/              # Project documentation
```

## 🧪 Test Coverage

```
Module                      Statements   Coverage
─────────────────────────────────────────────────
keyboard_controller.py           100      100%
browser_launcher.py              111       91%
nvda_parser.py                   101      (TBD)
output_monitor.py                152      (TBD)
─────────────────────────────────────────────────
Total                            610       33%
```

## 🛠️ Technology Stack

- **Python 3.11+**
- **pynput** - OS-level keyboard control
- **Pydantic AI** - Agent orchestration (Phase 5)
- **pytest** - Testing framework
- **Windows Registry** - Browser detection

## 🤝 Contributing

See `.claude/CLAUDE.md` for development workflow and agent personas:
- Manager - Project orchestration
- Python Engineer - Implementation
- Tester - QA and testing
- Reviewer - Code review
- Documentation Agent - Documentation

## 📝 License

[Your License Here]

## 🔗 Links

- [NVDA Screen Reader](https://www.nvaccess.org/)
- [WCAG Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)
- [Pydantic AI](https://ai.pydantic.dev/)

---

🤖 Generated with [Claude Code](https://claude.com/claude-code)
