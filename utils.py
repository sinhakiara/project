"""Common utility functions for StealthCrawler v17."""

import re
import os
import json
import hashlib
import logging
import asyncio
from datetime import datetime
from urllib.parse import urlparse, urljoin, urlunparse, parse_qs, urlencode
from typing import Optional, Dict, Any, List, Set
from pathlib import Path

logger = logging.getLogger(__name__)


def setup_logging(level: str = "INFO") -> logging.Logger:
    """Setup logging configuration."""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    return logging.getLogger("stealth_crawler")


def normalize_url(url: str) -> str:
    """
    Normalize a URL by removing fragments, sorting query parameters, etc.
    Args:
        url: The URL to normalize
    Returns:
        Normalized URL string
    """
    try:
        parsed = urlparse(url.lower().strip())
        # Remove default ports
        netloc = parsed.netloc
        if netloc.endswith(":80") and parsed.scheme == "http":
            netloc = netloc[:-3]
        elif netloc.endswith(":443") and parsed.scheme == "https":
            netloc = netloc[:-4]
        # Normalize path
        path = parsed.path or "/"
        if not path.startswith("/"):
            path = "/" + path
        path = re.sub(r"/+", "/", path)  # Remove duplicate slashes
        # Sort query parameters
        query = ""
        if parsed.query:
            params = parse_qs(parsed.query, keep_blank_values=True)
            sorted_params = sorted(params.items())
            query = urlencode(sorted_params, doseq=True)
        # Remove fragment
        normalized = urlunparse((parsed.scheme, netloc, path, "", query, ""))
        # Remove trailing slash from path (except for root)
        if normalized.endswith("/") and len(urlparse(normalized).path) > 1:
            normalized = normalized.rstrip("/")
        return normalized
    except Exception as e:
        logger.warning(f"Failed to normalize URL {url}: {e}")
        return url


def get_domain(url: str) -> Optional[str]:
    """
    Extract domain from URL.
    Args:
        url: The URL to extract domain from
    Returns:
        Domain string or None
    """
    try:
        parsed = urlparse(url)
        return parsed.netloc.lower() if parsed.netloc else None
    except Exception:
        return None


def extract_domain(url: str) -> str:
    """Extract domain from URL."""
    parsed = urlparse(url)
    return parsed.netloc.lower()


def get_base_domain(domain: str) -> str:
    """
    Get base domain from a full domain (e.g., 'api.example.com' -> 'example.com').
    Args:
        domain: Full domain name
    Returns:
        Base domain
    """
    parts = domain.split('.')
    if len(parts) >= 2:
        return '.'.join(parts[-2:])
    return domain


def extract_base_domain(url: str) -> str:
    """Extract base domain (without subdomains)."""
    domain = extract_domain(url)
    parts = domain.split(".")
    if len(parts) >= 2:
        return ".".join(parts[-2:])
    return domain


def is_same_domain(url1: str, url2: str) -> bool:
    """Check if two URLs are on the same domain."""
    return extract_domain(url1) == extract_domain(url2)


def is_valid_url(url: str) -> bool:
    """
    Check if a URL is valid.
    Args:
        url: URL to validate
    Returns:
        True if valid, False otherwise
    """
    try:
        parsed = urlparse(url)
        return bool(parsed.scheme and parsed.netloc)
    except Exception:
        return False


def url_hash(url: str) -> str:
    """Generate hash for URL."""
    normalized = normalize_url(url)
    return hashlib.md5(normalized.encode()).hexdigest()[:16]


def hash_url(url: str) -> str:
    """
    Generate a hash for a URL.
    Args:
        url: URL to hash
    Returns:
        SHA256 hash of the URL
    """
    return hashlib.sha256(url.encode()).hexdigest()


def content_hash(content: str) -> str:
    """Generate hash for content."""
    return hashlib.sha256(content.encode()).hexdigest()[:32]


def resolve_url(base_url: str, relative_url: str) -> str:
    """Resolve relative URL against base URL."""
    return urljoin(base_url, relative_url)


