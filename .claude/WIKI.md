# WIKI.md - Shared Knowledge Base

**Project:** Agentic Accessibility Testing Environment
**Goal:** AI agent simulating screen reader user to test websites and generate WCAG compliance reports

Detailed context, specs, blockers, and inter-agent notes. All agents read/write.

---

## App Architecture

### High-Level Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         Main Entry Point                         │
│                         (src/main.py)                            │
│  - CLI argument parsing (--url, --output, --config)             │
│  - Orchestration: Browser → Agent → WCAG → Report               │
│  - Exit code management (0=pass, 1=issues, 2=error)             │
└────────────────────────┬────────────────────────────────────────┘
                         │
         ┌───────────────┼───────────────┐
         │               │               │
         ▼               ▼               ▼
┌─────────────┐  ┌──────────────┐  ┌─────────────┐
│  Browser    │  │  AI Agent    │  │  NVDA       │
│  Launcher   │  │  (Pydantic)  │  │  Monitor    │
│             │  │              │  │             │
│ - Detect    │  │ - Decision   │  │ - Log file  │
│   default   │  │   making     │  │   parser    │
│ - Launch    │  │ - State mgmt │  │ - Real-time │
│   URL       │  │ - Memory     │  │   monitor   │
│             │  │ - Navigation │  │ - Output    │
└─────────────┘  └──────┬───────┘  └──────▲──────┘
                        │                  │
                        │                  │
                        ▼                  │
                 ┌──────────────┐          │
                 │  Keyboard    │          │
                 │  Controller  ├──────────┘
                 │              │
                 │ - OS-level   │ Correlation:
                 │   keystrokes │ Action → Feedback
                 │ - Tab/Enter  │
                 │ - NVDA keys  │
                 └──────┬───────┘
                        │
                        ▼
                 ┌──────────────┐
                 │  Navigation  │
                 │  Strategies  │
                 │              │
                 │ - Headings   │
                 │ - Links      │
                 │ - Landmarks  │
                 │ - Forms      │
                 └──────┬───────┘
                        │
                        ▼
                 ┌──────────────┐
                 │  WCAG        │
                 │  Validator   │
                 │              │
                 │ - Issue      │
                 │   detection  │
                 │ - Criteria   │
                 │   mapping    │
                 │ - Evidence   │
                 └──────┬───────┘
                        │
                        ▼
                 ┌──────────────┐
                 │  HTML        │
                 │  Report      │
                 │  Generator   │
                 │              │
                 │ - Jinja2     │
                 │ - Summary    │
                 │ - Issues     │
                 │ - Recommend  │
                 └──────────────┘
```

### Data Flow

1. **User Input** → CLI receives URL, config, output path
2. **Browser Launch** → Default browser opens with target URL
3. **Agent Activation** → Pydantic AI agent begins exploration
4. **Keyboard Actions** → Agent sends keystrokes (Tab, H, K, Enter, etc.)
5. **NVDA Output** → Screen reader announces content
6. **Correlation** → Match keyboard action timestamps with NVDA output
7. **Navigation Loop** → Agent decides next action based on NVDA feedback
8. **Issue Detection** → Identify WCAG violations during navigation
9. **Evidence Collection** → Log actions, NVDA output, timestamps
10. **Report Generation** → Create HTML report with findings
11. **Exit** → Return exit code based on severity

### Module Breakdown

| Module | Purpose | Key Classes/Functions |
|--------|---------|----------------------|
| `agent/` | AI decision-making and orchestration | `AccessibilityAgent`, `DecisionEngine` |
| `automation/` | OS-level keyboard/mouse control | `KeyboardController`, `BrowserLauncher` |
| `screen_reader/` | NVDA integration and log parsing | `NVDALogParser`, `OutputMonitor` |
| `navigation/` | Web navigation strategies | `Navigator`, `InteractionStrategies` |
| `wcag/` | WCAG compliance validation | `Validator`, `IssueDetector`, `CriteriaMapper` |
| `reporting/` | HTML report generation | `HTMLGenerator`, Jinja2 templates |
| `utils/` | Shared utilities | `logger`, `config` |

---

## NVDA Integration Specs

### Log File Format

NVDA logs are written to: `%TEMP%\nvda.log` (typically `C:\Users\<user>\AppData\Local\Temp\nvda.log`)

**Required NVDA Settings:**
- Preferences → Tools → Log level: **Debug**
- Tools → **Speech Viewer** (enabled for visual verification)

**Log Entry Format:**
```
IO - inputCore.InputManager.executeGesture (10:23:45.123) MainThread (INFO):
Input: kb(desktop):tab
```

```
DEBUG - speech.speech.speak (10:23:45.234) MainThread (DEBUG):
Speaking: ['Login button']
```

**Parser Requirements:**
- Parse timestamp with millisecond precision
- Extract speech output text
- Extract keyboard input events
- Handle multi-line log entries
- Real-time file monitoring (tail -f style)

### NVDA Keyboard Shortcuts (Quick Reference)

| Key | Action | Purpose |
|-----|--------|---------|
| `Tab` | Next focusable element | Standard navigation |
| `Shift+Tab` | Previous focusable element | Reverse navigation |
| `H` | Next heading | Navigate by headings |
| `Shift+H` | Previous heading | Reverse heading nav |
| `K` | Next link | Navigate by links |
| `Shift+K` | Previous link | Reverse link nav |
| `D` | Next landmark | Navigate by ARIA landmarks |
| `F` | Next form field | Navigate by form fields |
| `B` | Next button | Navigate by buttons |
| `L` | Next list | Navigate by lists |
| `Enter` | Activate | Click link/button |
| `Space` | Activate | Toggle checkbox, click button |
| `Insert+Down` | Say all | Read from current position |
| `Insert+T` | Read title | Announce page title |

---

## Action-Feedback Correlation

### Data Structure (JSON Schema)

```python
from pydantic import BaseModel
from datetime import datetime

