"""note.com API client with Selenium-based authentication."""

import os
import logging
import time
import requests
from typing import Optional, Dict
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

from .config import (
    NOTE_BASE_URL,
    NOTE_API_TIMEOUT,
)
from .markdown_utils import markdown_to_note_html


logger = logging.getLogger(__name__)


class NoteAPIError(Exception):
    """Base exception for note API errors."""
    pass


class LoginError(NoteAPIError):
    """Login authentication failed."""
    pass


class ValidationError(NoteAPIError):
    """Validation error from API."""
    pass


class NoteAPIClient:
    """
    Client for interacting with note.com API.

    Uses Selenium for authentication to obtain cookies.
    """

    def __init__(self, email: Optional[str] = None, password: Optional[str] = None):
        """
        Initialize note API client.

        Args:
            email: note.com login email (defaults to NOTE_EMAIL env var)
            password: note.com login password (defaults to NOTE_PASSWORD env var)
        """
        self.email = email or os.getenv("NOTE_EMAIL")
        self.password = password or os.getenv("NOTE_PASSWORD")

        if not self.email or not self.password:
            raise ValueError("NOTE_EMAIL and NOTE_PASSWORD must be set")

        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                          "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "ja,en-US;q=0.9,en;q=0.8",
        })

        self._cookies: Optional[Dict[str, str]] = None
        self._logged_in = False

    def _setup_driver(self) -> webdriver.Chrome:
        """
        Setup Chrome WebDriver with headless options.

        Returns:
            Configured WebDriver instance
        """
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )

        driver = webdriver.Chrome(options=chrome_options)
        return driver

    def login(self) -> None:
        """
        Login to note.com using Selenium and obtain cookies.

        Raises:
            LoginError: If login fails
        """
        logger.info("Logging in to note.com with Selenium...")

        driver = None
        try:
            driver = self._setup_driver()

            # Navigate to login page
            driver.get(f"{NOTE_BASE_URL}/login")
            logger.info("Navigated to login page")

            # Wait for email input field
            email_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.NAME, "email"))
            )
            email_input.send_keys(self.email)
            logger.info("Entered email")

            # Enter password
            password_input = driver.find_element(By.NAME, "password")
            password_input.send_keys(self.password)
            logger.info("Entered password")

            # Click login button
            login_button = driver.find_element(By.XPATH, "//button[@type='submit']")
            login_button.click()
            logger.info("Clicked login button")

            # Wait for login to complete (wait for redirect away from login page)
            time.sleep(5)

            # Check if login was successful by checking URL
            current_url = driver.current_url
            if "login" in current_url:
                raise LoginError("Login failed - still on login page")

            # Get cookies
            cookies = driver.get_cookies()
            self._cookies = {cookie['name']: cookie['value'] for cookie in cookies}

            # Check for note_session cookie
            if 'note_session' not in self._cookies:
                raise LoginError("Login appeared successful but no session cookie found")

            # Set cookies in requests session
            for name, value in self._cookies.items():
                self.session.cookies.set(name, value)

            logger.info("Successfully logged in and obtained cookies")
            self._logged_in = True

        except Exception as e:
            logger.error(f"Login failed: {e}")
            raise LoginError(f"Failed to login with Selenium: {e}")

        finally:
            if driver:
                driver.quit()

    def _ensure_logged_in(self) -> None:
        """Ensure user is logged in, login if necessary."""
        if not self._logged_in:
            self.login()

    def create_draft(
        self,
        title: str,
        content_markdown: str,
        magazine_id: Optional[str] = None
    ) -> str:
        """
        Create a draft article on note.com.

        Args:
            title: Article title
            content_markdown: Article content in markdown format
            magazine_id: Magazine ID to publish to (optional)

        Returns:
            URL of the created draft

        Raises:
            ValidationError: If API validation fails
            NoteAPIError: If API request fails
        """
        self._ensure_logged_in()

        # Convert markdown to HTML
        html_content = markdown_to_note_html(content_markdown)

        # Prepare payload
        payload = {
            "body": html_content,
            "name": title,
            "template_key": None,
        }

        # Try to create article
        try:
            response = self.session.post(
                f"{NOTE_BASE_URL}/api/v1/text_notes",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=NOTE_API_TIMEOUT
            )

            if response.status_code == 401:
                raise LoginError("Session expired")

            if response.status_code == 422:
                error_data = response.json()
                error_msg = error_data.get("message", "Validation error")
                raise ValidationError(f"Invalid payload: {error_msg}")

            response.raise_for_status()

            data = response.json()
            article_id = data.get("data", {}).get("id")
            article_key = data.get("data", {}).get("key")

            if not article_id:
                raise NoteAPIError("Could not get article ID from response")

            logger.info(f"Article created with ID: {article_id}")

            # Update to draft status and add to magazine if needed
            if magazine_id or True:  # Always update to set draft status
                self._update_article_draft(article_id, title, content_markdown, magazine_id)

            # Construct URL
            note_url = f"{NOTE_BASE_URL}/notes/{article_key}" if article_key else f"{NOTE_BASE_URL}"

            logger.info(f"Draft created successfully: {note_url}")
            return note_url

        except requests.exceptions.RequestException as e:
            raise NoteAPIError(f"Failed to create draft: {e}")

    def _update_article_draft(
        self,
        article_id: str,
        title: str,
        content_markdown: str,
        magazine_id: Optional[str] = None
    ) -> None:
        """
        Update article to draft status.

        Args:
            article_id: Article ID
            title: Article title
            content_markdown: Article content
            magazine_id: Magazine ID (optional)
        """
        html_content = markdown_to_note_html(content_markdown)

        payload = {
            "body": html_content,
            "name": title,
            "status": "draft",
        }

        if magazine_id:
            payload["magazine_id"] = magazine_id

        try:
            response = self.session.put(
                f"{NOTE_BASE_URL}/api/v1/text_notes/{article_id}",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=NOTE_API_TIMEOUT
            )

            if response.status_code == 200:
                logger.info("Article updated to draft status")
            else:
                logger.warning(f"Failed to update article status: {response.status_code}")

        except Exception as e:
            logger.warning(f"Failed to update article to draft: {e}")

    def test_connection(self) -> bool:
        """
        Test connection and authentication to note.com.

        Returns:
            True if connection is successful

        Raises:
            LoginError: If authentication fails
        """
        try:
            self.login()
            logger.info("Connection test successful")
            return True
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            raise
