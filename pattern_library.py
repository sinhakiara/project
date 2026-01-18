"""Self-learning URL pattern library for StealthCrawler v17."""

import re
from typing import Dict, List, Set
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


class PatternLibrary:
    """
    Self-learning URL pattern detector.
    
    Features:
    - Automatic pattern detection from crawled URLs
    - Pattern-based URL classification
    - Dynamic pattern updates
    """
    
    def __init__(self):
        self.patterns: Dict[str, List[str]] = defaultdict(list)
        self.url_counts: Dict[str, int] = defaultdict(int)
        self.learned_patterns: Set[str] = set()
        
    def add_url(self, url: str, category: str = 'default') -> None:
        """
        Add a URL and learn its pattern.
        
        Args:
            url: URL to add
            category: Category for the URL
        """
        self.url_counts[url] += 1
        self.patterns[category].append(url)
        
        # Extract pattern
        pattern = self._extract_pattern(url)
        if pattern:
            self.learned_patterns.add(pattern)
            logger.debug(f"Learned pattern: {pattern}")
    
    def _extract_pattern(self, url: str) -> str:
        """
        Extract a pattern from a URL by replacing dynamic parts.
        
        Args:
            url: URL to extract pattern from
            
        Returns:
            Pattern string
        """
        # Replace numbers with placeholder
        pattern = re.sub(r'\d+', '{id}', url)
        
        # Replace UUIDs
        pattern = re.sub(
            r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}',
            '{uuid}',
            pattern,
            flags=re.IGNORECASE
        )
        
        # Replace hashes (32+ hex chars)
        pattern = re.sub(r'[0-9a-f]{32,}', '{hash}', pattern, flags=re.IGNORECASE)
        
        return pattern
    
    def matches_pattern(self, url: str, pattern: str) -> bool:
        """
        Check if URL matches a pattern.
        
        Args:
            url: URL to check
            pattern: Pattern to match against
            
        Returns:
            True if matches, False otherwise
        """
        extracted = self._extract_pattern(url)
        return extracted == pattern
    
    def get_patterns(self, category: str = 'default') -> List[str]:
        """Get all learned patterns for a category."""
        return list(set(self._extract_pattern(url) for url in self.patterns[category]))
    
    def get_statistics(self) -> Dict:
        """Get pattern statistics."""
        return {
            'total_urls': sum(self.url_counts.values()),
            'unique_urls': len(self.url_counts),
            'learned_patterns': len(self.learned_patterns),
            'categories': len(self.patterns)
        }
    def create_api_interceptor(self, *args, **kwargs):
        # Provide real logic if you know what should happen,
        # or just return None/log for now to unblock crawling:
        if hasattr(self, "logger"):
            self.logger.debug("PatternLibrary.create_api_interceptor() called (stub)")
        return None   
