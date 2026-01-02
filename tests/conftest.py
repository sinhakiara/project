"""Pytest configuration and fixtures."""

import pytest
import asyncio
from typing import Generator


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def sample_urls():
    """Sample URLs for testing."""
    return [
        'https://example.com',
        'https://api.example.com',
        'https://admin.example.com',
        'https://test.api.example.com',
    ]


@pytest.fixture
def sample_html():
    """Sample HTML for testing."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Test Page</title>
    </head>
    <body>
        <h1>Test Page</h1>
        <a href="https://example.com/page1">Page 1</a>
        <a href="https://example.com/page2">Page 2</a>
        <a href="https://external.com/page">External</a>
    </body>
    </html>
    """


@pytest.fixture
def crawler_config():
    """Sample crawler configuration."""
    from config import CrawlerConfig
    return CrawlerConfig()
