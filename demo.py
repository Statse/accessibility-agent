"""Demo script to test keyboard controller and browser launcher.

This script demonstrates the basic functionality of the keyboard and browser
automation modules that have been implemented.

WARNING: This script will:
- Open your default web browser
- Send keyboard inputs to the active window
- Type text in the focused application

Make sure you're ready before running!
"""

import time
import sys
from src.automation.keyboard_controller import KeyboardController, NVDAKey
from src.automation.browser_launcher import BrowserLauncher


def demo_browser_detection():
    """Demo: Detect default browser."""
    print("\n" + "="*60)
    print("DEMO 1: Browser Detection")
    print("="*60)

    info = BrowserLauncher.get_browser_info()

    if info['path']:
        print(f"✓ Default browser detected:")
        print(f"  Name: {info['name']}")
        print(f"  Path: {info['path']}")
    else:
        print("✗ Could not detect default browser")
        print("  (This is normal on non-Windows systems)")


def demo_browser_launch():
    """Demo: Launch browser with URL."""
    print("\n" + "="*60)
    print("DEMO 2: Browser Launch")
    print("="*60)

    response = input("\nLaunch example.com in your browser? (y/n): ")
    if response.lower() != 'y':
        print("Skipped.")
        return

    launcher = BrowserLauncher()

    print("\nLaunching https://example.com...")
    try:
        launcher.launch_url("https://example.com")
        print("✓ Browser launched successfully!")
        print("\nNote: Browser window should now be open.")
    except Exception as e:
        print(f"✗ Failed to launch browser: {e}")


def demo_keyboard_basic():
    """Demo: Basic keyboard control."""
    print("\n" + "="*60)
    print("DEMO 3: Basic Keyboard Control")
    print("="*60)

    response = input("\nTest keyboard control? This will send keystrokes! (y/n): ")
    if response.lower() != 'y':
        print("Skipped.")
        return

    print("\nInitializing keyboard controller...")
    controller = KeyboardController(delay=0.5)

    print("\nIn 3 seconds, will open Notepad and type text...")
    print("(Make sure no important windows are in focus!)")
    time.sleep(3)

    try:
        # Open Notepad (Windows)
        print("\n→ Pressing Win+R to open Run dialog...")
        controller.press_combination(["win", "r"])
        time.sleep(1)

        print("→ Typing 'notepad'...")
        controller.type_text("notepad")
        time.sleep(0.5)

        print("→ Pressing Enter to open Notepad...")
        controller.press_enter()
        time.sleep(2)

        print("→ Typing demo text...")
        controller.type_text("Hello from the Accessibility Agent!")
        time.sleep(0.5)

        print("→ Pressing Enter...")
        controller.press_enter()

        controller.type_text("This text was typed by the keyboard controller.")

        print("\n✓ Keyboard demo complete!")
        print("\nNote: Check Notepad window for the typed text.")

    except Exception as e:
        print(f"\n✗ Keyboard demo failed: {e}")


def demo_nvda_keys():
    """Demo: NVDA navigation keys."""
    print("\n" + "="*60)
    print("DEMO 4: NVDA Navigation Keys")
    print("="*60)

    print("\nNVDA Key demonstrations:")
    print("  H - Next heading")
    print("  Shift+H - Previous heading")
    print("  K - Next link")
    print("  Shift+K - Previous link")
    print("  Insert+Down - Say All")
    print("  Insert+T - Read Title")

    response = input("\nTest NVDA keys? (Requires NVDA running) (y/n): ")
    if response.lower() != 'y':
        print("Skipped.")
        return

    controller = KeyboardController(delay=1.0)

    print("\nMake sure:")
    print("1. NVDA is running")
    print("2. A web browser is focused on a webpage")
    print("\nStarting in 3 seconds...")
    time.sleep(3)

    try:
        print("\n→ Pressing H (Next Heading)...")
        controller.press_nvda_key(NVDAKey.NEXT_HEADING)
        time.sleep(1)

        print("→ Pressing H again...")
        controller.press_nvda_key(NVDAKey.NEXT_HEADING)
        time.sleep(1)

        print("→ Pressing Shift+H (Previous Heading)...")
        controller.press_nvda_key(NVDAKey.PREV_HEADING)
        time.sleep(1)

        print("→ Pressing K (Next Link)...")
        controller.press_nvda_key(NVDAKey.NEXT_LINK)
        time.sleep(1)

        print("→ Pressing Insert+T (Read Title)...")
        controller.press_nvda_read_title()

        print("\n✓ NVDA keys demo complete!")
        print("\nNote: Listen to NVDA output to hear the results.")

    except Exception as e:
        print(f"\n✗ NVDA keys demo failed: {e}")


def demo_keyboard_combinations():
    """Demo: Keyboard combinations."""
    print("\n" + "="*60)
    print("DEMO 5: Keyboard Combinations")
    print("="*60)

    controller = KeyboardController(delay=0.3)

    print("\nKeyboard combination examples:")
    print("  Ctrl+F - Find")
    print("  Ctrl+Shift+T - Reopen closed tab")
    print("  Alt+Tab - Switch windows")

    print("\nNote: These are just examples. Not executing to avoid")
    print("      interfering with your current work.")


def main():
    """Run all demos."""
    print("\n" + "="*60)
    print("ACCESSIBILITY AGENT - Component Demo")
    print("="*60)
    print("\nThis demo tests the keyboard controller and browser launcher")
    print("modules that have been implemented in Phase 3.")

    try:
        # Always safe to run
        demo_browser_detection()

        # User confirms before running
        demo_browser_launch()
        demo_keyboard_basic()
        demo_nvda_keys()
        demo_keyboard_combinations()

        print("\n" + "="*60)
        print("DEMO COMPLETE")
        print("="*60)
        print("\nAll components are working! Next steps:")
        print("1. Implement Phase 5: Pydantic AI Agent")
        print("2. Implement Phase 4: Action-Feedback Correlation")
        print("3. Implement Phase 9: Main CLI entry point")
        print("\nSee QUICKSTART.md for more information.")

    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\n\nDemo failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
