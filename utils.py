"""Common utility functions for StealthCrawler v17."""

import re
import hashlib
import random
import string
from typing import Optional, Dict, Any, List
from urllib.parse import urlparse, urljoin, urlunparse
import logging

logger = logging.getLogger(__name__)


def normalize_url(url: str) -> str:
    """
    Normalize a URL by removing fragments, sorting query parameters, etc.
    
    Args:
        url: The URL to normalize
        
    Returns:
        Normalized URL string
    """
    try:
        parsed = urlparse(url)
        
        # Remove fragment
        normalized = urlunparse((
            parsed.scheme.lower(),
            parsed.netloc.lower(),
            parsed.path or '/',
            parsed.params,
            parsed.query,
            ''  # Remove fragment
        ))
        
        # Remove trailing slash from path (except for root)
        if normalized.endswith('/') and len(urlparse(normalized).path) > 1:
            normalized = normalized.rstrip('/')
            
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


def generate_id(prefix: str = "") -> str:
    """
    Generate a unique ID.
    
    Args:
        prefix: Optional prefix for the ID
        
    Returns:
        Unique ID string
    """
    random_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=12))
    return f"{prefix}{random_str}" if prefix else random_str


def hash_url(url: str) -> str:
    """
    Generate a hash for a URL.
    
    Args:
        url: URL to hash
        
    Returns:
        SHA256 hash of the URL
    """
    return hashlib.sha256(url.encode()).hexdigest()


def extract_links(html: str, base_url: str) -> List[str]:
    """
    Extract all links from HTML content.
    
    Args:
        html: HTML content
        base_url: Base URL for resolving relative links
        
    Returns:
        List of absolute URLs
    """
    from bs4 import BeautifulSoup
    
    links = []
    try:
        soup = BeautifulSoup(html, 'lxml')
        
        # Extract href from <a> tags
        for tag in soup.find_all('a', href=True):
            href = tag['href']
            absolute_url = urljoin(base_url, href)
            if is_valid_url(absolute_url):
                links.append(normalize_url(absolute_url))
        
        # Extract src from <iframe> tags
        for tag in soup.find_all('iframe', src=True):
            src = tag['src']
            absolute_url = urljoin(base_url, src)
            if is_valid_url(absolute_url):
                links.append(normalize_url(absolute_url))
                
    except Exception as e:
        logger.warning(f"Failed to extract links from HTML: {e}")
    
    return list(set(links))  # Remove duplicates


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
