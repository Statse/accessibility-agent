# PLAN.md - Task Status Board

**Project:** Agentic Accessibility Testing Environment
**Goal:** AI agent simulating screen reader user to test websites and generate WCAG compliance reports

Manager's source of truth for project tasks. Keep lightweight and scannable.

---

## Active Tasks

### Phase 1: Project Foundation

| Task | Status | Assigned To | Priority | Dependencies |
|------|--------|-------------|----------|--------------|
| Setup project structure (folders, __init__.py files) | [ ] PENDING | Python Engineer | HIGH | - |
| Create requirements.txt with core dependencies | [ ] PENDING | Python Engineer | HIGH | - |
| Create requirements-dev.txt with dev dependencies | [ ] PENDING | Python Engineer | HIGH | - |
| Setup pyproject.toml (black, isort, mypy config) | [ ] PENDING | Python Engineer | HIGH | - |
| Setup pytest.ini and test structure | [ ] PENDING | Python Engineer | HIGH | - |
| Create config/settings.yaml with default config | [ ] PENDING | Python Engineer | MEDIUM | - |
| Create utils/logger.py with structured logging | [ ] PENDING | Python Engineer | MEDIUM | - |
| Create utils/config.py for settings management | [ ] PENDING | Python Engineer | MEDIUM | - |

### Phase 2: NVDA Integration

| Task | Status | Assigned To | Priority | Dependencies |
|------|--------|-------------|----------|--------------|
| Research NVDA log file format and location | [ ] PENDING | Python Engineer | HIGH | - |
| Create screen_reader/nvda_parser.py for log parsing | [ ] PENDING | Python Engineer | HIGH | Log format research |
| Implement real-time log file monitoring | [ ] PENDING | Python Engineer | HIGH | nvda_parser.py |
| Create screen_reader/output_monitor.py for output tracking | [ ] PENDING | Python Engineer | HIGH | Log monitoring |
| Implement timestamp-based output correlation | [ ] PENDING | Python Engineer | HIGH | output_monitor.py |
| Write tests for NVDA log parser | [ ] PENDING | Tester | MEDIUM | nvda_parser.py |
| Write tests for output monitor | [ ] PENDING | Tester | MEDIUM | output_monitor.py |

### Phase 3: Keyboard Control

| Task | Status | Assigned To | Priority | Dependencies |
|------|--------|-------------|----------|--------------|
| Create automation/keyboard_controller.py with pynput | [✓] DONE | Python Engineer | HIGH | - |
| Implement Tab, Enter, Arrow keys, Escape, Space | [✓] DONE | Python Engineer | HIGH | keyboard_controller.py |
| Implement configurable delay between keystrokes | [✓] DONE | Python Engineer | MEDIUM | keyboard_controller.py |
| Implement keyboard shortcuts (Ctrl+F, NVDA keys) | [✓] DONE | Python Engineer | MEDIUM | keyboard_controller.py |
| Create automation/browser_launcher.py | [✓] DONE | Python Engineer | HIGH | - |
| Implement default browser detection (Windows registry) | [✓] DONE | Python Engineer | MEDIUM | browser_launcher.py |
| Implement URL launch in browser | [✓] DONE | Python Engineer | HIGH | browser_launcher.py |
| Write tests for keyboard controller | [✓] DONE | Tester | MEDIUM | keyboard_controller.py |
| Write tests for browser launcher | [✓] DONE | Tester | LOW | browser_launcher.py |

### Phase 4: Action-Feedback Correlation

| Task | Status | Assigned To | Priority | Dependencies |
|------|--------|-------------|----------|--------------|
| Design action log data structure (JSON schema) | [ ] PENDING | Python Engineer | HIGH | - |
| Implement action logger (keyboard + timestamp) | [ ] PENDING | Python Engineer | HIGH | Action log schema |
| Implement feedback correlator (match action → NVDA output) | [ ] PENDING | Python Engineer | HIGH | output_monitor.py |
| Implement correlation timeout handling | [ ] PENDING | Python Engineer | MEDIUM | Feedback correlator |
| Create correlation report formatter | [ ] PENDING | Python Engineer | MEDIUM | Feedback correlator |
| Write tests for action-feedback correlation | [ ] PENDING | Tester | HIGH | Correlation complete |

### Phase 5: Pydantic AI Agent

| Task | Status | Assigned To | Priority | Dependencies |
|------|--------|-------------|----------|--------------|
| Research Pydantic AI setup and patterns | [ ] PENDING | Python Engineer | HIGH | - |
| Create agent/accessibility_agent.py skeleton | [ ] PENDING | Python Engineer | HIGH | Pydantic AI research |
| Define agent system prompt (screen reader user persona) | [ ] PENDING | Python Engineer | HIGH | accessibility_agent.py |
| Integrate keyboard controller with agent | [ ] PENDING | Python Engineer | HIGH | Phase 3 complete |
| Integrate NVDA monitor with agent | [ ] PENDING | Python Engineer | HIGH | Phase 2 complete |
| Create agent/decision_engine.py for navigation logic | [ ] PENDING | Python Engineer | HIGH | accessibility_agent.py |
| Implement agent state management | [ ] PENDING | Python Engineer | MEDIUM | accessibility_agent.py |
| Implement agent memory (visited elements, actions taken) | [ ] PENDING | Python Engineer | MEDIUM | decision_engine.py |
| Write tests for agent decision engine | [ ] PENDING | Tester | HIGH | decision_engine.py |

