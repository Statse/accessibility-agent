"""Unit tests for browser_launcher module."""

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, Mock, call, patch

import pytest

from src.automation.browser_launcher import (
    BrowserLaunchError,
    BrowserLauncher,
)


class TestBrowserLauncher:
    """Test suite for BrowserLauncher class."""

    @pytest.fixture
    def launcher(self):
        """Create a BrowserLauncher instance."""
        return BrowserLauncher()

    @pytest.fixture
    def mock_browser_path(self, tmp_path):
        """Create a mock browser executable path."""
        browser_exe = tmp_path / "browser.exe"
        browser_exe.touch()  # Create the file
        return str(browser_exe)

    def test_init_no_path(self, launcher):
        """Test initialization without explicit browser path."""
        assert launcher.browser_path is None

    def test_init_with_valid_path(self, mock_browser_path):
        """Test initialization with valid browser path."""
        launcher = BrowserLauncher(browser_path=mock_browser_path)
        assert launcher.browser_path == mock_browser_path

    def test_init_with_invalid_path_raises_error(self):
        """Test initialization with non-existent path raises error."""
        with pytest.raises(
            BrowserLaunchError, match="Browser not found at"
        ):
            BrowserLauncher(browser_path="C:\\NonExistent\\browser.exe")

    @patch("src.automation.browser_launcher.winreg")
    def test_get_default_browser_path_success(self, mock_winreg):
        """Test successful default browser detection."""
        # Mock registry keys and values
        mock_key_user_choice = MagicMock()
        mock_key_command = MagicMock()

        mock_winreg.OpenKey.side_effect = [
            mock_key_user_choice.__enter__.return_value,
            mock_key_command.__enter__.return_value,
        ]

        mock_winreg.QueryValueEx.side_effect = [
            ("ChromeHTML", None),  # ProgId
            ('"C:\\Program Files\\Chrome\\chrome.exe" -- "%1"', None),  # Command
        ]

        mock_winreg.HKEY_CURRENT_USER = "HKCU"
        mock_winreg.HKEY_CLASSES_ROOT = "HKCR"

        with patch("src.automation.browser_launcher.Path") as mock_path:
            mock_path.return_value.exists.return_value = True

            result = BrowserLauncher.get_default_browser_path()

            assert result == "C:\\Program Files\\Chrome\\chrome.exe"

    @patch("src.automation.browser_launcher.winreg")
    def test_get_default_browser_path_unquoted_command(self, mock_winreg):
        """Test browser detection with unquoted command path."""
        mock_key_user_choice = MagicMock()
        mock_key_command = MagicMock()

        mock_winreg.OpenKey.side_effect = [
            mock_key_user_choice.__enter__.return_value,
            mock_key_command.__enter__.return_value,
        ]

        mock_winreg.QueryValueEx.side_effect = [
            ("FirefoxURL", None),
            ("C:\\Program Files\\Firefox\\firefox.exe -url %1", None),
        ]

        mock_winreg.HKEY_CURRENT_USER = "HKCU"
        mock_winreg.HKEY_CLASSES_ROOT = "HKCR"

        with patch("src.automation.browser_launcher.Path") as mock_path:
            mock_path.return_value.exists.return_value = True

            result = BrowserLauncher.get_default_browser_path()

            assert result == "C:\\Program Files\\Firefox\\firefox.exe"

    @patch("src.automation.browser_launcher.winreg", None)
    def test_get_default_browser_path_no_winreg(self):
        """Test browser detection when winreg is not available (non-Windows)."""
        result = BrowserLauncher.get_default_browser_path()
        assert result is None

    @patch("src.automation.browser_launcher.winreg")
    def test_get_default_browser_path_registry_not_found(self, mock_winreg):
        """Test browser detection when registry key is not found."""
        mock_winreg.OpenKey.side_effect = FileNotFoundError("Key not found")
        mock_winreg.HKEY_CURRENT_USER = "HKCU"

        result = BrowserLauncher.get_default_browser_path()
        assert result is None

    @patch("src.automation.browser_launcher.winreg")
    def test_get_default_browser_path_browser_not_exists(self, mock_winreg):
        """Test browser detection when detected path doesn't exist."""
        mock_key_user_choice = MagicMock()
        mock_key_command = MagicMock()

        mock_winreg.OpenKey.side_effect = [
            mock_key_user_choice.__enter__.return_value,
            mock_key_command.__enter__.return_value,
        ]

        mock_winreg.QueryValueEx.side_effect = [
            ("ChromeHTML", None),
            ('"C:\\Nonexistent\\chrome.exe"', None),
        ]

        mock_winreg.HKEY_CURRENT_USER = "HKCU"
        mock_winreg.HKEY_CLASSES_ROOT = "HKCR"

        with patch("src.automation.browser_launcher.Path") as mock_path:
            mock_path.return_value.exists.return_value = False

            result = BrowserLauncher.get_default_browser_path()
            assert result is None

    def test_launch_url_empty_raises_error(self, launcher):
        """Test that launching empty URL raises error."""
        with pytest.raises(BrowserLaunchError, match="URL cannot be empty"):
            launcher.launch_url("")

    @patch("src.automation.browser_launcher.webbrowser")
    def test_launch_url_adds_https_prefix(self, mock_webbrowser, launcher):
        """Test that URLs without protocol get https:// prefix."""
        mock_webbrowser.open_new.return_value = True

        launcher.launch_url("example.com")

        mock_webbrowser.open_new.assert_called_once_with("https://example.com")

    @patch("src.automation.browser_launcher.webbrowser")
    def test_launch_url_with_protocol(self, mock_webbrowser, launcher):
        """Test launching URL that already has protocol."""
        mock_webbrowser.open_new.return_value = True

        launcher.launch_url("https://example.com")

        mock_webbrowser.open_new.assert_called_once_with("https://example.com")

    @patch("src.automation.browser_launcher.webbrowser")
    def test_launch_url_with_default_browser(self, mock_webbrowser, launcher):
        """Test launching URL with default browser (no explicit path)."""
        mock_webbrowser.open_new.return_value = True

        result = launcher.launch_url("https://example.com")

        assert result is True
        mock_webbrowser.open_new.assert_called_once()

    @patch("src.automation.browser_launcher.webbrowser")
    def test_launch_url_new_window_false(self, mock_webbrowser, launcher):
        """Test launching URL without forcing new window."""
        mock_webbrowser.open.return_value = True

        result = launcher.launch_url("https://example.com", new_window=False)

        assert result is True
        mock_webbrowser.open.assert_called_once_with("https://example.com")

    @patch("src.automation.browser_launcher.subprocess.Popen")
    def test_launch_url_with_explicit_chrome_path(self, mock_popen, mock_browser_path):
        """Test launching URL with explicit Chrome path."""
        chrome_path = mock_browser_path.replace("browser.exe", "chrome.exe")
        Path(chrome_path).touch()

        launcher = BrowserLauncher(browser_path=chrome_path)
        result = launcher.launch_url("https://example.com")

        assert result is True
        mock_popen.assert_called_once()

        # Check that chrome was launched with correct args
        call_args = mock_popen.call_args[0][0]
        assert chrome_path in call_args
        assert "--new-window" in call_args
        assert "https://example.com" in call_args

    @patch("src.automation.browser_launcher.subprocess.Popen")
    def test_launch_url_with_explicit_firefox_path(self, mock_popen, mock_browser_path):
        """Test launching URL with explicit Firefox path."""
        firefox_path = mock_browser_path.replace("browser.exe", "firefox.exe")
        Path(firefox_path).touch()

        launcher = BrowserLauncher(browser_path=firefox_path)
        result = launcher.launch_url("https://example.com")

        assert result is True
        mock_popen.assert_called_once()

        # Check that firefox was launched with correct args
        call_args = mock_popen.call_args[0][0]
        assert firefox_path in call_args
        assert "-new-window" in call_args

    @patch("src.automation.browser_launcher.subprocess.Popen")
    def test_launch_url_with_explicit_path_no_new_window(
        self, mock_popen, mock_browser_path
    ):
        """Test launching with explicit path without new window."""
        chrome_path = mock_browser_path.replace("browser.exe", "chrome.exe")
        Path(chrome_path).touch()

        launcher = BrowserLauncher(browser_path=chrome_path)
        result = launcher.launch_url("https://example.com", new_window=False)

        assert result is True
        mock_popen.assert_called_once()

        # Should not include --new-window flag
        call_args = mock_popen.call_args[0][0]
        assert "--new-window" not in call_args

    @patch("src.automation.browser_launcher.webbrowser")
    def test_launch_url_failure_raises_error(self, mock_webbrowser, launcher):
        """Test that launch failure raises BrowserLaunchError."""
        mock_webbrowser.open_new.side_effect = Exception("Browser error")

        with pytest.raises(BrowserLaunchError, match="Failed to launch URL"):
            launcher.launch_url("https://example.com")

    def test_close_browser_not_implemented(self, launcher):
        """Test that close_browser is a placeholder."""
        # Should not raise, but logs warning
        launcher.close_browser()

    @patch("src.automation.browser_launcher.BrowserLauncher.get_default_browser_path")
    def test_get_browser_info_chrome(self, mock_get_path):
        """Test browser info detection for Chrome."""
        mock_get_path.return_value = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"

        info = BrowserLauncher.get_browser_info()

        assert info["path"] == "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"
        assert info["name"] == "Chrome"
        assert info["version"] is None

    @patch("src.automation.browser_launcher.BrowserLauncher.get_default_browser_path")
    def test_get_browser_info_firefox(self, mock_get_path):
        """Test browser info detection for Firefox."""
        mock_get_path.return_value = "C:\\Program Files\\Mozilla Firefox\\firefox.exe"

        info = BrowserLauncher.get_browser_info()

        assert info["name"] == "Firefox"

    @patch("src.automation.browser_launcher.BrowserLauncher.get_default_browser_path")
    def test_get_browser_info_edge(self, mock_get_path):
        """Test browser info detection for Edge."""
        mock_get_path.return_value = "C:\\Program Files\\Microsoft\\Edge\\msedge.exe"

        info = BrowserLauncher.get_browser_info()

        assert info["name"] == "Edge"

    @patch("src.automation.browser_launcher.BrowserLauncher.get_default_browser_path")
    def test_get_browser_info_opera(self, mock_get_path):
        """Test browser info detection for Opera."""
        mock_get_path.return_value = "C:\\Program Files\\Opera\\launcher.exe"

        info = BrowserLauncher.get_browser_info()

        assert info["name"] == "Opera"

    @patch("src.automation.browser_launcher.BrowserLauncher.get_default_browser_path")
    def test_get_browser_info_brave(self, mock_get_path):
        """Test browser info detection for Brave."""
        mock_get_path.return_value = "C:\\Program Files\\BraveSoftware\\Brave-Browser\\Application\\brave.exe"

        info = BrowserLauncher.get_browser_info()

        assert info["name"] == "Brave"

    @patch("src.automation.browser_launcher.BrowserLauncher.get_default_browser_path")
    def test_get_browser_info_unknown_browser(self, mock_get_path):
        """Test browser info detection for unknown browser."""
        mock_get_path.return_value = "C:\\SomeBrowser\\mybrowser.exe"

        info = BrowserLauncher.get_browser_info()

        assert info["name"] == "mybrowser"  # Uses filename without extension

    @patch("src.automation.browser_launcher.BrowserLauncher.get_default_browser_path")
    def test_get_browser_info_no_browser(self, mock_get_path):
        """Test browser info when no browser detected."""
        mock_get_path.return_value = None

        info = BrowserLauncher.get_browser_info()

        assert info["path"] is None
        assert info["name"] is None
        assert info["version"] is None
