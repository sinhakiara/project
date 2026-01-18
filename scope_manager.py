"""Scope management for StealthCrawler v18+ with strict and feature-full wildcard/exclusion support."""

from urllib.parse import urlparse
from typing import List, Set, Optional
import logging
from utils import normalize_url

logger = logging.getLogger(__name__)

class ScopeManager:
    """
    Manages URL scope with strict wildcard support and exclusion priority.

    Features:
    - Wildcard support: *.domain.tld matches all direct subdomains only
    - Nested wildcards: **.domain.tld matches root and any subdomain (optional)
    - Exclusion always takes precedence (exclusions checked before inclusions)
    - IP/domain normalization (URL normalization via normalize_url)
    - Accurate hostname-based matching (no regex-based bug risk)
    - Logger/debug info supported
    - Utility helpers: filter_urls, get_scope_summary, test_url, normalize_url
    """

    def __init__(self, in_scope=None, out_scope=None, logger=None):
        self.logger = logger
        self.in_scope_domains: Set[str] = set()           # exact
        self.in_scope_subdomains: Set[str] = set()        # *.domain
        self.in_scope_deep: Set[str] = set()              # **.domain
        self.out_of_scope_domains: Set[str] = set()
        self.out_of_scope_subdomains: Set[str] = set()
        self.out_of_scope_deep: Set[str] = set()
        if in_scope:
            for pat in in_scope:
                self.add_in_scope(pat)
        if out_scope:
            for pat in out_scope:
                self.add_out_of_scope(pat)

    def add_in_scope(self, pattern: str) -> None:
        pattern = pattern.lower().strip()
        if pattern.startswith("**."):
            self.in_scope_deep.add(pattern[3:])
            if self.logger:
                self.logger.debug(f"Added in-scope deep wildcard: {pattern}")
        elif pattern.startswith("*."):
            self.in_scope_subdomains.add(pattern[2:])
            if self.logger:
                self.logger.debug(f"Added in-scope subdomain wildcard: {pattern}")
        else:
            self.in_scope_domains.add(pattern)
            if self.logger:
                self.logger.debug(f"Added in-scope exact: {pattern}")

    def add_out_of_scope(self, pattern: str) -> None:
        pattern = pattern.lower().strip()
        if pattern.startswith("**."):
            self.out_of_scope_deep.add(pattern[3:])
            if self.logger:
                self.logger.debug(f"Added out-of-scope deep wildcard: {pattern}")
        elif pattern.startswith("*."):
            self.out_of_scope_subdomains.add(pattern[2:])
            if self.logger:
                self.logger.debug(f"Added out-of-scope subdomain wildcard: {pattern}")
        else:
            self.out_of_scope_domains.add(pattern)
            if self.logger:
                self.logger.debug(f"Added out-of-scope exact: {pattern}")

    def is_in_scope(self, url: str) -> bool:
        url = normalize_url(url)
        hostname = urlparse(url).hostname or ''
        hostname = hostname.lower()

        # 1. Exclusion priority (deep, subdomain, exact)
        for base in self.out_of_scope_deep:
            if hostname == base or hostname.endswith('.' + base):
                if self.logger:
                    self.logger.debug(f"OUT OF SCOPE (deep exclusion): {hostname} vs {base}")
                return False
        for base in self.out_of_scope_subdomains:
            # Only direct subdomain match (e.g., foo.domain.com)
            parts = hostname.split('.', maxsplit=1)
            if len(parts) == 2 and parts[1] == base:
                if self.logger:
                    self.logger.debug(f"OUT OF SCOPE (subdomain exclusion): {hostname} vs {base}")
                return False
        if hostname in self.out_of_scope_domains:
            if self.logger:
                self.logger.debug(f"OUT OF SCOPE (exact exclusion): {hostname}")
            return False

        # 2. If no inclusions, only exclusions matter (everything else is in scope)
        if not (self.in_scope_domains or self.in_scope_subdomains or self.in_scope_deep):
            return True

        # 3. Inclusion matchers (deep, subdomain, exact)
        for base in self.in_scope_deep:
            if hostname == base or hostname.endswith('.' + base):
                if self.logger:
                    self.logger.debug(f"IN SCOPE (deep): {hostname} vs {base}")
                return True
        for base in self.in_scope_subdomains:
            parts = hostname.split('.', maxsplit=1)
            if len(parts) == 2 and parts[1] == base:
                if self.logger:
                    self.logger.debug(f"IN SCOPE (subdomain): {hostname} vs {base}")
                return True
        if hostname in self.in_scope_domains:
            if self.logger:
                self.logger.debug(f"IN SCOPE (exact): {hostname}")
            return True

        if self.logger:
            self.logger.debug(f"OUT OF SCOPE (no inclusion match): {hostname}")
        return False

    def filter_urls(self, urls: List[str]) -> List[str]:
        return [url for url in urls if self.is_in_scope(url)]

    def get_scope_summary(self) -> dict:
        return {
            'in_scope_patterns': (
                list(self.in_scope_domains)
                + ['*.' + x for x in self.in_scope_subdomains]
                + ['**.' + x for x in self.in_scope_deep]
            ),
            'out_of_scope_patterns': (
                list(self.out_of_scope_domains)
                + ['*.' + x for x in self.out_of_scope_subdomains]
                + ['**.' + x for x in self.out_of_scope_deep]
            ),
            'in_scope_count': len(self.in_scope_domains) + len(self.in_scope_subdomains) + len(self.in_scope_deep),
            'out_of_scope_count': len(self.out_of_scope_domains) + len(self.out_of_scope_subdomains) + len(self.out_of_scope_deep)
        }

    def test_url(self, url: str) -> dict:
        normalized = normalize_url(url)
        hostname = urlparse(url).hostname or ''
        hostname = hostname.lower()
        in_scope = self.is_in_scope(url)
        matches_in = []
        matches_out = []
        if hostname:
            if hostname in self.in_scope_domains:
                matches_in.append(f"exact: {hostname}")
            for sub in self.in_scope_subdomains:
                parts = hostname.split('.', maxsplit=1)
                if len(parts) == 2 and parts[1] == sub:
                    matches_in.append(f"subdomain: {sub}")
            for deep in self.in_scope_deep:
                if hostname == deep or hostname.endswith('.' + deep):
                    matches_in.append(f"deep: {deep}")
            if hostname in self.out_of_scope_domains:
                matches_out.append(f"exact: {hostname}")
            for sub in self.out_of_scope_subdomains:
                parts = hostname.split('.', maxsplit=1)
                if len(parts) == 2 and parts[1] == sub:
                    matches_out.append(f"subdomain: {sub}")
            for deep in self.out_of_scope_deep:
                if hostname == deep or hostname.endswith('.' + deep):
                    matches_out.append(f"deep: {deep}")
        return {
            'url': url,
            'normalized': normalized,
            'hostname': hostname,
            'in_scope': in_scope,
            'matches_in_scope': matches_in,
            'matches_out_of_scope': matches_out,
            'reason': 'EXCLUDED' if matches_out else ('INCLUDED' if matches_in else 'NO_MATCH')
        }

    def normalize_url(self, url, *args, **kwargs):
        return url.strip().rstrip('/')

def create_scope_manager(
    in_scope: Optional[List[str]] = None,
    out_of_scope: Optional[List[str]] = None
) -> ScopeManager:
    manager = ScopeManager()
    if in_scope:
        for pattern in in_scope:
            manager.add_in_scope(pattern)
    if out_of_scope:
        for pattern in out_of_scope:
            manager.add_out_of_scope(pattern)
    return manager