class KeyboardAction(BaseModel):
    timestamp: datetime
    key: str  # "Tab", "Enter", "h", etc.
    modifiers: list[str]  # ["Ctrl", "Shift"], etc.
    action_id: str  # Unique ID for correlation

class NVDAOutput(BaseModel):
    timestamp: datetime
    text: str  # What NVDA announced
    output_id: str  # Unique ID

class CorrelatedEvent(BaseModel):
    action: KeyboardAction
    output: NVDAOutput | None  # None if timeout
    latency_ms: float  # Time between action and output
    success: bool  # True if output received within timeout
```

### Correlation Algorithm

1. **Action Logged:** Keyboard action with timestamp T1
2. **Wait for Output:** Monitor NVDA log for new entries after T1
3. **Timeout:** If no output within 2 seconds, mark as timeout
4. **Match:** First output after T1 is correlated with action
5. **Latency:** Calculate T2 - T1 in milliseconds
6. **Store:** Log correlated event for WCAG analysis

### Edge Cases

- **Multiple rapid actions:** Queue actions, correlate in order
- **No NVDA output:** Element might be unlabeled (accessibility issue!)
- **Delayed output:** Slow page load, async content
- **Duplicate output:** NVDA repeats, take first occurrence

---

## WCAG Criteria Mapping

### Level A (Minimum Conformance)

| Criterion | Name | Detection Method |
|-----------|------|-----------------|
| 1.1.1 | Non-text Content | NVDA announces "unlabeled graphic" or silence on image |
| 1.3.1 | Info and Relationships | Missing form labels, improper heading structure |
| 2.1.1 | Keyboard | Element not reachable by Tab or NVDA navigation |
| 2.1.2 | No Keyboard Trap | Agent stuck, cannot Tab out of element |
| 2.4.1 | Bypass Blocks | No skip link detected at page start |
| 2.4.4 | Link Purpose | NVDA announces "link" with no text or "click here" |
| 3.3.2 | Labels or Instructions | Form field with no label announced |
| 4.1.2 | Name, Role, Value | NVDA cannot determine element role or value |

### Level AA (Standard Target)

| Criterion | Name | Detection Method |
|-----------|------|-----------------|
| 1.4.3 | Contrast | (Not detectable via screen reader, skip for v1) |
| 2.4.6 | Headings and Labels | Poor heading hierarchy (H1 → H4 without H2/H3) |
| 3.2.4 | Consistent Identification | Same elements announced differently |
| 3.3.3 | Error Suggestion | Form error with no recovery instructions |

### Level AAA (Highest Conformance)

- For v1, focus on A and AA
- AAA criteria can be added in future phases

---

## Agent System Prompt

**Draft Persona:**

```
You are an experienced screen reader user who is blind and relies on NVDA to navigate websites.

Your goal is to thoroughly explore a website and identify accessibility issues that would prevent
screen reader users from successfully using the site.

Your capabilities:
- You can send keyboard commands (Tab, Enter, arrow keys, NVDA shortcuts)
- You receive feedback from NVDA about what is announced
- You understand WCAG 2.1/2.2 accessibility guidelines
- You can detect missing labels, poor structure, keyboard traps, and other accessibility barriers

