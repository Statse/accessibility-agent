"""Browser launcher for opening URLs in the default or specified browser.

This module provides functionality to detect the default browser on Windows
via the registry and launch URLs in the browser.
"""

import logging
import os
import subprocess
import webbrowser
from pathlib import Path
from typing import Optional

try:
    import winreg
except ImportError:
    # Not on Windows, winreg won't be available
    winreg = None  # type: ignore


logger = logging.getLogger(__name__)


class BrowserLaunchError(Exception):
    """Exception raised when browser launch fails."""

    pass


class BrowserLauncher:
    """Launches URLs in a web browser.

    This class detects the default browser on Windows via the registry
    and provides methods to launch URLs. It supports both auto-detection
    and manual browser path specification.

    Attributes:
        browser_path: Path to browser executable. If None, uses system default.
    """

    def __init__(self, browser_path: Optional[str] = None) -> None:
        """Initialize the browser launcher.

        Args:
            browser_path: Optional explicit path to browser executable.
                If None, the default system browser will be used.

        Raises:
            BrowserLaunchError: If explicit browser_path is provided but doesn't exist.
        """
        self.browser_path = browser_path

        if browser_path:
            if not Path(browser_path).exists():
                raise BrowserLaunchError(f"Browser not found at: {browser_path}")
            logger.info(f"BrowserLauncher initialized with explicit path: {browser_path}")
        else:
            logger.info("BrowserLauncher initialized with system default browser")

    @staticmethod
    def get_default_browser_path() -> Optional[str]:
        """Detect the default browser path from Windows registry.

        Returns:
            Path to the default browser executable, or None if detection fails.

        Note:
            This method only works on Windows. On other platforms, returns None.
        """
        if winreg is None:
            logger.warning("winreg not available (not on Windows)")
            return None

        try:
            # Get the user's choice for default browser
            # HKEY_CURRENT_USER\Software\Microsoft\Windows\Shell\Associations\UrlAssociations\http\UserChoice
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\Shell\Associations\UrlAssociations\http\UserChoice",
            ) as key:
                prog_id = winreg.QueryValueEx(key, "ProgId")[0]
                logger.debug(f"Default browser ProgId: {prog_id}")

            # Get the command associated with this ProgId
            # HKEY_CLASSES_ROOT\<ProgId>\shell\open\command
            with winreg.OpenKey(
                winreg.HKEY_CLASSES_ROOT,
                rf"{prog_id}\shell\open\command",
            ) as key:
                command = winreg.QueryValueEx(key, "")[0]
                logger.debug(f"Browser command: {command}")

            # Extract the executable path from the command
            # Command typically looks like: "C:\Program Files\Browser\browser.exe" -- "%1"
            if command.startswith('"'):
                # Path is quoted
                end_quote = command.find('"', 1)
                if end_quote > 0:
                    browser_path = command[1:end_quote]
                else:
                    browser_path = command.split()[0].strip('"')
            else:
                # Path is not quoted
                # Try to find .exe extension to handle paths with spaces
                exe_index = command.lower().find('.exe')
                if exe_index > 0:
                    # Include .exe in the path
                    browser_path = command[:exe_index + 4].strip()
                else:
                    # Fallback to first token
                    browser_path = command.split()[0]

            # Verify the path exists
            if Path(browser_path).exists():
                logger.info(f"Detected default browser: {browser_path}")
                return browser_path
            else:
                logger.warning(f"Detected browser path doesn't exist: {browser_path}")
                return None

        except FileNotFoundError as e:
            logger.warning(f"Registry key not found: {e}")
            return None
        except Exception as e:
            logger.error(f"Error detecting default browser: {e}")
            return None

    def launch_url(self, url: str, new_window: bool = True) -> bool:
        """Launch a URL in the browser.

        Args:
            url: URL to open (e.g., "https://example.com").
            new_window: If True, attempt to open in a new window.
                If False, may reuse existing window/tab (default: True).

        Returns:
            True if launch was successful, False otherwise.

        Raises:
            BrowserLaunchError: If URL is invalid or launch fails.

        Example:
            launcher = BrowserLauncher()
            launcher.launch_url("https://example.com")
        """
        if not url:
            raise BrowserLaunchError("URL cannot be empty")

        # Add https:// if no protocol specified
        if not url.startswith(("http://", "https://", "file://")):
            url = f"https://{url}"
            logger.debug(f"Added https:// prefix to URL: {url}")

        logger.info(f"Launching URL: {url}")

        try:
            if self.browser_path:
                # Launch with explicit browser path
                return self._launch_with_path(url, new_window)
            else:
                # Use system default browser
                return self._launch_with_default(url, new_window)

        except Exception as e:
            logger.error(f"Failed to launch URL: {e}")
            raise BrowserLaunchError(f"Failed to launch URL '{url}': {e}") from e

    def _launch_with_path(self, url: str, new_window: bool) -> bool:
        """Launch URL with explicit browser path using subprocess.

        Args:
            url: URL to open.
            new_window: Whether to open in new window.

        Returns:
            True if successful.
        """
        try:
            # Common browser arguments for new window
            args = [self.browser_path]

            # Add new window flag based on browser type
            browser_lower = self.browser_path.lower()
            if "chrome" in browser_lower or "edge" in browser_lower:
                if new_window:
                    args.append("--new-window")
            elif "firefox" in browser_lower:
                if new_window:
                    args.extend(["-new-window"])

            args.append(url)

            # Launch browser as separate process
            subprocess.Popen(
                args,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )

            logger.info(f"Browser launched with explicit path: {self.browser_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to launch browser with path: {e}")
            return False

    def _launch_with_default(self, url: str, new_window: bool) -> bool:
        """Launch URL with system default browser using webbrowser module.

        Args:
            url: URL to open.
            new_window: Whether to open in new window.

        Returns:
            True if successful.

        Raises:
            Exception: If browser launch fails.
        """
        # Use Python's webbrowser module for cross-platform support
        if new_window:
            webbrowser.open_new(url)
        else:
            webbrowser.open(url)

        logger.info("URL opened with system default browser")
        return True

    def close_browser(self) -> None:
        """Attempt to close the browser.

        Note:
            This is a best-effort operation. It's difficult to reliably
            close a browser programmatically without additional tools.
            For now, this is a placeholder for future implementation.
        """
        logger.warning("close_browser() not yet implemented - requires additional tools")
        # Future: Could use pywinauto or similar to find and close browser windows

    @staticmethod
    def get_browser_info() -> dict[str, Optional[str]]:
        """Get information about the detected default browser.

        Returns:
            Dictionary with browser information:
                - 'path': Path to browser executable
                - 'name': Browser name (e.g., 'Chrome', 'Firefox')
                - 'version': Browser version (not yet implemented)

        Example:
            info = BrowserLauncher.get_browser_info()
            print(f"Default browser: {info['name']} at {info['path']}")
        """
        browser_path = BrowserLauncher.get_default_browser_path()

        if not browser_path:
            return {"path": None, "name": None, "version": None}

        # Extract browser name from path
        browser_name = None
        path_lower = browser_path.lower()

        if "chrome" in path_lower:
            browser_name = "Chrome"
        elif "firefox" in path_lower:
            browser_name = "Firefox"
        elif "edge" in path_lower or "msedge" in path_lower:
            browser_name = "Edge"
        elif "opera" in path_lower:
            browser_name = "Opera"
        elif "brave" in path_lower:
            browser_name = "Brave"
        else:
            # Extract filename without extension
            browser_name = Path(browser_path).stem

        return {
            "path": browser_path,
            "name": browser_name,
            "version": None,  # TODO: Implement version detection
        }
