"""Safe component test script - no keyboard output.

This script safely tests that all components can be imported and initialized
without actually sending any keystrokes or opening browsers.

Safe to run anytime!
"""

import sys
import os

# Set UTF-8 encoding for Windows console
if os.name == 'nt':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


def test_imports():
    """Test that all modules can be imported."""
    print("Testing imports...")

    try:
        from src.automation.keyboard_controller import KeyboardController, NVDAKey
        print("  ✓ keyboard_controller imported")
    except ImportError as e:
        print(f"  ✗ Failed to import keyboard_controller: {e}")
        return False

    try:
        from src.automation.browser_launcher import BrowserLauncher, BrowserLaunchError
        print("  ✓ browser_launcher imported")
    except ImportError as e:
        print(f"  ✗ Failed to import browser_launcher: {e}")
        return False

    try:
        from src.screen_reader.nvda_parser import NVDALogParser
        print("  ✓ nvda_parser imported")
    except ImportError as e:
        print(f"  ✗ Failed to import nvda_parser: {e}")
        return False

    try:
        from src.screen_reader.output_monitor import NVDAOutputMonitor
        print("  ✓ output_monitor imported")
    except ImportError as e:
        print(f"  ✗ Failed to import output_monitor: {e}")
        return False

    try:
        from src.utils.logger import get_logger
        print("  ✓ logger imported")
    except ImportError as e:
        print(f"  ✗ Failed to import logger: {e}")
        return False

    try:
        from src.utils.config import get_settings
        print("  ✓ config imported")
    except ImportError as e:
        print(f"  ✗ Failed to import config: {e}")
        return False

    return True


def test_keyboard_controller():
    """Test keyboard controller initialization."""
    print("\nTesting KeyboardController...")

    from src.automation.keyboard_controller import KeyboardController, NVDAKey

    try:
        controller = KeyboardController(delay=0.1)
        print(f"  ✓ Controller initialized with delay={controller.delay}s")
    except Exception as e:
        print(f"  ✗ Failed to initialize controller: {e}")
        return False

    try:
        controller.set_delay(0.5)
        print(f"  ✓ Delay updated to {controller.delay}s")
    except Exception as e:
        print(f"  ✗ Failed to set delay: {e}")
        return False

    # Test NVDAKey enum
    try:
        assert NVDAKey.NEXT_HEADING.value == "h"
        assert NVDAKey.PREV_HEADING.value == "H"
        assert NVDAKey.NEXT_LINK.value == "k"
        print("  ✓ NVDAKey enum values correct")
    except AssertionError as e:
        print(f"  ✗ NVDAKey enum values incorrect: {e}")
        return False

    return True


def test_browser_launcher():
    """Test browser launcher initialization."""
    print("\nTesting BrowserLauncher...")

    from src.automation.browser_launcher import BrowserLauncher

    try:
        launcher = BrowserLauncher()
        print("  ✓ Launcher initialized (no explicit path)")
    except Exception as e:
        print(f"  ✗ Failed to initialize launcher: {e}")
        return False

    # Test browser detection
    try:
        info = BrowserLauncher.get_browser_info()
        if info['path']:
            print(f"  ✓ Browser detected: {info['name']} at {info['path']}")
        else:
            print("  ℹ No browser detected (may not be on Windows)")
    except Exception as e:
        print(f"  ✗ Browser detection failed: {e}")
        return False

    return True


def test_logger():
    """Test logger setup."""
    print("\nTesting Logger...")

    from src.utils.logger import get_logger

    try:
        logger = get_logger("test_logger")
        print("  ✓ Logger created successfully")

        logger.info("Test log message")
        print("  ✓ Logger can write messages")
    except Exception as e:
        print(f"  ✗ Logger test failed: {e}")
        return False

    return True


def test_config():
    """Test config loading."""
    print("\nTesting Config...")

    from src.utils.config import get_settings

    try:
        settings = get_settings()
        print("  ✓ Settings loaded")

        # Check some expected settings
        if hasattr(settings, 'keyboard'):
            print(f"  ✓ Keyboard settings present")
            if hasattr(settings.keyboard, 'delay_between_keys'):
                print(f"    - delay_between_keys: {settings.keyboard.delay_between_keys}s")

        if hasattr(settings, 'nvda'):
            print(f"  ✓ NVDA settings present")
            if hasattr(settings.nvda, 'log_path'):
                print(f"    - log_path: {settings.nvda.log_path}")

        if hasattr(settings, 'browser'):
            print(f"  ✓ Browser settings present")

    except Exception as e:
        print(f"  ✗ Config test failed: {e}")
        return False

    return True


def main():
    """Run all component tests."""
    print("="*60)
    print("COMPONENT TEST - Safe Validation")
    print("="*60)
    print("\nThis script validates that all components can be")
    print("imported and initialized without sending any keystrokes.")
    print()

    all_passed = True

    # Run tests
    if not test_imports():
        all_passed = False

    if not test_keyboard_controller():
        all_passed = False

    if not test_browser_launcher():
        all_passed = False

    if not test_logger():
        all_passed = False

    if not test_config():
        all_passed = False

    # Summary
    print("\n" + "="*60)
    if all_passed:
        print("✓ ALL TESTS PASSED")
        print("="*60)
        print("\nAll components are working correctly!")
        print("\nNext steps:")
        print("1. Run 'pytest' to execute the full test suite")
        print("2. Run 'python demo.py' for interactive demo (sends keystrokes!)")
        print("3. See QUICKSTART.md for usage examples")
        return 0
    else:
        print("✗ SOME TESTS FAILED")
        print("="*60)
        print("\nPlease check the errors above.")
        print("\nCommon issues:")
        print("- Missing dependencies: pip install -r requirements.txt")
        print("- Not in virtual environment: venv\\Scripts\\activate")
        return 1


if __name__ == "__main__":
    sys.exit(main())
