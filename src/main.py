"""
Main Entry Point for Agentic Accessibility Testing

Orchestrates the complete accessibility testing workflow:
1. Launch browser with target URL
2. Initialize NVDA monitoring
3. Run agent exploration
4. Detect WCAG violations
5. Generate HTML report
6. Return exit code based on results
"""

import argparse
import sys
import logging
import signal
import webbrowser
import json
import os
import time
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

# Import core modules
from src.automation.browser_launcher import BrowserLauncher
from src.automation.keyboard_controller import KeyboardController
from src.agent.memory import AgentMemory
from src.agent.decision_engine import DecisionEngine, AgentState, NavigationStrategy
from src.correlation.action_logger import ActionLogger
from src.correlation.correlator import FeedbackCorrelator
from src.wcag.validator import WCAGValidator
from src.reporting.html_generator import HTMLGenerator
from src.screen_reader.output_monitor import NVDAOutputMonitor
from src.screen_reader.nvda_parser import NVDALogParser

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Exit codes
EXIT_SUCCESS = 0  # No issues found
EXIT_ISSUES_FOUND = 1  # Accessibility issues detected
EXIT_ERROR = 2  # Error during testing


def get_nvda_log_path() -> Optional[Path]:
    """
    Detect NVDA log file path.

    Returns:
        Path to NVDA log file, or None if not found
    """
    # Default NVDA log location (Windows TEMP directory)
    temp_dir = os.environ.get('TEMP', os.environ.get('TMP', ''))
    if temp_dir:
        log_path = Path(temp_dir) / 'nvda.log'
        if log_path.exists():
            logger.info(f"Found NVDA log file: {log_path}")
            return log_path
        else:
            logger.warning(f"NVDA log file not found at: {log_path}")
            logger.warning("Make sure NVDA is running with debug logging enabled")

    return None