### Phase 6: Web Navigation Strategies

| Task | Status | Assigned To | Priority | Dependencies |
|------|--------|-------------|----------|--------------|
| Create navigation/navigator.py for navigation coordination | [ ] PENDING | Python Engineer | HIGH | Phase 5 complete |
| Implement navigation by headings (H key in NVDA) | [ ] PENDING | Python Engineer | HIGH | navigator.py |
| Implement navigation by links (Tab, K key) | [ ] PENDING | Python Engineer | HIGH | navigator.py |
| Implement navigation by landmarks (D key) | [ ] PENDING | Python Engineer | HIGH | navigator.py |
| Implement navigation by form fields (F key) | [ ] PENDING | Python Engineer | MEDIUM | navigator.py |
| Implement navigation by buttons (B key) | [ ] PENDING | Python Engineer | MEDIUM | navigator.py |
| Create navigation/interaction_strategies.py | [ ] PENDING | Python Engineer | HIGH | navigator.py |
| Implement form filling strategy | [ ] PENDING | Python Engineer | HIGH | interaction_strategies.py |
| Implement link activation strategy | [ ] PENDING | Python Engineer | HIGH | interaction_strategies.py |
| Implement page exploration strategy | [ ] PENDING | Python Engineer | HIGH | interaction_strategies.py |
| Write tests for navigation strategies | [ ] PENDING | Tester | HIGH | Strategies complete |

### Phase 7: WCAG Analysis

| Task | Status | Assigned To | Priority | Dependencies |
|------|--------|-------------|----------|--------------|
| Create wcag/criteria_mapper.py with WCAG 2.1/2.2 criteria | [ ] PENDING | Python Engineer | HIGH | - |
| Create wcag/issue_detector.py skeleton | [ ] PENDING | Python Engineer | HIGH | - |
| Implement detection: Missing alt text (1.1.1 - Level A) | [ ] PENDING | Python Engineer | HIGH | issue_detector.py |
| Implement detection: Missing form labels (1.3.1, 3.3.2 - Level A) | [ ] PENDING | Python Engineer | HIGH | issue_detector.py |
| Implement detection: Keyboard trap detection (2.1.2 - Level A) | [ ] PENDING | Python Engineer | HIGH | issue_detector.py |
| Implement detection: Missing skip links (2.4.1 - Level A) | [ ] PENDING | Python Engineer | MEDIUM | issue_detector.py |
| Implement detection: Poor heading structure (2.4.6 - Level AA) | [ ] PENDING | Python Engineer | MEDIUM | issue_detector.py |
| Implement detection: Insufficient link text (2.4.4 - Level A) | [ ] PENDING | Python Engineer | MEDIUM | issue_detector.py |
| Implement detection: Incomplete ARIA usage (4.1.2 - Level A) | [ ] PENDING | Python Engineer | MEDIUM | issue_detector.py |
| Create wcag/validator.py to orchestrate detection | [ ] PENDING | Python Engineer | HIGH | issue_detector.py |
| Implement issue severity classification | [ ] PENDING | Python Engineer | HIGH | validator.py |
| Implement evidence collection (logs, actions, NVDA output) | [ ] PENDING | Python Engineer | HIGH | validator.py |
| Write tests for WCAG issue detection | [ ] PENDING | Tester | HIGH | Detection complete |

### Phase 8: HTML Report Generation

| Task | Status | Assigned To | Priority | Dependencies |
|------|--------|-------------|----------|--------------|
| Create reporting/html_generator.py skeleton | [ ] PENDING | Python Engineer | HIGH | Phase 7 complete |
| Design HTML report template structure | [ ] PENDING | Python Engineer | HIGH | - |
| Create reporting/templates/report.html.jinja2 | [ ] PENDING | Python Engineer | HIGH | Template structure |
| Implement executive summary section | [ ] PENDING | Python Engineer | HIGH | html_generator.py |
| Implement issue list by severity | [ ] PENDING | Python Engineer | HIGH | html_generator.py |
| Implement WCAG criteria grouping (A, AA, AAA) | [ ] PENDING | Python Engineer | HIGH | html_generator.py |
| Implement evidence section (logs, actions, NVDA output) | [ ] PENDING | Python Engineer | MEDIUM | html_generator.py |
| Implement recommendations section | [ ] PENDING | Python Engineer | MEDIUM | html_generator.py |
| Add CSS styling to report template | [ ] PENDING | Python Engineer | LOW | report.html.jinja2 |
| Write tests for report generation | [ ] PENDING | Tester | MEDIUM | html_generator.py |

