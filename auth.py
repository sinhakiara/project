"""Multi-strategy authentication for StealthCrawler v17."""

import asyncio
import logging
from typing import Optional, Dict, Any
from playwright.async_api import Page

logger = logging.getLogger(__name__)


class AuthenticationHandler:
    """
    Handle various authentication methods.
    
    Features:
    - Basic authentication
    - Form-based login
    - OAuth2 support
    - Session management
    - Cookie persistence
    """
    
    def __init__(self):
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
        logger.info("Basic authentication configured")
    
    def configure_oauth2(self, client_id: str, client_secret: str, token_url: str) -> None:
        """Configure OAuth2 authentication."""
        self.auth_type = 'oauth2'
        self.credentials = {
            'client_id': client_id,
            'client_secret': client_secret,
            'token_url': token_url
        }
        logger.info("OAuth2 authentication configured")
    
    async def login_form(
        self,
        page: Page,
        login_url: str,
        username: str,
        password: str,
        username_selector: str = 'input[name="username"]',
        password_selector: str = 'input[name="password"]',
        submit_selector: str = 'button[type="submit"]'
    ) -> bool:
        """
        Perform form-based login.
        
        Args:
            page: Playwright page
            login_url: Login page URL
            username: Username
            password: Password
            username_selector: CSS selector for username field
            password_selector: CSS selector for password field
            submit_selector: CSS selector for submit button
            
        Returns:
            True if login successful, False otherwise
        """
        try:
            logger.info(f"Attempting form login at {login_url}")
            
            # Navigate to login page
            await page.goto(login_url)
            await page.wait_for_load_state('networkidle')
            
            # Fill in credentials
            await page.fill(username_selector, username)
            await page.fill(password_selector, password)
            
            # Submit form
            await page.click(submit_selector)
            await page.wait_for_load_state('networkidle')
            
            # Check if login successful (customize based on your needs)
            # Here we just check if we're not still on the login page
            current_url = page.url
            success = current_url != login_url
            
            if success:
                logger.info("Form login successful")
                # Store cookies
                self.cookies = await page.context.cookies()
            else:
                logger.warning("Form login may have failed")
            
            return success
            
        except Exception as e:
            logger.error(f"Form login failed: {e}")
            return False
    
    async def get_oauth2_token(self) -> Optional[str]:
        """
        Obtain OAuth2 access token.
        
        Returns:
            Access token or None
        """
        if self.auth_type != 'oauth2':
            logger.warning("OAuth2 not configured")
            return None
        
        try:
            import httpx
            
            # Request token
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
                    logger.info("OAuth2 token obtained")
                    return token
                else:
                    logger.error(f"Failed to obtain OAuth2 token: {response.status_code}")
                    return None
                    
        except Exception as e:
            logger.error(f"OAuth2 token request failed: {e}")
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
        
        return headers
    
    async def apply_cookies(self, page: Page) -> None:
        """Apply stored cookies to a page."""
        if self.cookies:
            await page.context.add_cookies(self.cookies)
            logger.debug("Cookies applied to page")
