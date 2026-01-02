"""note.com API client with email/password authentication."""

import os
import logging
import requests
from bs4 import BeautifulSoup
from typing import Optional

from .config import (
    NOTE_BASE_URL,
    NOTE_LOGIN_ENDPOINT,
    NOTE_NOTES_ENDPOINT,
    NOTE_DASHBOARD_URL,
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

    Handles authentication via email/password and draft creation.
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

        self._csrf_token: Optional[str] = None
        self._logged_in = False

    def login(self) -> None:
        """
        Login to note.com using email and password.

        Raises:
            LoginError: If login fails
        """
        logger.info("Logging in to note.com...")

        # First, get CSRF token from login page
        try:
            response = self.session.get(
                f"{NOTE_BASE_URL}/login",
                timeout=NOTE_API_TIMEOUT
            )
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")
            csrf_meta = soup.find("meta", {"name": "csrf-token"})

            if not csrf_meta:
                raise LoginError("Could not retrieve CSRF token from login page")

            csrf_token = csrf_meta.get("content")

        except requests.exceptions.RequestException as e:
            raise LoginError(f"Failed to access login page: {e}")

        # Send login request
        login_payload = {
            "emailOrUrlname": self.email,
            "password": self.password,
        }

        try:
            response = self.session.post(
                NOTE_LOGIN_ENDPOINT,
                json=login_payload,
                headers={"X-CSRF-Token": csrf_token},
                timeout=NOTE_API_TIMEOUT
            )

            if response.status_code == 401:
                raise LoginError("Invalid email or password")

            if response.status_code == 422:
                error_msg = response.json().get("message", "Validation error")
                raise LoginError(f"Login validation error: {error_msg}")

            response.raise_for_status()

            # Check if login was successful by verifying session cookie
            if "note_session" not in self.session.cookies:
                raise LoginError("Login appeared successful but no session cookie received")

            logger.info("Successfully logged in to note.com")
            self._logged_in = True

        except requests.exceptions.RequestException as e:
            raise LoginError(f"Login request failed: {e}")

    def _ensure_logged_in(self) -> None:
        """Ensure user is logged in, login if necessary."""
        if not self._logged_in:
            self.login()

    def _get_csrf_token(self) -> str:
        """
        Get CSRF token from note.com dashboard.

        Returns:
            CSRF token string

        Raises:
            NoteAPIError: If CSRF token cannot be retrieved
        """
        if self._csrf_token:
            return self._csrf_token

        self._ensure_logged_in()

        try:
            response = self.session.get(NOTE_DASHBOARD_URL, timeout=NOTE_API_TIMEOUT)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")
            csrf_meta = soup.find("meta", {"name": "csrf-token"})

            if not csrf_meta:
                raise NoteAPIError("Could not retrieve CSRF token from dashboard")

            self._csrf_token = csrf_meta.get("content")
            return self._csrf_token

        except requests.exceptions.RequestException as e:
            raise NoteAPIError(f"Failed to retrieve CSRF token: {e}")

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

        # Get CSRF token
        csrf_token = self._get_csrf_token()

        # Prepare payload
        payload = {
            "note": {
                "name": title,
                "body": html_content,
                "status": "draft",  # Always create as draft
                "publish_at": None,
                "eyecatch": None,
            }
        }

        # Add magazine_id if provided
        if magazine_id:
            payload["note"]["magazine_id"] = magazine_id

        # Send request
        try:
            response = self.session.post(
                NOTE_NOTES_ENDPOINT,
                json=payload,
                headers={
                    "X-CSRF-Token": csrf_token,
                    "Content-Type": "application/json",
                },
                timeout=NOTE_API_TIMEOUT
            )

            if response.status_code == 401:
                raise LoginError("Session expired, please login again")

            if response.status_code == 422:
                error_data = response.json()
                error_msg = error_data.get("message", "Validation error")
                raise ValidationError(f"Invalid payload: {error_msg}")

            response.raise_for_status()

            data = response.json()
            note_data = data.get("data", {}).get("note", {})
            note_url = note_data.get("note_url")

            if not note_url:
                # Fallback: construct URL from note key
                note_key = note_data.get("key")
                if note_key:
                    note_url = f"{NOTE_BASE_URL}/notes/{note_key}"
                else:
                    raise NoteAPIError("Could not determine note URL from response")

            logger.info(f"Draft created successfully: {note_url}")
            return note_url

        except requests.exceptions.RequestException as e:
            raise NoteAPIError(f"Failed to create draft: {e}")

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
            csrf_token = self._get_csrf_token()
            logger.info("Connection test successful")
            return True
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            raise