class AccessibilityTestRunner:
    """
    Main test runner that orchestrates the complete workflow.
    """

    def __init__(
        self,
        url: str,
        output_path: str,
        max_actions: int = 100,
        browser_path: Optional[str] = None,
        open_report: bool = False,
        form_data: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize test runner.

        Args:
            url: Target URL to test
            output_path: Path for HTML report output
            max_actions: Maximum agent actions before stopping
            browser_path: Optional explicit browser path
            open_report: Automatically open report after generation
            form_data: Optional form data for filling forms (field_name: value)
        """
        self.url = url
        self.output_path = output_path
        self.max_actions = max_actions
        self.browser_path = browser_path
        self.open_report = open_report
        self.form_data = form_data or {}

        # Initialize components
        self.browser: Optional[BrowserLauncher] = None
        self.keyboard: Optional[KeyboardController] = None
        self.memory: Optional[AgentMemory] = None
        self.decision_engine: Optional[DecisionEngine] = None
        self.action_logger: Optional[ActionLogger] = None
        self.correlator: Optional[FeedbackCorrelator] = None
        self.validator: Optional[WCAGValidator] = None
        self.generator: Optional[HTMLGenerator] = None
        self.nvda_monitor: Optional[NVDAOutputMonitor] = None

        # Runtime state
        self.is_running = False
        self.start_time: Optional[datetime] = None
        self.nvda_log_path: Optional[Path] = None

    def setup(self) -> bool:
        """
        Set up all components for testing.

        Returns:
            True if setup successful, False otherwise
        """
        try:
            logger.info("Setting up accessibility test environment...")

            # Initialize browser launcher
            self.browser = BrowserLauncher(browser_path=self.browser_path)
            logger.info(f"Browser initialized: {self.browser.get_browser_info()}")

            # Initialize keyboard controller
            self.keyboard = KeyboardController(delay=0.1)
            logger.info("Keyboard controller initialized")

            # Initialize agent memory
            self.memory = AgentMemory(max_history=1000)
            logger.info("Agent memory initialized")

            # Initialize decision engine
            self.decision_engine = DecisionEngine(
                initial_strategy=NavigationStrategy.HEADINGS_FIRST,
                max_actions=self.max_actions
            )
            logger.info(f"Decision engine initialized (max_actions={self.max_actions})")

            # Initialize correlation components
            self.action_logger = ActionLogger(max_history=1000)
            self.correlator = FeedbackCorrelator(
                action_logger=self.action_logger,
                correlation_timeout=2.0,
                max_history=1000
            )
            logger.info("Correlation components initialized")

            # Initialize WCAG validator
            self.validator = WCAGValidator(page_url=self.url)
            logger.info("WCAG validator initialized")

            # Initialize HTML generator
            self.generator = HTMLGenerator()
            logger.info("HTML report generator initialized")

            # Initialize NVDA monitor
            self.nvda_log_path = get_nvda_log_path()
            if self.nvda_log_path:
                try:
                    self.nvda_monitor = NVDAOutputMonitor(
                        log_path=self.nvda_log_path,
                        correlation_timeout=2.0,
                        poll_interval=0.1
                    )
                    logger.info(f"NVDA monitor initialized (log: {self.nvda_log_path})")
                except Exception as e:
                    logger.warning(f"Failed to initialize NVDA monitor: {e}")
                    logger.warning("Will use simulated mode instead")
                    self.nvda_monitor = None
            else:
                logger.warning("NVDA not detected - running in simulated mode")
                logger.warning("Install and run NVDA with debug logging for full functionality")
                self.nvda_monitor = None

            return True

        except Exception as e:
            logger.error(f"Setup failed: {e}", exc_info=True)
            return False

    def launch_browser(self) -> bool:
        """
        Launch browser with target URL.

        Returns:
            True if launch successful, False otherwise
        """
        try:
            logger.info(f"Launching browser with URL: {self.url}")

            success = self.browser.launch_url(self.url, new_window=True)

            if success:
                logger.info("Browser launched successfully")
                # Give page time to load
                import time
                time.sleep(3)
                return True
            else:
                logger.error("Failed to launch browser")
                return False

        except Exception as e:
            logger.error(f"Browser launch failed: {e}", exc_info=True)
            return False

    def run_exploration(self) -> bool:
        """
        Run agent exploration of the page.

        Uses real NVDA monitoring if available, otherwise falls back to simulation.

        Real NVDA mode:
        1. Monitors NVDA log file in real-time
        2. Correlates keyboard actions with screen reader output
        3. Detects unlabeled form fields, missing alt text, etc.
        4. Builds navigation memory from actual NVDA announcements

        Simulated mode (fallback):
        1. Simulates basic navigation without NVDA
        2. Limited issue detection
        3. Used when NVDA is not installed/running

        Returns:
            True if exploration completed, False if error
        """
        try:
            logger.info("Starting page exploration...")

            # Check if form filling mode is enabled
            if self.form_data:
                logger.info(f"Form filling mode enabled with {len(self.form_data)} fields")
                logger.info(f"Form data: {list(self.form_data.keys())}")

            # Determine mode
            if self.nvda_monitor:
                logger.info("Running in REAL NVDA mode - reading screen reader output")
                return self._run_nvda_exploration()
            else:
                logger.info("Running in SIMULATED mode - NVDA not available")
                return self._run_simulated_exploration()

        except Exception as e:
            logger.error(f"Exploration failed: {e}", exc_info=True)
            self.decision_engine.set_state(AgentState.ERROR)
            return False

    def _run_nvda_exploration(self) -> bool:
        """
        Run exploration with real NVDA monitoring.

        Returns:
            True if successful, False otherwise
        """
        try:
            self.decision_engine.set_state(AgentState.EXPLORING)

            # Start monitoring NVDA log
            self.nvda_monitor.start()
            logger.info("NVDA monitoring started")

            # Give NVDA a moment to start producing output
            time.sleep(0.5)

            # Track filled fields for form filling mode
            filled_fields = []

            # Exploration loop
            for i in range(self.max_actions):
                # Press Tab to navigate to next element
                logger.info(f"Action {i+1}/{self.max_actions}: Pressing Tab")
                action_timestamp = datetime.now()
                self.keyboard.press_tab()

                # Wait for NVDA to announce the element and get the speech output
                nvda_speech = self.nvda_monitor.get_output_after(
                    timestamp=action_timestamp,
                    timeout=2.0
                )

                if nvda_speech:
                    nvda_text = nvda_speech.full_text
                    logger.info(f"  NVDA says: '{nvda_text}'")

                    # Log the action
                    self.action_logger.log_action(
                        key="Tab",
                        modifiers=[],
                        context=f"Navigating to element {i}"
                    )

                    # Add correlation with NVDA output
                    self.correlator.add_nvda_output(
                        nvda_text=nvda_text,
                        timestamp=datetime.now()
                    )

                    # Add to agent memory
                    self.memory.add_element(
                        nvda_text=nvda_text,
                        key_used="Tab",
                        element_id=f"elem_{i}",
                        is_interactive=self._is_interactive_element(nvda_text)
                    )

                    # Form filling logic
                    if self.form_data and self._is_form_field(nvda_text):
                        field_name = self._extract_field_name(nvda_text)
                        if field_name and field_name in self.form_data and field_name not in filled_fields:
                            value = self.form_data[field_name]
                            logger.info(f"  → Filling '{field_name}' with '{value}'")
                            self.keyboard.type_text(str(value))
                            filled_fields.append(field_name)
                            time.sleep(0.2)
                else:
                    logger.warning(f"  No NVDA output detected (potential unlabeled element!)")
                    # Still log the action even if no speech
                    self.action_logger.log_action(
                        key="Tab",
                        modifiers=[],
                        context=f"Silent element {i}"
                    )

                    # Add to memory with warning
                    self.memory.add_element(
                        nvda_text="[SILENT - No NVDA output]",
                        key_used="Tab",
                        element_id=f"elem_{i}",
                        is_interactive=False
                    )

                # Check if max actions reached
                self.decision_engine.increment_actions()
                if self.decision_engine.has_reached_max_actions():
                    logger.info("Reached maximum actions, stopping exploration")
                    break

            # Stop monitoring
            self.nvda_monitor.stop()
            logger.info("NVDA monitoring stopped")

            # Report filled fields
            if filled_fields:
                logger.info(f"Form filling completed. Filled {len(filled_fields)} fields: {filled_fields}")

            self.decision_engine.set_state(AgentState.COMPLETED)
            logger.info(f"Exploration completed. Visited {self.memory.count_visits()} elements")
            return True

        except Exception as e:
            logger.error(f"NVDA exploration failed: {e}", exc_info=True)
            if self.nvda_monitor:
                try:
                    self.nvda_monitor.stop()
                except:
                    pass
            return False

    def _run_simulated_exploration(self) -> bool:
        """
        Run exploration in simulated mode (fallback when NVDA not available).

        Returns:
            True if successful, False otherwise
        """
        try:
            self.decision_engine.set_state(AgentState.EXPLORING)

            # Simulate basic exploration for demonstration
            # In production, this would be driven by the Pydantic AI agent

            # Track filled fields for form filling mode
            filled_fields = []

            # Example: Press Tab a few times to explore
            for i in range(min(10, self.max_actions)):
                # Get decision from engine
                decision = self.decision_engine.decide_next_action(
                    nvda_output=f"Element {i}",  # Would come from NVDA
                    is_circular=False
                )

                logger.info(f"Action {i+1}: {decision.action} - {decision.reasoning}")

                # Execute action
                if decision.action.value == "Tab":
                    self.keyboard.press_tab()
                elif decision.action.value == "h":
                    from src.automation.keyboard_controller import NVDAKey
                    self.keyboard.press_nvda_key(NVDAKey.NEXT_HEADING)
                elif decision.action.value == "k":
                    from src.automation.keyboard_controller import NVDAKey
                    self.keyboard.press_nvda_key(NVDAKey.NEXT_LINK)

                # Log action
                logged_action = self.action_logger.log_action(
                    key=decision.action.value,
                    modifiers=[],
                    context=decision.reasoning
                )

                # Simulate NVDA output correlation
                # In production, this would come from real NVDA monitoring
                simulated_nvda_text = f"Simulated output for element {i}"

                # Form filling logic (simplified for demonstration)
                if self.form_data and i % 3 == 1:  # Simulate encountering form fields
                    # Try to match field name with form data
                    for field_name, field_value in self.form_data.items():
                        if field_name not in filled_fields:
                            logger.info(f"  → Filling form field '{field_name}' with '{field_value}'")
                            # Type the value
                            self.keyboard.type_text(str(field_value))
                            filled_fields.append(field_name)
                            simulated_nvda_text = f"Edit field: {field_name}, filled with {field_value}"
                            # Press Tab to move to next field
                            import time
                            time.sleep(0.1)
                            self.keyboard.press_tab()
                            break

                # Add to memory
                self.memory.add_element(
                    nvda_text=simulated_nvda_text,
                    key_used=decision.action.value,
                    element_id=f"elem_{i}",
                    is_interactive=(i % 2 == 0)  # Every other element
                )

                # Increment action counter
                self.decision_engine.increment_actions()

                # Check if max actions reached
                if self.decision_engine.has_reached_max_actions():
                    logger.info("Reached maximum actions, stopping exploration")
                    break

                # Small delay between actions
                import time
                time.sleep(0.2)

            # Report filled fields
            if filled_fields:
                logger.info(f"Form filling completed. Filled {len(filled_fields)} fields: {filled_fields}")

            self.decision_engine.set_state(AgentState.COMPLETED)
            logger.info(f"Exploration completed. Visited {self.memory.count_visits()} elements")

            return True

        except Exception as e:
            logger.error(f"Exploration failed: {e}", exc_info=True)
            self.decision_engine.set_state(AgentState.ERROR)
            return False

    def _is_interactive_element(self, nvda_text: str) -> bool:
        """
        Determine if NVDA output indicates an interactive element.

        Args:
            nvda_text: Text announced by NVDA

        Returns:
            True if element appears interactive, False otherwise
        """
        interactive_keywords = [
            "button", "link", "edit", "checkbox", "radio",
            "combo box", "list box", "menu", "tab", "clickable"
        ]
        nvda_lower = nvda_text.lower()
        return any(keyword in nvda_lower for keyword in interactive_keywords)

    def _is_form_field(self, nvda_text: str) -> bool:
        """
        Determine if NVDA output indicates a form field.

        Args:
            nvda_text: Text announced by NVDA

        Returns:
            True if element is a form field, False otherwise
        """
        form_keywords = ["edit", "combo box", "text area", "password"]
        nvda_lower = nvda_text.lower()
        return any(keyword in nvda_lower for keyword in form_keywords)

    def _extract_field_name(self, nvda_text: str) -> Optional[str]:
        """
        Extract field name from NVDA output.

        Examples:
        - "Name edit" -> "name"
        - "Email address edit" -> "email"
        - "Message text area" -> "message"

        Args:
            nvda_text: Text announced by NVDA

        Returns:
            Extracted field name, or None if cannot determine
        """
        # Simple heuristic: take the first word before "edit", "combo box", etc.
        nvda_lower = nvda_text.lower()

        # Remove common suffixes
        for suffix in [" edit", " combo box", " text area", " password"]:
            if suffix in nvda_lower:
                field_name = nvda_lower.replace(suffix, "").strip()
                # Take first word or full phrase
                return field_name.split()[0] if field_name else None

        return None

    def run_validation(self) -> bool:
        """
        Run WCAG validation on collected data.

        Returns:
            True if validation completed, False if error
        """
        try:
            logger.info("Running WCAG validation...")

            # Get correlation events (in production, would have real events)
            correlation_events = self.correlator.get_all_events()

            # Run validation
            self.validation_report = self.validator.validate(
                agent_memory=self.memory,
                correlation_events=correlation_events
            )

            logger.info(f"Validation completed. Found {self.validation_report.total_issues} issues:")
            logger.info(f"  Critical: {self.validation_report.issues_by_severity.get('critical', 0)}")
            logger.info(f"  High: {self.validation_report.issues_by_severity.get('high', 0)}")
            logger.info(f"  Medium: {self.validation_report.issues_by_severity.get('medium', 0)}")
            logger.info(f"  Low: {self.validation_report.issues_by_severity.get('low', 0)}")

            return True

        except Exception as e:
            logger.error(f"Validation failed: {e}", exc_info=True)
            return False

    def generate_report(self) -> bool:
        """
        Generate HTML accessibility report.

        Returns:
            True if report generated, False if error
        """
        try:
            logger.info(f"Generating HTML report: {self.output_path}")

            output_file = self.generator.generate_report(
                validation_report=self.validation_report,
                output_path=self.output_path
            )

            logger.info(f"Report generated successfully: {output_file}")

            # Show summary
            print("\n" + "="*80)
            print(self.validation_report.get_summary())
            print("="*80)
            print(f"\nHTML Report: {output_file}")

            # Auto-open report if flag is set
            if self.open_report:
                logger.info("Opening report in default browser...")
                try:
                    # Convert to absolute path for browser
                    abs_path = Path(output_file).absolute()
                    webbrowser.open(f"file:///{abs_path}")
                    print("[OK] Report opened in browser")
                except Exception as e:
                    logger.warning(f"Failed to auto-open report: {e}")
                    print(f"[WARNING] Could not auto-open report, please open manually: {output_file}")

            return True

        except Exception as e:
            logger.error(f"Report generation failed: {e}", exc_info=True)
            return False

    def cleanup(self):
        """Clean up resources and close browser."""
        try:
            logger.info("Cleaning up...")

            # Stop NVDA monitoring if running
            if self.nvda_monitor:
                try:
                    self.nvda_monitor.stop()
                    logger.info("NVDA monitoring stopped")
                except Exception as e:
                    logger.warning(f"Error stopping NVDA monitor: {e}")

            # Note: BrowserLauncher doesn't have close functionality yet
            # In production, would close browser window

            if self.memory:
                self.memory.clear()

            if self.action_logger:
                self.action_logger.clear()

            if self.correlator:
                self.correlator.clear()

            logger.info("Cleanup completed")

        except Exception as e:
            logger.error(f"Cleanup error: {e}", exc_info=True)

    def run(self) -> int:
        """
        Run the complete accessibility testing workflow.

        Returns:
            Exit code (0=success, 1=issues found, 2=error)
        """
        self.is_running = True
        self.start_time = datetime.now()

        try:
            # Setup
            if not self.setup():
                logger.error("Setup failed")
                return EXIT_ERROR

            # Launch browser
            if not self.launch_browser():
                logger.error("Browser launch failed")
                return EXIT_ERROR

            # Run exploration
            if not self.run_exploration():
                logger.error("Exploration failed")
                return EXIT_ERROR

            # Run validation
            if not self.run_validation():
                logger.error("Validation failed")
                return EXIT_ERROR

            # Generate report
            if not self.generate_report():
                logger.error("Report generation failed")
                return EXIT_ERROR

            # Determine exit code based on issues found
            if self.validation_report.total_issues == 0:
                logger.info("No accessibility issues found!")
                return EXIT_SUCCESS
            else:
                # Check for critical issues
                critical_count = self.validation_report.issues_by_severity.get('critical', 0)
                high_count = self.validation_report.issues_by_severity.get('high', 0)

                if critical_count > 0 or high_count > 0:
                    logger.warning(f"Found {critical_count} critical and {high_count} high severity issues")

                return EXIT_ISSUES_FOUND

        except KeyboardInterrupt:
            logger.warning("Testing interrupted by user")
            return EXIT_ERROR

        except Exception as e:
            logger.error(f"Unexpected error: {e}", exc_info=True)
            return EXIT_ERROR

        finally:
            self.is_running = False
            self.cleanup()


def parse_form_data(fill_forms_arg: Optional[str]) -> Dict[str, Any]:
    """
    Parse form data from JSON string or file path.

    Args:
        fill_forms_arg: JSON string or file path

    Returns:
        Dictionary of form field names to values
    """
    if not fill_forms_arg:
        return {}

    try:
        # First, try to parse as JSON string
        try:
            form_data = json.loads(fill_forms_arg)
            logger.info(f"Parsed form data from JSON string: {list(form_data.keys())}")
            return form_data
        except json.JSONDecodeError:
            # If that fails, try to read as file path
            file_path = Path(fill_forms_arg)
            if file_path.exists() and file_path.is_file():
                with open(file_path, 'r', encoding='utf-8') as f:
                    form_data = json.load(f)
                logger.info(f"Loaded form data from file '{file_path}': {list(form_data.keys())}")
                return form_data
            else:
                logger.error(f"Invalid form data: not valid JSON and file not found: {fill_forms_arg}")
                return {}

    except Exception as e:
        logger.error(f"Failed to parse form data: {e}")
        return {}


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Agentic Accessibility Testing - Test websites for WCAG compliance using AI and screen readers",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Test a website and save report
  python -m src.main --url https://example.com --output reports/example.html

  # Test and auto-open report in browser
  python -m src.main --url https://example.com --open-report

  # Fill forms with data (JSON string)
  python -m src.main --url https://example.com --fill-forms '{"name": "John Doe", "email": "john@example.com"}'

  # Fill forms with data from file
  python -m src.main --url https://example.com --fill-forms form_data.json

  # Test with custom browser and auto-open report
  python -m src.main --url https://example.com --browser "C:\\Program Files\\Firefox\\firefox.exe" --open-report

  # Complete example with all options
  python -m src.main --url https://example.com --output report.html --max-actions 50 --fill-forms '{"username": "test", "password": "demo123"}' --open-report --verbose

Exit Codes:
  0 - No accessibility issues found
  1 - Accessibility issues detected
  2 - Error during testing
        """
    )

    parser.add_argument(
        '--url',
        required=True,
        help='Target URL to test for accessibility (required)'
    )

    parser.add_argument(
        '--output',
        '-o',
        default='reports/accessibility_report.html',
        help='Output path for HTML report (default: reports/accessibility_report.html)'
    )

    parser.add_argument(
        '--max-actions',
        type=int,
        default=100,
        help='Maximum number of agent actions before stopping (default: 100)'
    )

    parser.add_argument(
        '--browser',
        help='Path to browser executable (optional, auto-detects if not provided)'
    )

    parser.add_argument(
        '--verbose',
        '-v',
        action='store_true',
        help='Enable verbose logging'
    )

    parser.add_argument(
        '--config',
        help='Path to custom configuration file (not yet implemented)'
    )

    parser.add_argument(
        '--open-report',
        action='store_true',
        help='Automatically open the HTML report in the default browser after generation'
    )

    parser.add_argument(
        '--fill-forms',
        help='JSON string or file path with form data to fill (e.g., \'{"name": "John", "email": "john@example.com"}\')'
    )

    return parser.parse_args()


