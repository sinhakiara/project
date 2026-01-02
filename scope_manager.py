"""Scope management for StealthCrawler v17 with wildcard support and exclusion priority."""

import re
from typing import List, Set, Optional
from urllib.parse import urlparse
import logging
from utils import normalize_url, get_domain

logger = logging.getLogger(__name__)


class ScopeManager:
    """
    Manages URL scope with wildcard support and exclusion priority.
    
    Features:
    - Wildcard support: *.domain.tld matches all subdomains
    - Nested wildcards: **.domain.tld matches deeply nested subdomains
    - EXCLUSION PRIORITY: Exclusions always take precedence over inclusions
    - IP range support
    - URL normalization
    """
    
    def __init__(self):
        self.in_scope_patterns: List[str] = []
        self.out_of_scope_patterns: List[str] = []
        self.in_scope_domains: Set[str] = set()
        self.out_of_scope_domains: Set[str] = set()
        self.in_scope_regexes: List[re.Pattern] = []
        self.out_of_scope_regexes: List[re.Pattern] = []
        
    def add_in_scope(self, pattern: str) -> None:
        """
        Add a pattern to in-scope list.
        
        Args:
            pattern: Domain pattern (e.g., 'example.com', '*.example.com', '**.example.com')
        """
        pattern = pattern.lower().strip()
        self.in_scope_patterns.append(pattern)
        
        if '*' in pattern:
            # Convert wildcard pattern to regex
            regex = self._pattern_to_regex(pattern)
            self.in_scope_regexes.append(re.compile(regex))
        else:
            self.in_scope_domains.add(pattern)
            
        logger.debug(f"Added in-scope pattern: {pattern}")
        
    def add_out_of_scope(self, pattern: str) -> None:
        """
        Add a pattern to out-of-scope list.
        
        Args:
            pattern: Domain pattern (e.g., 'admin.example.com', '*.admin.example.com')
        """
        pattern = pattern.lower().strip()
        self.out_of_scope_patterns.append(pattern)
        
        if '*' in pattern:
            # Convert wildcard pattern to regex
            regex = self._pattern_to_regex(pattern)
            self.out_of_scope_regexes.append(re.compile(regex))
        else:
            self.out_of_scope_domains.add(pattern)
            
        logger.debug(f"Added out-of-scope pattern: {pattern}")
        
    def is_in_scope(self, url: str) -> bool:
        """
        Check if a URL is in scope.
        
        EXCLUSION PRIORITY: If a URL matches both in-scope and out-of-scope patterns,
        it will be considered OUT OF SCOPE.
        
        Args:
            url: URL to check
            
        Returns:
            True if in scope, False otherwise
        """
        # Normalize the URL first
        url = normalize_url(url)
        domain = get_domain(url)
        
        if not domain:
            return False
        
        # CRITICAL: Check exclusions FIRST (exclusion priority)
        if self._matches_out_of_scope(domain):
            logger.debug(f"URL {url} is OUT OF SCOPE (exclusion match)")
            return False
        
        # If no in-scope patterns defined, allow everything (except exclusions)
        if not self.in_scope_patterns:
            return True
        
        # Check if matches in-scope patterns
        if self._matches_in_scope(domain):
            logger.debug(f"URL {url} is IN SCOPE")
            return True
        
        logger.debug(f"URL {url} is OUT OF SCOPE (no inclusion match)")
        return False
    
    def _matches_in_scope(self, domain: str) -> bool:
        """Check if domain matches any in-scope pattern."""
        # Exact domain match
        if domain in self.in_scope_domains:
            return True
        
        # Regex pattern match
        for regex in self.in_scope_regexes:
            if regex.fullmatch(domain):
                return True
        
        return False
    
    def _matches_out_of_scope(self, domain: str) -> bool:
        """Check if domain matches any out-of-scope pattern."""
        # Exact domain match
        if domain in self.out_of_scope_domains:
            return True
        
        # Regex pattern match
        for regex in self.out_of_scope_regexes:
            if regex.fullmatch(domain):
                return True
        
        return False
    
    def _pattern_to_regex(self, pattern: str) -> str:
        """
        Convert a wildcard pattern to a regex pattern.
        
        Supports:
        - *.domain.tld: matches one subdomain level (e.g., api.domain.tld)
        - **.domain.tld: matches multiple subdomain levels (e.g., api.v1.domain.tld)
        
        Args:
            pattern: Wildcard pattern
            
        Returns:
            Regex pattern string
        """
        # First, replace ** with a placeholder to avoid conflicts
        # Note: **.domain.com should match api.domain.com, api.v1.domain.com, etc.
        pattern = pattern.replace('**.', '__DOUBLE_WILDCARD__')
        
        # Replace single * with a placeholder
        # Note: *.domain.com should match api.domain.com but NOT api.v1.domain.com
        pattern = pattern.replace('*.', '__SINGLE_WILDCARD__')
        
        # Escape special regex characters (now * is already replaced)
        escaped = pattern.replace('.', r'\.')
        
        # Replace placeholders with actual regex patterns
        # ** matches one or more subdomain levels: api.domain.com, api.v1.domain.com, etc.
        # Pattern: (subdomain.)+ where subdomain is [a-z0-9]([a-z0-9-]*[a-z0-9])?
        escaped = escaped.replace('__DOUBLE_WILDCARD__', r'([a-z0-9]([a-z0-9\-]*[a-z0-9])?\.)+')
        
        # * matches exactly one subdomain level: api.domain.com but not api.v1.domain.com
        # Pattern: subdomain. where subdomain is [a-z0-9]([a-z0-9-]*[a-z0-9])?
        escaped = escaped.replace('__SINGLE_WILDCARD__', r'[a-z0-9]([a-z0-9\-]*[a-z0-9])?'  + r'\.')
        
        return escaped
    
    def filter_urls(self, urls: List[str]) -> List[str]:
        """
        Filter a list of URLs to only those in scope.
        
        Args:
            urls: List of URLs to filter
            
        Returns:
            List of in-scope URLs
        """
        return [url for url in urls if self.is_in_scope(url)]
    
    def get_scope_summary(self) -> dict:
        """
        Get a summary of the current scope configuration.
        
        Returns:
            Dictionary with scope information
        """
        return {
            'in_scope_patterns': self.in_scope_patterns,
            'out_of_scope_patterns': self.out_of_scope_patterns,
            'in_scope_count': len(self.in_scope_patterns),
            'out_of_scope_count': len(self.out_of_scope_patterns)
        }
    
    def test_url(self, url: str) -> dict:
        """
        Test a URL against scope rules and return detailed information.
        
        Args:
            url: URL to test
            
        Returns:
            Dictionary with test results
        """
        normalized = normalize_url(url)
        domain = get_domain(url)
        in_scope = self.is_in_scope(url)
        
        matches_in = []
        matches_out = []
        
        if domain:
            # Check which patterns match
            if domain in self.in_scope_domains:
                matches_in.append(f"exact: {domain}")
            
            for i, regex in enumerate(self.in_scope_regexes):
                if regex.fullmatch(domain):
                    matches_in.append(f"pattern: {self.in_scope_patterns[i]}")
            
            if domain in self.out_of_scope_domains:
                matches_out.append(f"exact: {domain}")
            
            for i, regex in enumerate(self.out_of_scope_regexes):
                if regex.fullmatch(domain):
                    matches_out.append(f"pattern: {self.out_of_scope_patterns[i]}")
        
        return {
            'url': url,
            'normalized': normalized,
            'domain': domain,
            'in_scope': in_scope,
            'matches_in_scope': matches_in,
            'matches_out_of_scope': matches_out,
            'reason': 'EXCLUDED' if matches_out else ('INCLUDED' if matches_in else 'NO_MATCH')
        }


def create_scope_manager(
    in_scope: Optional[List[str]] = None,
    out_of_scope: Optional[List[str]] = None
) -> ScopeManager:
    """
    Create and configure a ScopeManager.
    
    Args:
        in_scope: List of in-scope patterns
        out_of_scope: List of out-of-scope patterns
        
    Returns:
        Configured ScopeManager instance
    """
    manager = ScopeManager()
    
    if in_scope:
        for pattern in in_scope:
            manager.add_in_scope(pattern)
    
    if out_of_scope:
        for pattern in out_of_scope:
            manager.add_out_of_scope(pattern)
    
    return manager