### Phase 9: Main Entry Point & CLI

| Task | Status | Assigned To | Priority | Dependencies |
|------|--------|-------------|----------|--------------|
| Create src/main.py with argparse CLI | [ ] PENDING | Python Engineer | HIGH | All phases complete |
| Implement --url argument for target URL | [ ] PENDING | Python Engineer | HIGH | main.py |
| Implement --output argument for report path | [ ] PENDING | Python Engineer | MEDIUM | main.py |
| Implement --config argument for custom config | [ ] PENDING | Python Engineer | LOW | main.py |
| Implement orchestration: Launch browser → Agent → WCAG → Report | [ ] PENDING | Python Engineer | HIGH | main.py |
| Implement exit codes (0=pass, 1=issues, 2=error) | [ ] PENDING | Python Engineer | MEDIUM | main.py |
| Implement graceful shutdown (cleanup, close browser) | [ ] PENDING | Python Engineer | HIGH | main.py |
| Write integration tests for full workflow | [ ] PENDING | Tester | HIGH | main.py complete |

### Phase 10: Testing & Quality

| Task | Status | Assigned To | Priority | Dependencies |
|------|--------|-------------|----------|--------------|
| Run full test suite and fix failing tests | [ ] PENDING | Tester | HIGH | All phases complete |
| Achieve 80%+ code coverage | [ ] PENDING | Tester | HIGH | Test suite passing |
| Run pylint and fix issues | [ ] PENDING | Python Engineer | HIGH | - |
| Run flake8 and fix issues | [ ] PENDING | Python Engineer | HIGH | - |
| Run mypy and fix type errors | [ ] PENDING | Python Engineer | HIGH | - |
| Format code with black | [ ] PENDING | Python Engineer | MEDIUM | - |
| Sort imports with isort | [ ] PENDING | Python Engineer | MEDIUM | - |
| Code review for security issues | [ ] PENDING | Reviewer | HIGH | All code complete |
| Code review for performance issues | [ ] PENDING | Reviewer | MEDIUM | All code complete |

### Phase 11: Documentation

| Task | Status | Assigned To | Priority | Dependencies |
|------|--------|-------------|----------|--------------|
| Write README.md with project overview | [ ] PENDING | Documentation Agent | HIGH | Project complete |
| Write SETUP.md with installation instructions | [ ] PENDING | Documentation Agent | HIGH | - |
| Write USAGE.md with CLI examples | [ ] PENDING | Documentation Agent | HIGH | - |
| Document NVDA setup requirements | [ ] PENDING | Documentation Agent | HIGH | - |
| Write module docstrings (Google style) | [ ] PENDING | Documentation Agent | MEDIUM | - |
| Write function docstrings with examples | [ ] PENDING | Documentation Agent | MEDIUM | - |
| Create architecture diagram | [ ] PENDING | Documentation Agent | LOW | - |
| Write troubleshooting guide | [ ] PENDING | Documentation Agent | MEDIUM | - |

### Phase 12: Jenkins Integration (Optional)

| Task | Status | Assigned To | Priority | Dependencies |
|------|--------|-------------|----------|--------------|
| Create Jenkinsfile for CI/CD | [ ] PENDING | Python Engineer | LOW | Project complete |
| Configure HTML report publishing | [ ] PENDING | Python Engineer | LOW | Jenkinsfile |
| Configure test result integration | [ ] PENDING | Python Engineer | LOW | Jenkinsfile |
| Test Jenkins pipeline | [ ] PENDING | Tester | LOW | Jenkinsfile complete |

---

## Status Definitions

- `[ ] PENDING` - Not started, waiting for assignment or dependencies
- `[→] IN PROGRESS` - Currently being worked on
- `[✓] DONE` - Completed and verified
- `[⚠] BLOCKED` - Stuck, see WIKI.md for blocker details

---

## Notes

- **Current Focus:** Phase 1 (Project Foundation)
- **Next Phase:** Phase 2 (NVDA Integration) depends on Phase 1 completion
- Reference WIKI.md for detailed specs, blockers, and Q&A
- Manager updates status and assignments
- All agents read to find their [→] IN PROGRESS tasks

---

## Copy-Paste Agent Prompts

### To Start Phase 1:
```
Act as Python Engineer. Implement Phase 1 tasks: Setup project structure, requirements files, and configuration.
```

### To Start Phase 2:
```
Act as Python Engineer. Implement Phase 2 tasks: NVDA log parser and output monitor.
```

### To Run Tests:
```
Act as Tester. Run tests for completed modules in Phase X.
```

### To Review Code:
```
Act as Reviewer. Review Phase X code for security, performance, and style issues.
```

### To Write Documentation:
```
Act as Documentation Agent. Write documentation for completed Phase X.
```
