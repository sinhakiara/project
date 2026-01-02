"""CAPTCHA solving integration for StealthCrawler v17."""

import asyncio
import logging
from typing import Optional
from playwright.async_api import Page

logger = logging.getLogger(__name__)


class CaptchaHandler:
    """
    Handle CAPTCHA challenges using various solving services.
    
    Features:
    - 2Captcha integration
    - Anti-Captcha integration
    - Manual solving fallback
    - reCAPTCHA v2/v3 support
    """
    
    def __init__(self, solver: str = 'none', api_key: Optional[str] = None):
        self.solver = solver
        self.api_key = api_key
        
    async def detect_captcha(self, page: Page) -> Optional[str]:
        """
        Detect if a CAPTCHA is present on the page.
        
        Args:
            page: Playwright page
            
        Returns:
            CAPTCHA type if detected, None otherwise
        """
        try:
            # Check for reCAPTCHA
            recaptcha = await page.query_selector('.g-recaptcha, iframe[src*="recaptcha"]')
            if recaptcha:
                logger.info("reCAPTCHA detected")
                return 'recaptcha'
            
            # Check for hCaptcha
            hcaptcha = await page.query_selector('.h-captcha, iframe[src*="hcaptcha"]')
            if hcaptcha:
                logger.info("hCaptcha detected")
                return 'hcaptcha'
            
            # Check for image CAPTCHA
            img_captcha = await page.query_selector('img[alt*="captcha" i], img[src*="captcha" i]')
            if img_captcha:
                logger.info("Image CAPTCHA detected")
                return 'image'
            
        except Exception as e:
            logger.error(f"CAPTCHA detection error: {e}")
        
        return None
    
    async def solve_recaptcha(self, page: Page, site_key: str) -> Optional[str]:
        """
        Solve reCAPTCHA using configured solver.
        
        Args:
            page: Playwright page
            site_key: reCAPTCHA site key
            
        Returns:
            Solution token or None
        """
        if self.solver == 'none' or not self.api_key:
            logger.warning("No CAPTCHA solver configured")
            return None
        
        try:
            if self.solver == '2captcha':
                return await self._solve_with_2captcha(page.url, site_key)
            elif self.solver == 'anti-captcha':
                return await self._solve_with_anticaptcha(page.url, site_key)
            else:
                logger.error(f"Unknown solver: {self.solver}")
                return None
                
        except Exception as e:
            logger.error(f"CAPTCHA solving failed: {e}")
            return None
    
    async def _solve_with_2captcha(self, url: str, site_key: str) -> Optional[str]:
        """Solve using 2Captcha service."""
        try:
            import httpx
            
            # Submit CAPTCHA
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    'http://2captcha.com/in.php',
                    data={
                        'key': self.api_key,
                        'method': 'userrecaptcha',
                        'googlekey': site_key,
                        'pageurl': url,
                        'json': 1
                    }
                )
                
                result = response.json()
                if result.get('status') != 1:
                    logger.error(f"2Captcha error: {result}")
                    return None
                
                captcha_id = result['request']
                logger.info(f"CAPTCHA submitted to 2Captcha: {captcha_id}")
                
                # Poll for result
                for _ in range(60):  # Try for 5 minutes
                    await asyncio.sleep(5)
                    
                    response = await client.get(
                        f'http://2captcha.com/res.php',
                        params={
                            'key': self.api_key,
                            'action': 'get',
                            'id': captcha_id,
                            'json': 1
                        }
                    )
                    
                    result = response.json()
                    if result.get('status') == 1:
                        token = result['request']
                        logger.info("CAPTCHA solved successfully")
                        return token
                    elif result.get('request') != 'CAPCHA_NOT_READY':
                        logger.error(f"2Captcha error: {result}")
                        return None
                
                logger.error("CAPTCHA solving timeout")
                return None
                
        except Exception as e:
            logger.error(f"2Captcha error: {e}")
            return None
    
    async def _solve_with_anticaptcha(self, url: str, site_key: str) -> Optional[str]:
        """Solve using Anti-Captcha service."""
        logger.warning("Anti-Captcha integration not yet implemented")
        return None
    
    async def handle_captcha(self, page: Page) -> bool:
        """
        Detect and solve CAPTCHA on page.
        
        Args:
            page: Playwright page
            
        Returns:
            True if CAPTCHA solved or not present, False otherwise
        """
        captcha_type = await self.detect_captcha(page)
        
        if not captcha_type:
            return True  # No CAPTCHA
        
        if captcha_type == 'recaptcha':
            # Extract site key
            try:
                site_key = await page.evaluate('''
                    () => {
                        const element = document.querySelector('.g-recaptcha');
                        return element ? element.getAttribute('data-sitekey') : null;
                    }
                ''')
                
                if site_key:
                    solution = await self.solve_recaptcha(page, site_key)
                    
                    if solution:
                        # Inject solution
                        await page.evaluate(f'''
                            (token) => {{
                                document.getElementById('g-recaptcha-response').innerHTML = token;
                                if (typeof onCaptchaSuccess === 'function') {{
                                    onCaptchaSuccess(token);
                                }}
                            }}
                        ''', solution)
                        return True
                        
            except Exception as e:
                logger.error(f"Failed to handle reCAPTCHA: {e}")
        
        logger.warning(f"Unable to solve {captcha_type} CAPTCHA")
        return False
