"""Test script for Ollama integration with AccessibilityAgent.

This script verifies that the Ollama LLM provider integration works correctly.

Prerequisites:
1. Ollama server running locally (ollama serve)
2. A model pulled (e.g., ollama pull llama3.2)
3. Python environment with ollama package installed

Usage:
    python test_ollama.py
"""

import logging
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.agent.accessibility_agent import AccessibilityAgent
from src.automation.keyboard_controller import KeyboardController
from src.agent.decision_engine import DecisionEngine
from src.agent.memory import AgentMemory
from src.correlation.action_logger import ActionLogger
from src.correlation.correlator import FeedbackCorrelator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_ollama_connection():
    """Test if Ollama server is accessible."""
    import httpx

    print("\n" + "="*60)
    print("TEST 1: Ollama Server Connection")
    print("="*60)

    try:
        response = httpx.get("http://localhost:11434/api/tags", timeout=5.0)
        if response.status_code == 200:
            models = response.json().get("models", [])
            print(f"✓ Ollama server is running")
            print(f"✓ Available models: {len(models)}")
            for model in models:
                print(f"  - {model['name']}")
            return True, models
        else:
            print(f"✗ Ollama server returned status code: {response.status_code}")
            return False, []
    except Exception as e:
        print(f"✗ Cannot connect to Ollama server: {e}")
        print("\nPlease ensure:")
        print("  1. Ollama is installed (https://ollama.com)")
        print("  2. Ollama server is running: ollama serve")
        print("  3. At least one model is pulled: ollama pull llama3.2")
        return False, []


def test_agent_initialization_ollama():
    """Test AccessibilityAgent initialization with Ollama."""
    print("\n" + "="*60)
    print("TEST 2: AccessibilityAgent with Ollama")
    print("="*60)

    try:
        # Initialize agent with Ollama provider
        agent = AccessibilityAgent(
            keyboard_controller=KeyboardController(),
            decision_engine=DecisionEngine(),
            memory=AgentMemory(),
            action_logger=ActionLogger(),
            model="llama3.2",  # or whatever model is available
            provider="ollama",
            ollama_base_url="http://localhost:11434/v1"
        )
        print("✓ AccessibilityAgent initialized with Ollama")
        print(f"✓ Agent instance created: {type(agent).__name__}")
        print(f"✓ Pydantic AI agent created: {type(agent.agent).__name__}")
        return True
    except Exception as e:
        print(f"✗ Failed to initialize agent: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_agent_initialization_openai():
    """Test AccessibilityAgent initialization with OpenAI (if API key available)."""
    import os

    print("\n" + "="*60)
    print("TEST 3: AccessibilityAgent with OpenAI (optional)")
    print("="*60)

    if not os.getenv("OPENAI_API_KEY"):
        print("⊘ Skipped - OPENAI_API_KEY not set")
        return True

    try:
        agent = AccessibilityAgent(
            keyboard_controller=KeyboardController(),
            decision_engine=DecisionEngine(),
            memory=AgentMemory(),
            action_logger=ActionLogger(),
            model="openai:gpt-4",
            provider="openai"
        )
        print("✓ AccessibilityAgent initialized with OpenAI")
        return True
    except Exception as e:
        print(f"✗ Failed to initialize agent: {e}")
        return False


def test_config_loading():
    """Test config loading with Ollama settings."""
    print("\n" + "="*60)
    print("TEST 4: Config Loading with Ollama Settings")
    print("="*60)

    try:
        from src.utils.config import load_config

        # Temporarily set provider to ollama to skip OpenAI API key check
        import os
        os.environ["LLM_PROVIDER"] = "ollama"

        settings = load_config()
        print("✓ Config loaded successfully")
        print(f"✓ Provider: {settings.agent.provider}")
        print(f"✓ Model: {settings.agent.model}")
        print(f"✓ Ollama base URL: {settings.agent.ollama.base_url}")
        print(f"✓ Ollama default model: {settings.agent.ollama.default_model}")

        # Clean up
        del os.environ["LLM_PROVIDER"]

        return True
    except Exception as e:
        print(f"✗ Failed to load config: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all Ollama integration tests."""
    print("\n" + "="*70)
    print(" "*15 + "OLLAMA INTEGRATION TEST SUITE")
    print("="*70)
    print("\nThis script tests the Ollama LLM integration for AccessibilityAgent.")
    print()

    all_passed = True

    # Test 1: Ollama server connection
    ollama_ok, models = test_ollama_connection()
    if not ollama_ok:
        print("\n❌ Cannot proceed without Ollama server. Please start it first.")
        return False

    # Test 2: Agent initialization with Ollama
    if not test_agent_initialization_ollama():
        all_passed = False

    # Test 3: Agent initialization with OpenAI (optional)
    if not test_agent_initialization_openai():
        all_passed = False

    # Test 4: Config loading
    if not test_config_loading():
        all_passed = False

    # Summary
    print("\n" + "="*70)
    if all_passed:
        print("✅ ALL TESTS PASSED")
        print("\nThe Ollama integration is working correctly!")
        print("\nNext steps:")
        print("  1. Update your .env to set LLM_PROVIDER=ollama")
        print("  2. Update settings.yaml to configure your preferred model")
        print("  3. Run the accessibility agent with Ollama for local, private testing")
    else:
        print("❌ SOME TESTS FAILED")
        print("\nPlease review the errors above and fix any issues.")
    print("="*70)

    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
