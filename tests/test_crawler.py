"""Tests for the StealthCrawler."""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from stealth_crawler import StealthCrawler, CrawlResult
from config import CrawlerConfig


class TestCrawlResult:
    """Test CrawlResult class."""
    
    def test_crawl_result_initialization(self):
        """Test CrawlResult initialization."""
        result = CrawlResult("https://example.com", status=200, success=True)
        
        assert result.url == "https://example.com"
        assert result.status == 200
        assert result.success is True
        assert result.title is None
        assert result.html is None
        assert result.links == []
        assert result.depth == 0
    
    def test_crawl_result_to_dict(self):
        """Test CrawlResult to_dict method."""
        result = CrawlResult("https://example.com", status=200, success=True)
        result.title = "Test Page"
        result.depth = 2
        
        data = result.to_dict()
        
        assert data['url'] == "https://example.com"
        assert data['status'] == 200
        assert data['success'] is True
        assert data['title'] == "Test Page"
        assert data['depth'] == 2
        assert 'timestamp' in data


class TestStealthCrawler:
    """Test StealthCrawler class."""
    
    def test_crawler_initialization(self):
        """Test crawler initialization."""
        config = CrawlerConfig()
        crawler = StealthCrawler(config)
        
        assert crawler.config == config
        assert crawler.scope_manager is not None
        assert crawler.rate_limiter is not None
        assert crawler.fingerprint is not None
        assert crawler.browser is None
        assert len(crawler.visited) == 0
        assert len(crawler.results) == 0
        assert crawler.running is False
    
    @pytest.mark.asyncio
    async def test_crawler_initialize(self):
        """Test crawler browser initialization."""
        config = CrawlerConfig()
        config.headless = True
        crawler = StealthCrawler(config)
        
        # Mock Playwright
        with patch('stealth_crawler.async_playwright') as mock_playwright:
            mock_browser = AsyncMock()
            mock_context = AsyncMock()
            
            mock_playwright.return_value.start = AsyncMock()
            mock_playwright.return_value.start.return_value.chromium.launch = AsyncMock(
                return_value=mock_browser
            )
            mock_browser.new_context = AsyncMock(return_value=mock_context)
            
            await crawler.initialize()
            
            # Browser should be initialized
            assert crawler.browser is not None
            assert crawler.context is not None
    
    def test_crawler_visited_tracking(self):
        """Test that crawler tracks visited URLs."""
        crawler = StealthCrawler()
        
        assert len(crawler.visited) == 0
        
        crawler.visited.add("https://example.com")
        crawler.visited.add("https://example.com/page1")
        
        assert len(crawler.visited) == 2
        assert "https://example.com" in crawler.visited
        assert "https://example.com/page1" in crawler.visited
    
    def test_crawler_results_collection(self):
        """Test that crawler collects results."""
        crawler = StealthCrawler()
        
        result1 = CrawlResult("https://example.com", status=200, success=True)
        result2 = CrawlResult("https://example.com/page1", status=200, success=True)
        
        crawler.results.append(result1)
        crawler.results.append(result2)
        
        assert len(crawler.results) == 2
        assert crawler.results[0].url == "https://example.com"
        assert crawler.results[1].url == "https://example.com/page1"


class TestCrawlerIntegration:
    """Integration tests for crawler."""
    
    @pytest.mark.asyncio
    async def test_queue_operations(self):
        """Test queue operations."""
        crawler = StealthCrawler()
        
        # Add items to queue
        await crawler.queue.put(("https://example.com", 0))
        await crawler.queue.put(("https://example.com/page1", 1))
        
        assert crawler.queue.qsize() == 2
        
        # Get items from queue
        url1, depth1 = await crawler.queue.get()
        assert url1 == "https://example.com"
        assert depth1 == 0
        
        url2, depth2 = await crawler.queue.get()
        assert url2 == "https://example.com/page1"
        assert depth2 == 1
        
        assert crawler.queue.qsize() == 0
    
    def test_crawler_config_usage(self):
        """Test that crawler uses config correctly."""
        config = CrawlerConfig()
        config.max_workers = 5
        config.max_depth = 3
        config.timeout = 20000
        
        crawler = StealthCrawler(config)
        
        assert crawler.config.max_workers == 5
        assert crawler.config.max_depth == 3
        assert crawler.config.timeout == 20000