Your navigation strategy:
1. Start by reading the page title (Insert+T)
2. Check for skip links at the top (Tab once)
3. Explore headings structure (H key) to understand page layout
4. Navigate through interactive elements (Tab, K for links, B for buttons, F for forms)
5. Test form interactions (labels, error messages)
6. Identify any elements you cannot reach or understand
7. Document all accessibility issues you encounter

Remember: You cannot see the page. You rely entirely on NVDA's audio output.
If NVDA is silent or unclear, that's an accessibility issue.
```

---

## Known Issues & Blockers

| Issue | Reported By | Status | Action Needed |
|-------|-------------|--------|---------------|
| (No blockers yet) | - | - | - |

**Format for adding:** `- [Blocker Name] | Reported by [Agent] | [Timestamp] | [Details]`

---

## Inter-Agent Q&A

### Python Engineer Notes

*Questions and clarifications during implementation will be documented here.*

**Phase 3 Implementation:**
- **Engineer Note:** KeyboardController uses pynput for OS-level keyboard control. src/automation/keyboard_controller.py:1
- **Engineer Note:** Configurable delay (default 0.1s) prevents race conditions with NVDA. src/automation/keyboard_controller.py:52
- **Engineer Note:** NVDAKey enum uses uppercase values to indicate Shift modifier (e.g., "H" = Shift+H). src/automation/keyboard_controller.py:19
- **Engineer Note:** BrowserLauncher detects default browser from Windows registry via HKCU\...\UrlAssociations\http\UserChoice. src/automation/browser_launcher.py:77
- **Engineer Note:** Unquoted registry paths with spaces handled by finding .exe extension. src/automation/browser_launcher.py:105
- **Engineer Note:** Browser launch supports both explicit path (subprocess) and default browser (webbrowser module). src/automation/browser_launcher.py:150

**Example:**
- **Question:** Should we support multiple NVDA log file locations?
  - **Answer:** Start with default `%TEMP%\nvda.log`, make configurable in settings.yaml

### Tester Notes

*Test failures and edge cases discovered during testing.*

**Example:**
- **Test Failure:** Log parser fails on multi-line speech output
  - **Fix Needed:** Update parser regex to handle multi-line entries

### Code Review Findings

*Security, performance, style issues found during review.*

**Example:**
- **Code Review:** nvda_parser.py:45 - File handle not closed on exception
  - **Fix:** Use `with` statement for file operations

---

## Session Notes

**Format:** `- **Session [Date] ([Agent]):** [What was accomplished, blockers, next steps]`

### Session 2025-12-05 (Manager)
- Created comprehensive PLAN.md with 12 phases and 150+ tasks
- Updated TECH.md with full technology stack (Python 3.11+, Pydantic AI, pynput, NVDA)
- Updated WIKI.md with architecture, NVDA specs, WCAG criteria mapping
- Updated CLAUDE.md for Python desktop automation project
- **Next Steps:** Python Engineer to start Phase 1 (Project Foundation)

### Session 2025-12-05 (Python Engineer - Phase 3)
- **Completed:** Phase 3: Keyboard Control
- **Created:** src/automation/keyboard_controller.py with full pynput integration
  - Supports Tab, Enter, Arrow keys, Escape, Space
  - Configurable delay between keystrokes (default 0.1s)
  - NVDA keyboard shortcuts (H, K, D, F, B, L with Shift variants)
  - Special NVDA commands (Insert+Down for Say All, Insert+T for Read Title)
  - Ctrl+F and other combinations
  - Type text character-by-character
  - NVDAKey enum for navigation shortcuts
- **Created:** src/automation/browser_launcher.py with Windows integration
  - Windows registry browser detection (HKCU\...\UrlAssociations\http\UserChoice)
  - Handles both quoted and unquoted registry paths
  - Smart parsing for paths with spaces using .exe extension
  - Supports explicit browser path or system default
  - Browser-specific flags (Chrome: --new-window, Firefox: -new-window)
  - Browser info detection (Chrome, Firefox, Edge, Opera, Brave)
- **Created:** tests/unit/test_keyboard_controller.py (49 tests, 100% coverage)
- **Created:** tests/unit/test_browser_launcher.py (25 tests, 91% coverage)
- **Tests:** All 74 Phase 3 tests passing
- **Next Steps:** Phase 4 (Action-Feedback Correlation) or Phase 2 (NVDA Integration) depending on priority

---

## WCAG Testing Strategy

### Detection Methods by Type

1. **Keyboard Navigation Issues**
   - Cannot reach element via Tab or NVDA shortcuts → 2.1.1 violation
   - Stuck in element (keyboard trap) → 2.1.2 violation
   - Skip link missing → 2.4.1 violation

2. **Missing Labels/Alt Text**
   - NVDA silent on image → 1.1.1 violation (missing alt text)
   - NVDA announces "edit" with no label → 3.3.2 violation (missing form label)
   - NVDA announces "button" with no text → 4.1.2 violation (missing accessible name)

3. **Poor Structure**
   - Heading sequence H1 → H4 (skipped H2, H3) → 2.4.6 violation
   - NVDA cannot identify landmarks with D key → 1.3.1 violation

4. **Insufficient Link Text**
   - NVDA announces "link, click here" → 2.4.4 violation
   - Multiple links with identical text but different destinations → 2.4.4 violation

### Evidence Collection

For each issue, collect:
- **Screenshot** (optional, if Playwright integrated)
- **Keyboard sequence** leading to issue (e.g., "Tab → Tab → Tab → H")
- **NVDA output** at moment of issue (e.g., "unlabeled graphic")
- **Expected behavior** (e.g., "Should announce: 'Company logo, image'")
- **WCAG criterion** (e.g., "1.1.1 Non-text Content, Level A")
- **Severity** (Critical, High, Medium, Low)

---

## Configuration Specs

### config/settings.yaml

```yaml
# NVDA Settings
nvda:
  log_path: "%TEMP%\\nvda.log"  # Can be overridden
  speech_viewer: true            # Recommend enabling
  log_level: "debug"             # Required for detailed logs

