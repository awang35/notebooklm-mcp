"""
Browser automation client for NotebookLM interactions

Enhanced with improved response parsing for cleaner AI responses.
"""

import asyncio
import time
from pathlib import Path
from typing import Optional

from loguru import logger
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

try:
    import undetected_chromedriver as uc

    USE_UNDETECTED = True
except ImportError:
    USE_UNDETECTED = False

from .config import ServerConfig
from .exceptions import AuthenticationError, ChatError, NavigationError


class NotebookLMClient:
    """High-level client for NotebookLM automation"""

    def __init__(self, config: ServerConfig):
        self.config = config
        self.driver: Optional[webdriver.Chrome] = None
        self.current_notebook_id: Optional[str] = config.default_notebook_id
        self._is_authenticated = False

    async def start(self) -> None:
        """Start browser session"""
        await asyncio.get_event_loop().run_in_executor(None, self._start_browser)
        # Note: Authentication is deferred until first tool use for faster MCP startup

    def _start_browser(self) -> None:
        """Initialize browser with proper configuration"""
        if USE_UNDETECTED:
            logger.info("Using undetected-chromedriver for better compatibility")

            # Create persistent profile directory
            if self.config.auth.use_persistent_session:
                profile_path = Path(self.config.auth.profile_dir).absolute()
                profile_path.mkdir(exist_ok=True)

            options = uc.ChromeOptions()
            if self.config.auth.use_persistent_session:
                options.add_argument(f"--user-data-dir={profile_path}")
            options.add_argument("--no-first-run")
            options.add_argument("--no-default-browser-check")
            options.add_argument("--disable-extensions")

            # Additional stability options for Windows
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            options.add_argument("--disable-software-rasterizer")
            options.add_argument("--disable-features=VizDisplayCompositor")

            if self.config.headless:
                options.add_argument("--headless=new")
                options.add_argument("--window-size=1920,1080")
                options.add_argument("--disable-background-networking")
                options.add_argument("--disable-background-timer-throttling")
                options.add_argument("--disable-backgrounding-occluded-windows")
                options.add_argument("--disable-breakpad")
                options.add_argument("--disable-component-extensions-with-background-pages")
                options.add_argument("--disable-features=TranslateUI,BlinkGenPropertyTrees")
                options.add_argument("--disable-ipc-flooding-protection")
                options.add_argument("--disable-renderer-backgrounding")
                options.add_argument("--enable-features=NetworkService,NetworkServiceInProcess")
                options.add_argument("--force-color-profile=srgb")
                options.add_argument("--hide-scrollbars")
                options.add_argument("--metrics-recording-only")
                options.add_argument("--mute-audio")
                # Fix for DevToolsActivePort crash on Windows
                options.add_argument("--remote-debugging-port=9222")
                options.add_argument("--disable-popup-blocking")

            try:
                self.driver = uc.Chrome(options=options, version_main=None, headless=self.config.headless)
            except Exception as e:
                logger.warning(f"Failed to start undetected-chromedriver: {e}")
                logger.info("Falling back to regular Chrome WebDriver")
                self._start_regular_chrome()
        else:
            logger.warning(
                "undetected-chromedriver not available, using regular Selenium"
            )
            # Fallback implementation with regular ChromeDriver
            self._start_regular_chrome()

        if self.driver is None:
            raise RuntimeError("Failed to initialize browser driver")
        self.driver.set_page_load_timeout(self.config.timeout)

    def _start_regular_chrome(self) -> None:
        """Fallback Chrome initialization"""
        opts = ChromeOptions()

        # Use profile directory if persistent session is enabled
        if self.config.auth.use_persistent_session:
            profile_path = Path(self.config.auth.profile_dir).absolute()
            profile_path.mkdir(exist_ok=True, parents=True)
            opts.add_argument(f"--user-data-dir={profile_path}")
            logger.info(f"Using Chrome profile: {profile_path}")

            # Windows-specific flags to avoid profile lock issues
            opts.add_argument("--disable-features=RendererCodeIntegrity")
            opts.add_argument("--disable-site-isolation-trials")

        # Basic options (fewer flags for non-headless to avoid crashes)
        if not self.config.headless:
            # Minimal flags for GUI mode
            opts.add_argument("--no-first-run")
            opts.add_argument("--no-default-browser-check")
            opts.add_argument("--disable-infobars")
        else:
            # Headless mode needs more flags
            opts.add_argument("--headless=new")
            opts.add_argument("--window-size=1920,1080")
            opts.add_argument("--no-sandbox")
            opts.add_argument("--disable-dev-shm-usage")
            opts.add_argument("--disable-gpu")
            opts.add_argument("--disable-software-rasterizer")
            opts.add_argument("--disable-background-networking")
            opts.add_argument("--disable-renderer-backgrounding")
            opts.add_argument("--remote-debugging-port=9222")
            opts.add_argument("--disable-extensions")
            opts.add_argument("--disable-popup-blocking")

        # Anti-detection for all modes
        opts.add_argument("--disable-blink-features=AutomationControlled")
        opts.add_experimental_option("excludeSwitches", ["enable-automation"])
        opts.add_experimental_option("useAutomationExtension", False)

        self.driver = webdriver.Chrome(options=opts)

        # Remove automation indicators
        self.driver.execute_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )


    async def authenticate(self) -> bool:
        """Authenticate with NotebookLM"""
        if not self.driver:
            raise AuthenticationError("Browser not started")

        return await asyncio.get_event_loop().run_in_executor(
            None, self._authenticate_sync
        )

    def _authenticate_sync(self) -> bool:
        """Synchronous authentication logic"""
        if self.driver is None:
            raise RuntimeError("Browser driver not initialized")

        target_url = self.config.base_url
        if self.current_notebook_id:
            target_url = f"{self.config.base_url}/notebook/{self.current_notebook_id}"

        logger.info(f"Navigating to: {target_url}")
        self.driver.get(target_url)

        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )

            current_url = self.driver.current_url
            logger.info(f"Current URL after navigation: {current_url}")

            # Check if authenticated
            if "signin" not in current_url and "accounts.google.com" not in current_url:
                logger.info("Already authenticated via persistent session!")
                self._is_authenticated = True
                return True
            else:
                logger.warning(f"Authentication required - please log in manually")
                logger.warning(f"Current URL: {current_url}")

                if not self.config.headless:
                    logger.info("Browser will stay open for manual authentication")
                    logger.info("Please log in and the session will be saved to the profile")

                self._is_authenticated = False
                return False

        except TimeoutException:
            raise AuthenticationError("Page load timed out during authentication")


    async def send_message(self, message: str) -> None:
        """Send chat message to NotebookLM"""
        if not self.driver:
            raise ChatError("Browser not ready")

        # Auto-authenticate on first use
        if not self._is_authenticated:
            logger.info("First tool use - authenticating now...")
            auth_success = await self.authenticate()
            if not auth_success:
                raise ChatError("Authentication failed - manual login required")

        await asyncio.get_event_loop().run_in_executor(
            None, self._send_message_sync, message
        )

    def _send_message_sync(self, message: str) -> None:
        """Synchronous message sending"""
        if self.driver is None:
            raise RuntimeError("Browser driver not initialized")

        # Sanitize message: replace newlines with spaces to prevent multiple entries
        message = message.replace('\n', ' ').replace('\r', ' ')
        # Clean up multiple spaces
        message = ' '.join(message.split())
        logger.debug(f"Sanitized message: {message[:100]}...")

        # Ensure we're on the right notebook
        if self.current_notebook_id:
            current_url = self.driver.current_url
            expected_url = f"notebook/{self.current_notebook_id}"
            if expected_url not in current_url:
                self._navigate_to_notebook_sync(self.current_notebook_id)

        # Find chat input with multiple fallback selectors
        chat_selectors = [
            "textarea[placeholder*='Ask']",
            "textarea[data-testid*='chat']",
            "textarea[aria-label*='message']",
            "[contenteditable='true'][role='textbox']",
            "input[type='text'][placeholder*='Ask']",
            "textarea:not([disabled])",
        ]

        chat_input = None
        for selector in chat_selectors:
            try:
                chat_input = WebDriverWait(self.driver, 2).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                )
                logger.info(f"Found chat input with selector: {selector}")
                break
            except TimeoutException:
                continue

        if chat_input is None:
            raise ChatError("Could not find chat input element")

        # Send message
        chat_input.clear()
        chat_input.send_keys(message)

        # Submit message
        try:
            from selenium.webdriver.common.keys import Keys

            chat_input.send_keys(Keys.RETURN)
            logger.info("Message sent successfully")
        except Exception as e:
            raise ChatError(f"Failed to submit message: {e}")

    async def get_response(
        self, wait_for_completion: bool = True, max_wait: int = 60
    ) -> str:
        """Get response from NotebookLM with streaming support"""
        if not self.driver:
            raise ChatError("Browser not ready")

        if wait_for_completion:
            return await asyncio.get_event_loop().run_in_executor(
                None, self._wait_for_streaming_response, max_wait
            )
        else:
            return await asyncio.get_event_loop().run_in_executor(
                None, self._get_current_response
            )

    def _wait_for_streaming_response(self, max_wait: int) -> str:
        """Wait for streaming response to complete"""
        start_time = time.time()
        last_response = ""
        stable_count = 0
        required_stable_count = self.config.response_stability_checks

        logger.info("Waiting for streaming response to complete...")

        while time.time() - start_time < max_wait:
            current_response = self._get_current_response()

            if current_response == last_response:
                stable_count += 1
                logger.debug(
                    f"Response stable ({stable_count}/{required_stable_count})"
                )

                # Check for streaming indicators
                is_streaming = self._check_streaming_indicators()
                if not is_streaming and stable_count >= required_stable_count:
                    logger.info("Response appears complete")
                    return current_response
            else:
                stable_count = 0
                last_response = current_response
                logger.debug(f"Response updated: {current_response[:50]}...")

            time.sleep(1)

        logger.warning(
            f"Response wait timeout ({max_wait}s), returning current content"
        )
        return (
            last_response
            if last_response
            else "Response timeout - no content retrieved"
        )

    def _check_streaming_indicators(self) -> bool:
        """Check if response is still streaming"""
        if self.driver is None:
            return False

        try:
            indicators = [
                "[class*='loading']",
                "[class*='typing']",
                "[class*='generating']",
                "[class*='spinner']",
                ".dots",
            ]

            for indicator in indicators:
                elements = self.driver.find_elements(By.CSS_SELECTOR, indicator)
                for elem in elements:
                    if elem.is_displayed():
                        logger.debug(f"Found streaming indicator: {indicator}")
                        return True

            return False
        except Exception:
            return False

    def _get_current_response(self) -> str:
        """Get current response text, excluding user input"""
        if self.driver is None:
            return ""

        response_selectors = [
            "[data-testid*='response']",
            "[data-testid*='message']",
            "[role='article']",
            "[class*='message']:last-child",
            "[class*='response']:last-child",
            "[class*='chat-message']:last-child",
            ".message:last-child",
            ".chat-bubble:last-child",
            "[class*='ai-response']",
            "[class*='assistant-message']",
        ]

        best_response = ""

        for selector in response_selectors:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    elem = elements[-1]
                    text = elem.text.strip()

                    if len(text) > len(best_response):
                        best_response = text

            except Exception:
                continue

        if not best_response:
            # Fallback to any substantial text
            try:
                text_elements = self.driver.find_elements(
                    By.CSS_SELECTOR, "p, div, span"
                )
                for elem in reversed(text_elements[-20:]):
                    text = elem.text.strip()
                    if len(text) > 50 and not any(
                        skip in text.lower()
                        for skip in [
                            "ask about",
                            "loading",
                            "error",
                            "sign in",
                            "menu",
                            "copy_all",
                            "thumb_up",
                            "thumb_down",
                        ]
                    ):
                        best_response = text
                        break
            except Exception:
                pass

        # Clean up response by removing user input if it appears at the beginning
        if best_response:
            best_response = self._clean_response_text(best_response)

        return best_response if best_response else "No response content found"

    def _clean_response_text(self, response_text: str) -> str:
        """Clean response text by removing user input and extracting AI response"""
        if not response_text:
            return response_text

        # Remove UI artifacts at the end
        ui_artifacts = [
            "copy_all",
            "thumb_up",
            "thumb_down",
            "share",
            "more_options",
            "like",
            "dislike",
        ]
        for artifact in ui_artifacts:
            if response_text.endswith(artifact):
                response_text = response_text[: -len(artifact)].strip()

        # Remove multiple UI artifacts that might appear together
        lines = response_text.split("\n")
        cleaned_lines = []

        for line in lines:
            line_clean = line.strip().lower()
            # Skip lines that are just UI artifacts
            if line_clean in ui_artifacts:
                continue
            # Skip lines with multiple UI artifacts
            if (
                any(artifact in line_clean for artifact in ui_artifacts)
                and len(line_clean) < 50
            ):
                continue
            cleaned_lines.append(line)

        response_text = "\n".join(cleaned_lines).strip()

        # Split by common delimiters that might separate user input from AI response
        lines = response_text.split("\n")

        # If response starts with the user's message, try to find where AI response begins
        # Look for patterns that indicate the start of AI response
        ai_response_indicators = [
            "Mixture-of-Experts",  # Specific to MoE responses
            "Based on",
            "According to",
            "Here's",
            "Let me",
            "I can",
            "The answer",
            "To answer",
            # Common AI response starters
        ]

        # Try to find the first line that looks like an AI response
        start_index = 0
        for i, line in enumerate(lines):
            line_clean = line.strip()
            if line_clean and any(
                indicator in line_clean for indicator in ai_response_indicators
            ):
                start_index = i
                break
            # If we find a line that's significantly longer and looks like content
            elif len(line_clean) > 50 and not line_clean.endswith("?"):
                start_index = i
                break

        # Join from the AI response start
        cleaned_response = "\n".join(lines[start_index:]).strip()

        # If cleaning didn't work well, try a different approach
        if not cleaned_response or len(cleaned_response) < 50:
            # Look for the first substantial paragraph
            paragraphs = response_text.split("\n\n")
            for paragraph in paragraphs:
                if len(paragraph.strip()) > 100:  # Substantial content
                    cleaned_response = paragraph.strip()
                    break

        # Fallback: if still no good content, return original but try to remove first line if it looks like user input
        if not cleaned_response or len(cleaned_response) < 50:
            if lines and len(lines) > 1:
                first_line = lines[0].strip()
                # If first line looks like a question or command, remove it
                if first_line.endswith("?") or len(first_line) < 100:
                    cleaned_response = "\n".join(lines[1:]).strip()
                else:
                    cleaned_response = response_text
            else:
                cleaned_response = response_text

        return cleaned_response

    async def navigate_to_notebook(self, notebook_id: str) -> str:
        """Navigate to specific notebook"""
        if not self.driver:
            raise NavigationError("Browser not started")

        return await asyncio.get_event_loop().run_in_executor(
            None, self._navigate_to_notebook_sync, notebook_id
        )

    def _navigate_to_notebook_sync(self, notebook_id: str) -> str:
        """Synchronous notebook navigation"""
        if self.driver is None:
            raise RuntimeError("Browser driver not initialized")

        url = f"{self.config.base_url}/notebook/{notebook_id}"
        self.driver.get(url)

        try:
            WebDriverWait(self.driver, self.config.timeout).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            self.current_notebook_id = notebook_id
            return self.driver.current_url
        except TimeoutException:
            raise NavigationError(f"Failed to navigate to notebook {notebook_id}")

    async def close(self) -> None:
        """Close browser session"""
        if self.driver:
            await asyncio.get_event_loop().run_in_executor(None, self.driver.quit)
            self.driver = None
            self._is_authenticated = False
