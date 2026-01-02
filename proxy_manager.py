"""Proxy rotation and health checking for StealthCrawler v17."""

import asyncio
import logging
from typing import List, Optional, Dict
from dataclasses import dataclass
from datetime import datetime, timedelta
import random

logger = logging.getLogger(__name__)


@dataclass
class ProxyInfo:
    """Information about a proxy server."""
    url: str
    protocol: str = 'http'
    username: Optional[str] = None
    password: Optional[str] = None
    health_score: float = 1.0
    last_used: Optional[datetime] = None
    success_count: int = 0
    failure_count: int = 0
    avg_response_time: float = 0.0
    
    def get_proxy_url(self) -> str:
        """Get formatted proxy URL."""
        if self.username and self.password:
            return f"{self.protocol}://{self.username}:{self.password}@{self.url}"
        return f"{self.protocol}://{self.url}"


class ProxyManager:
    """
    Manage proxy rotation with health checking.
    
    Features:
    - Automatic proxy rotation
    - Health monitoring
    - Performance tracking
    - Intelligent selection
    """
    
    def __init__(self, proxy_list_file: Optional[str] = None):
        self.proxies: List[ProxyInfo] = []
        self.current_index = 0
        self._lock = asyncio.Lock()
        
        if proxy_list_file:
            self.load_proxies(proxy_list_file)
    
    def load_proxies(self, filepath: str) -> None:
        """
        Load proxies from file.
        
        File format: protocol://host:port or protocol://user:pass@host:port
        
        Args:
            filepath: Path to proxy list file
        """
        try:
            with open(filepath, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        self.add_proxy(line)
            
            logger.info(f"Loaded {len(self.proxies)} proxies from {filepath}")
        except FileNotFoundError:
            logger.warning(f"Proxy file not found: {filepath}")
        except Exception as e:
            logger.error(f"Failed to load proxies: {e}")
    
    def add_proxy(self, proxy_url: str) -> None:
        """
        Add a proxy to the pool.
        
        Args:
            proxy_url: Proxy URL (e.g., 'http://user:pass@host:port')
        """
        try:
            # Parse proxy URL
            if '://' in proxy_url:
                protocol, rest = proxy_url.split('://', 1)
            else:
                protocol = 'http'
                rest = proxy_url
            
            username = None
            password = None
            
            if '@' in rest:
                auth, host = rest.rsplit('@', 1)
                if ':' in auth:
                    username, password = auth.split(':', 1)
            else:
                host = rest
            
            proxy = ProxyInfo(
                url=host,
                protocol=protocol,
                username=username,
                password=password
            )
            
            self.proxies.append(proxy)
            logger.debug(f"Added proxy: {protocol}://{host}")
            
        except Exception as e:
            logger.error(f"Failed to parse proxy URL {proxy_url}: {e}")
    
    async def get_proxy(self, strategy: str = 'round-robin') -> Optional[ProxyInfo]:
        """
        Get next proxy based on strategy.
        
        Args:
            strategy: Selection strategy ('round-robin', 'random', 'best-health')
            
        Returns:
            ProxyInfo or None
        """
        async with self._lock:
            if not self.proxies:
                return None
            
            if strategy == 'round-robin':
                proxy = self.proxies[self.current_index]
                self.current_index = (self.current_index + 1) % len(self.proxies)
                
            elif strategy == 'random':
                proxy = random.choice(self.proxies)
                
            elif strategy == 'best-health':
                # Sort by health score and choose best
                healthy = sorted(self.proxies, key=lambda p: p.health_score, reverse=True)
                proxy = healthy[0] if healthy else None
                
            else:
                proxy = self.proxies[0]
            
            if proxy:
                proxy.last_used = datetime.utcnow()
            
            return proxy
    
    async def report_success(self, proxy: ProxyInfo, response_time: float) -> None:
        """
        Report successful proxy usage.
        
        Args:
            proxy: Proxy that was used
            response_time: Response time in seconds
        """
        proxy.success_count += 1
        
        # Update average response time
        total_requests = proxy.success_count + proxy.failure_count
        proxy.avg_response_time = (
            (proxy.avg_response_time * (total_requests - 1) + response_time) / total_requests
        )
        
        # Improve health score
        proxy.health_score = min(1.0, proxy.health_score + 0.01)
        
        logger.debug(f"Proxy success: {proxy.url} (health: {proxy.health_score:.2f})")
    
    async def report_failure(self, proxy: ProxyInfo, error: str) -> None:
        """
        Report proxy failure.
        
        Args:
            proxy: Proxy that failed
            error: Error message
        """
        proxy.failure_count += 1
        
        # Decrease health score
        proxy.health_score = max(0.0, proxy.health_score - 0.1)
        
        logger.warning(f"Proxy failure: {proxy.url} - {error} (health: {proxy.health_score:.2f})")
        
        # Remove proxy if too unhealthy
        if proxy.health_score < 0.2:
            self.proxies.remove(proxy)
            logger.warning(f"Removed unhealthy proxy: {proxy.url}")
    
    async def health_check(self, test_url: str = 'http://example.com') -> None:
        """
        Perform health check on all proxies.
        
        Args:
            test_url: URL to test proxies against
        """
        logger.info("Starting proxy health check")
        
        import httpx
        
        for proxy in self.proxies:
            try:
                async with httpx.AsyncClient(proxies=proxy.get_proxy_url(), timeout=10.0) as client:
                    start_time = asyncio.get_event_loop().time()
                    response = await client.get(test_url)
                    response_time = asyncio.get_event_loop().time() - start_time
                    
                    if response.status_code == 200:
                        await self.report_success(proxy, response_time)
                    else:
                        await self.report_failure(proxy, f"Status: {response.status_code}")
                        
            except Exception as e:
                await self.report_failure(proxy, str(e))
        
        logger.info(f"Health check complete. Active proxies: {len(self.proxies)}")
    
    def get_statistics(self) -> Dict:
        """Get proxy pool statistics."""
        if not self.proxies:
            return {
                'total': 0,
                'active': 0,
                'avg_health': 0.0
            }
        
        return {
            'total': len(self.proxies),
            'active': len([p for p in self.proxies if p.health_score > 0.5]),
            'avg_health': sum(p.health_score for p in self.proxies) / len(self.proxies),
            'total_success': sum(p.success_count for p in self.proxies),
            'total_failures': sum(p.failure_count for p in self.proxies)
        }
