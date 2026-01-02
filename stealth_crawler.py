"""Core async crawler with Playwright for StealthCrawler v17."""

import asyncio
import logging
from typing import Optional, List, Dict, Set, Any
from datetime import datetime
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
from urllib.parse import urljoin

from config import CrawlerConfig
from scope_manager import ScopeManager
from utils import normalize_url, extract_links, get_domain
from rate_limiter import RateLimiter
from fingerprint import FingerprintRandomizer

logger = logging.getLogger(__name__)


class CrawlResult:
    """Represents the result of crawling a single URL."""
    
    def __init__(self, url: str, status: int = 0, success: bool = False):
        self.url = url
        self.status = status
        self.success = success
        self.title: Optional[str] = None
        self.html: Optional[str] = None
        self.screenshot: Optional[bytes] = None
        self.links: List[str] = []
        self.depth: int = 0
        self.timestamp = datetime.utcnow()
        self.error: Optional[str] = None
        self.headers: Dict[str, str] = {}
        
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            'url': self.url,
            'status': self.status,
            'success': self.success,
            'title': self.title,
            'links': self.links,
            'depth': self.depth,
            'timestamp': self.timestamp.isoformat(),
            'error': self.error,
            'headers': self.headers
        }


class StealthCrawler:
    """
    Advanced async web crawler with stealth features.
    
    Features:
    - Playwright-based browser automation
    - Stealth mode with fingerprint randomization
    - Concurrent workers
    - Rate limiting
    - Scope management
    - Screenshot capture
    """
    
    def __init__(self, config: Optional[CrawlerConfig] = None):
        self.config = config or CrawlerConfig()
        self.scope_manager = ScopeManager()
        self.rate_limiter = RateLimiter(
            requests_per_second=self.config.requests_per_second,
            adaptive=self.config.adaptive_rate_limit
        )
        self.fingerprint = FingerprintRandomizer()
        
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.visited: Set[str] = set()
        self.queue: asyncio.Queue = asyncio.Queue()
        self.results: List[CrawlResult] = []
        self.running = False
        
    async def initialize(self) -> None:
        """Initialize the browser."""
        logger.info("Initializing StealthCrawler...")
        
        playwright = await async_playwright().start()
        
        # Launch browser
        browser_type = getattr(playwright, self.config.browser_type)
        self.browser = await browser_type.launch(
            headless=self.config.headless,
            args=self.config.browser_args
        )
        
        # Create context with stealth settings
        self.context = await self.browser.new_context(
            viewport={
                'width': self.config.viewport_width,
                'height': self.config.viewport_height
            },
            user_agent=self.fingerprint.get_user_agent() if self.config.user_agent_rotation else None
        )
        
        # Apply stealth scripts
        if self.config.fingerprint_randomization:
            await self._apply_stealth_scripts()
        
        logger.info("Browser initialized successfully")
        
    async def _apply_stealth_scripts(self) -> None:
        """Apply stealth scripts to hide automation."""
        stealth_script = """
        // Override navigator.webdriver
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        });
        
        // Override chrome property
        window.chrome = {
            runtime: {}
        };
        
        // Override permissions
        const originalQuery = window.navigator.permissions.query;
        window.navigator.permissions.query = (parameters) => (
            parameters.name === 'notifications' ?
                Promise.resolve({ state: Notification.permission }) :
                originalQuery(parameters)
        );
        """
        
        await self.context.add_init_script(stealth_script)
        
    async def crawl(self, start_urls: List[str], max_depth: Optional[int] = None) -> List[CrawlResult]:
        """
        Start crawling from given URLs.
        
        Args:
            start_urls: List of starting URLs
            max_depth: Maximum crawl depth (None for unlimited)
            
        Returns:
            List of crawl results
        """
        if not self.browser:
            await self.initialize()
        
        max_depth = max_depth or self.config.max_depth
        
        # Add start URLs to queue
        for url in start_urls:
            normalized = normalize_url(url)
            if self.scope_manager.is_in_scope(normalized):
                await self.queue.put((normalized, 0))
                logger.info(f"Added start URL: {normalized}")
            else:
                logger.warning(f"Start URL out of scope: {normalized}")
        
        # Start workers
        self.running = True
        workers = [
            asyncio.create_task(self._worker(worker_id, max_depth))
            for worker_id in range(self.config.max_workers)
        ]
        
        # Wait for queue to be empty
        await self.queue.join()
        
        # Stop workers
        self.running = False
        for worker in workers:
            worker.cancel()
        
        await asyncio.gather(*workers, return_exceptions=True)
        
        logger.info(f"Crawling completed. Visited {len(self.visited)} URLs")
        return self.results
        
    async def _worker(self, worker_id: int, max_depth: int) -> None:
        """Worker coroutine to process URLs from queue."""
        logger.debug(f"Worker {worker_id} started")
        
        while self.running:
            try:
                # Get URL from queue with timeout
                url, depth = await asyncio.wait_for(self.queue.get(), timeout=1.0)
                
                try:
                    # Skip if already visited
                    if url in self.visited:
                        continue
                    
                    self.visited.add(url)
                    
                    # Respect rate limit
                    await self.rate_limiter.acquire()
                    
                    # Crawl the page
                    result = await self._crawl_page(url, depth)
                    self.results.append(result)
                    
                    # Add new links to queue if within depth
                    if depth < max_depth and result.success:
                        for link in result.links:
                            normalized = normalize_url(link)
                            if normalized not in self.visited and self.scope_manager.is_in_scope(normalized):
                                await self.queue.put((normalized, depth + 1))
                    
                except Exception as e:
                    logger.error(f"Worker {worker_id} error processing {url}: {e}")
                finally:
                    self.queue.task_done()
                    
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Worker {worker_id} unexpected error: {e}")
                
        logger.debug(f"Worker {worker_id} stopped")
        
    async def _crawl_page(self, url: str, depth: int) -> CrawlResult:
        """
        Crawl a single page.
        
        Args:
            url: URL to crawl
            depth: Current depth
            
        Returns:
            CrawlResult object
        """
        result = CrawlResult(url)
        result.depth = depth
        
        page: Optional[Page] = None
        
        try:
            logger.info(f"Crawling: {url} (depth: {depth})")
            
            # Create new page
            page = await self.context.new_page()
            
            # Navigate to URL
            response = await page.goto(url, timeout=self.config.timeout, wait_until='networkidle')
            
            if response:
                result.status = response.status
                result.success = 200 <= response.status < 300
                result.headers = dict(response.headers)
            
            # Get page content
            result.title = await page.title()
            result.html = await page.content()
            
            # Extract links
            result.links = extract_links(result.html, url)
            
            # Take screenshot if configured
            if self.config.save_screenshots and result.success:
                result.screenshot = await page.screenshot(full_page=False)
            
            logger.info(f"Successfully crawled: {url} (status: {result.status}, links: {len(result.links)})")
            
        except Exception as e:
            result.error = str(e)
            logger.error(f"Failed to crawl {url}: {e}")
        finally:
            if page:
                await page.close()
        
        return result
        
    async def close(self) -> None:
        """Close the browser and cleanup resources."""
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        logger.info("Browser closed")
