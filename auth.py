"""Multi-strategy authentication for StealthCrawler v18/v17.

Features:
- Basic, Form, and Bearer authentication (Playwright & requests patterns)
- OAuth2 (async token retrieval, httpx)
- Session/cookie management
- Supports both Class: AuthenticationManager and AuthenticationHandler
- God Mode compatible: accepts optional logger
"""
import asyncio
import logging
from typing import Optional, Dict, Any, Union
from playwright.async_api import Page

class AuthenticationHandler:
    """
    Handles various authentication methods.

    Features:
    - Basic authentication
    - Form-based login (browser and requests)
    - OAuth2 support (async, httpx)
    - Session management
    - Cookie persistence
    - Bearer token (header)
    - Uses optional injected logger
    """

    def __init__(self, logger=None):
        if logger is None:
            logger = logging.getLogger(__name__)
        self.logger = logger
        self.auth_type: str = 'none'
        self.credentials: Dict[str, str] = {}
        self.tokens: Dict[str, str] = {}
        self.cookies: list = []

    def configure_basic_auth(self, username: str, password: str) -> None:
        """Configure HTTP Basic Authentication."""
        self.auth_type = 'basic'
        self.credentials = {
            'username': username,
            'password': password
        }
        self.logger.info("Basic authentication configured")

    def configure_bearer_token(self, token: str):
        """Configure Bearer Token Authentication."""
        self.auth_type = "bearer"
        self.credentials = {"bearer_token": token}
        self.logger.info("Bearer token authentication configured")

    def configure_oauth2(self, client_id: str, client_secret: str, token_url: str) -> None:
        """Configure OAuth2 authentication."""
        self.auth_type = 'oauth2'
        self.credentials = {
            'client_id': client_id,
            'client_secret': client_secret,
            'token_url': token_url
        }
        self.logger.info("OAuth2 authentication configured")

    def configure_form_auth(self, username: str, password: str, login_url: str, username_selector:str=None, password_selector:str=None, submit_selector:str=None):
        """Configure browser form auth (selectors optional)."""
        self.auth_type = 'form'
        self.credentials = {
            'username': username,
            'password': password,
            'login_url': login_url,
            'username_selector': username_selector or 'input[name="username"]',
            'password_selector': password_selector or 'input[name="password"]',
            'submit_selector': submit_selector or 'button[type="submit"]'
        }
        self.logger.info("Form authentication configured")

    async def login_form(
        self,
        page: Page,
        login_url: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        username_selector: Optional[str] = None,
        password_selector: Optional[str] = None,
        submit_selector: Optional[str] = None,
    ) -> bool:
        """
        Perform form-based login with Playwright.

        Args:
            page: Playwright page
            login_url: Login page URL
            username: Username
            password: Password
            username_selector/password_selector/submit_selector (optional): CSS selectors

        Returns:
            True if login successful, False otherwise
        """
        # Use provided or fallback to configured credentials
        creds = self.credentials
        url = login_url or creds.get("login_url")
        user = username or creds.get("username")
        passwd = password or creds.get("password")
        user_sel = username_selector or creds.get("username_selector", 'input[name="username"]')
        pass_sel = password_selector or creds.get("password_selector", 'input[name="password"]')
        submit_sel = submit_selector or creds.get("submit_selector", 'button[type="submit"]')
        try:
            self.logger.info(f"Attempting form login at {url}")
            await page.goto(url)
            await page.wait_for_load_state('networkidle')
            await page.fill(user_sel, user)
            await page.fill(pass_sel, passwd)
            await page.click(submit_sel)
            await page.wait_for_load_state('networkidle')
            # Check if login succeeded (not robust; customize as needed)
            current_url = page.url
            success = current_url != url
            if success:
                self.logger.info("Form login successful")
                self.cookies = await page.context.cookies()
            else:
                self.logger.warning("Form login may have failed")
            return success
        except Exception as e:
            self.logger.error(f"Form login failed: {e}")
            return False

    async def get_oauth2_token(self) -> Optional[str]:
        """
        Obtain OAuth2 access token.
        Returns:
            Access token or None
        """
        if self.auth_type != 'oauth2':
            self.logger.warning("OAuth2 not configured")
            return None
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.credentials['token_url'],
                    data={
                        'grant_type': 'client_credentials',
                        'client_id': self.credentials['client_id'],
                        'client_secret': self.credentials['client_secret']
                    }
                )
                if response.status_code == 200:
                    data = response.json()
                    token = data.get('access_token')
                    self.tokens['access_token'] = token
                    self.logger.info("OAuth2 token obtained")
                    return token
                else:
                    self.logger.error(f"Failed to obtain OAuth2 token: {response.status_code}")
                    return None
        except Exception as e:
            self.logger.error(f"OAuth2 token request failed: {e}")
            return None

    def get_auth_headers(self) -> Dict[str, str]:
        """
        Get authentication headers.
        Returns:
            Dictionary of headers
        """
        headers = {}
        if self.auth_type == 'basic':
            import base64
            credentials = f"{self.credentials['username']}:{self.credentials['password']}"
            encoded = base64.b64encode(credentials.encode()).decode()
            headers['Authorization'] = f'Basic {encoded}'
        elif self.auth_type == 'oauth2' and 'access_token' in self.tokens:
            headers['Authorization'] = f"Bearer {self.tokens['access_token']}"
        elif self.auth_type == 'bearer':
            token = self.credentials.get('bearer_token')
            if token:
                headers['Authorization'] = f"Bearer {token}"
        return headers

    async def apply_cookies(self, page: Page) -> None:
        """Apply stored cookies to a page."""
        if self.cookies:
            await page.context.add_cookies(self.cookies)
            self.logger.debug("Cookies applied to page")

    # Universal method to select and perform auth at orchestrator level
    async def authenticate(self, session_or_page: Union[Any, Page], config: Any = None, browser=None):
        """
        Perform authentication based on the type specified. Works for both HTTP and browser.
        For Playwright browser-based login, pass a Page.
        For requests/httpx, pass a session.
        """
        t = getattr(config, "auth_type", self.auth_type)
        if t == "basic":
            user = getattr(config, "username", None) or self.credentials.get("username")
            pwd = getattr(config, "password", None) or self.credentials.get("password")
            self.configure_basic_auth(user, pwd)
        elif t == "bearer_token":
            token = getattr(config, "bearer_token", None) or self.credentials.get("bearer_token")
            self.configure_bearer_token(token)
        elif t == "oauth2":
            cid = getattr(config, "client_id", None) or self.credentials.get("client_id")
            csec = getattr(config, "client_secret", None) or self.credentials.get("client_secret")
            turl = getattr(config, "token_url", None) or self.credentials.get("token_url")
            self.configure_oauth2(cid, csec, turl)
            await self.get_oauth2_token()
        elif t == "form":
            # If browser/Page is provided, do browser login (async)
            if isinstance(session_or_page, Page):
                await self.login_form(session_or_page)
            else:
                self.logger.warning("Form login via HTTP session not implemented in God Mode (use Playwright Page).")
        # Apply cookies if any, for browser:
        if isinstance(session_or_page, Page):
            await self.apply_cookies(session_or_page)
        return session_or_page

# Legacy alias for compatibility
AuthenticationManager = AuthenticationHandler