# Browser Settings
browser:
  default: "auto"                # Auto-detect or specify path
  # path: "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"
  headless: false                # Always false for screen reader

# Keyboard Settings
keyboard:
  delay_between_keys: 0.1        # Seconds between keystrokes
  nvda_response_timeout: 2.0     # Seconds to wait for NVDA output
  retry_on_timeout: 1            # Retry failed actions N times

# Agent Settings
agent:
  model: "openai:gpt-4"          # Pydantic AI model
  max_actions: 100               # Prevent infinite loops
  exploration_depth: 3           # How many levels deep to explore

# WCAG Settings
wcag:
  version: "2.1"                 # "2.1" or "2.2"
  conformance_levels: ["A", "AA", "AAA"]  # Which levels to test
  min_severity: "low"            # Report issues >= this severity

# Reporting Settings
reporting:
  output_dir: "./reports"        # Where to save HTML reports
  template: "default"            # Template name
  include_screenshots: false     # For v1, no screenshots

# Logging Settings
logging:
  level: "INFO"                  # DEBUG, INFO, WARNING, ERROR
  format: "json"                 # "json" or "text"
  file: "./logs/agent.log"       # Log file location
```

---

## Report Structure Specs

### HTML Report Sections

1. **Executive Summary**
   - Total issues found
   - Breakdown by severity (Critical, High, Medium, Low)
   - Breakdown by WCAG level (A, AA, AAA)
   - Overall score/rating
   - Test metadata (URL, date, duration)

2. **Issue List by Severity**
   - **Critical:** Blocking issues (keyboard traps, inaccessible forms)
   - **High:** Major barriers (missing labels, unlabeled images)
   - **Medium:** Usability issues (poor link text, heading structure)
   - **Low:** Minor issues (inconsistent labeling)

3. **Issue Details**
   - Issue ID
   - WCAG criterion (e.g., "1.1.1 Non-text Content, Level A")
   - Description
   - Evidence (keyboard sequence, NVDA output)
   - Expected behavior
   - Recommendations for fix

4. **WCAG Criteria Breakdown**
   - Table showing all tested criteria
   - Pass/Fail status for each
   - Count of issues per criterion

5. **Recommendations**
   - Prioritized list of fixes
   - Resources/links for developers
   - Quick wins vs. long-term improvements

---

## Future Enhancements (Post-V1)

- **Visual screenshots:** Integrate Playwright for element screenshots
- **Automated fixes:** Suggest code changes to fix issues
- **Database storage:** Store test results for trend analysis
- **Multi-page testing:** Crawl entire site, not just one URL
- **Custom rules:** Allow users to define custom WCAG checks
- **PDF reports:** Generate PDF in addition to HTML
- **CI/CD plugins:** Native Jenkins/GitHub Actions integration
- **Real NVDA API:** Direct integration vs. log parsing
- **Multi-browser support:** Test with different browsers
- **Mobile accessibility:** Test mobile web with TalkBack/VoiceOver simulation