def extract_links(html: str, base_url: str) -> List[str]:
    """
    Extract all links from HTML content.
    Args:
        html: HTML content
        base_url: Base URL for resolving relative links
    Returns:
        List of absolute URLs
    """
    links = set()
    # Find href attributes
    href_pattern = re.compile(r'href=["\']([^"\']+)["\']', re.IGNORECASE)
    for match in href_pattern.finditer(html):
        url = match.group(1)
        if url and not url.startswith(("#", "javascript:", "mailto:", "tel:")):
            resolved = resolve_url(base_url, url)
            if is_valid_url(resolved):
                links.add(normalize_url(resolved))
    # Optionally extract src from iframes etc. via BeautifulSoup for richer case
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, 'lxml')
        for tag in soup.find_all('iframe', src=True):
            src = tag['src']
            absolute_url = urljoin(base_url, src)
            if is_valid_url(absolute_url):
                links.add(normalize_url(absolute_url))
    except Exception as e:
        logger.debug(f"BeautifulSoup not available or failed: {e}")
    return list(links)


def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename by removing invalid characters.
    Args:
        filename: Original filename
    Returns:
        Sanitized filename
    """
    # Remove invalid characters
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Limit length
    if len(sanitized) > 200:
        sanitized = sanitized[:200]
    return sanitized


def parse_content_type(content_type: str) -> Dict[str, str]:
    """
    Parse Content-Type header.
    Args:
        content_type: Content-Type header value
    Returns:
        Dictionary with 'type' and 'charset' keys
    """
    parts = content_type.split(';')
    result = {'type': parts[0].strip().lower()}
    for part in parts[1:]:
        if '=' in part:
            key, value = part.split('=', 1)
            if key.strip().lower() == 'charset':
                result['charset'] = value.strip().strip('"')
    return result


def format_bytes(bytes_count: int) -> str:
    """
    Format bytes into human-readable format.
    Args:
        bytes_count: Number of bytes
    Returns:
        Formatted string (e.g., "1.5 MB")
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_count < 1024.0:
            return f"{bytes_count:.2f} {unit}"
        bytes_count /= 1024.0
    return f"{bytes_count:.2f} PB"


def safe_get(data: Dict[str, Any], path: str, default: Any = None) -> Any:
    """
    Safely get a nested value from a dictionary.
    Args:
        data: Dictionary to search
        path: Dot-separated path (e.g., "user.profile.name")
        default: Default value if path not found
    Returns:
        Value at path or default
    """
    keys = path.split('.')
    current = data
    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return default
    return current


def ensure_dir(path: str) -> Path:
    """Ensure directory exists."""
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def save_json(data: Any, filepath: str) -> None:
    """Save data to JSON file."""
    ensure_dir(os.path.dirname(filepath) or ".")
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str, ensure_ascii=False)


def load_json(filepath: str) -> Any:
    """Load data from JSON file."""
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def timestamp() -> str:
    """Get current timestamp string."""
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def human_readable_size(size_bytes: int) -> str:
    """Convert bytes to human readable format."""
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.2f} TB"


def human_readable_duration(seconds: float) -> str:
    """Convert seconds to human readable format."""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}m"
    else:
        hours = seconds / 3600
        return f"{hours:.1f}h"


async def retry_async(
    func,
    max_retries: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,)
):
    """Retry async function with exponential backoff."""
    last_exception = None
    current_delay = delay
    for attempt in range(max_retries):
        try:
            return await func()
        except exceptions as e:
            last_exception = e
            if attempt < max_retries - 1:
                await asyncio.sleep(current_delay)
                current_delay *= backoff
    raise last_exception


def chunk_list(lst: List[Any], chunk_size: int) -> List[List[Any]]:
    """Split list into chunks."""
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


def flatten_list(nested: List[List[Any]]) -> List[Any]:
    """Flatten nested list."""
    return [item for sublist in nested for item in sublist]


def deduplicate(items: List[Any], key=None) -> List[Any]:
    """Remove duplicates while preserving order."""
    seen = set()
    result = []
    for item in items:
        k = key(item) if key else item
        if k not in seen:
            seen.add(k)
            result.append(item)
    return result