def setup_signal_handlers(runner):
    """Set up signal handlers for graceful shutdown."""
    def signal_handler(signum, frame):
        logger.warning(f"Received signal {signum}, shutting down gracefully...")
        if runner and runner.is_running:
            runner.cleanup()
        sys.exit(EXIT_ERROR)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)


def main():
    """Main entry point."""
    # Parse arguments
    args = parse_arguments()

    # Configure logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Verbose logging enabled")

    # Parse form data if provided
    form_data = parse_form_data(args.fill_forms)

    # Display banner
    print("="*80)
    print("  Agentic Accessibility Testing Environment")
    print("  AI-Powered WCAG Compliance Testing with Screen Readers")
    print("="*80)
    print(f"\nTarget URL: {args.url}")
    print(f"Output Report: {args.output}")
    print(f"Max Actions: {args.max_actions}")
    if args.open_report:
        print(f"Auto-open Report: Yes")
    if form_data:
        print(f"Form Filling: Enabled ({len(form_data)} fields)")
    print()

    # Create test runner
    runner = AccessibilityTestRunner(
        url=args.url,
        output_path=args.output,
        max_actions=args.max_actions,
        browser_path=args.browser,
        open_report=args.open_report,
        form_data=form_data
    )

    # Set up signal handlers
    setup_signal_handlers(runner)

    # Run tests
    exit_code = runner.run()

    # Exit with appropriate code
    sys.exit(exit_code)


if __name__ == '__main__':
    main()
