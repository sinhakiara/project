"""Redis-based distributed crawling for StealthCrawler v17."""

import asyncio
import json
import logging
from typing import Optional, List, Any
from datetime import datetime
import redis.asyncio as redis

from config import CrawlerConfig
from stealth_crawler import StealthCrawler, CrawlResult

logger = logging.getLogger(__name__)


class DistributedCrawler:
    """
    Distributed crawler using Redis for coordination.
    
    Features:
    - Shared URL queue
    - Distributed visited set
    - Result aggregation
    - Worker coordination
    """
    
    def __init__(self, config: CrawlerConfig, worker_id: str = 'worker-1'):
        self.config = config
        self.worker_id = worker_id
        self.redis_client: Optional[redis.Redis] = None
        self.crawler = StealthCrawler(config)
        
        # Redis keys
        self.queue_key = 'stealth:queue'
        self.visited_key = 'stealth:visited'
        self.results_key = 'stealth:results'
        self.workers_key = 'stealth:workers'
        
    async def connect(self) -> None:
        """Connect to Redis."""
        try:
            self.redis_client = await redis.from_url(
                f"redis://{self.config.redis_host}:{self.config.redis_port}",
                password=self.config.redis_password,
                db=self.config.redis_db,
                decode_responses=False
            )
            
            # Test connection
            await self.redis_client.ping()
            logger.info(f"Connected to Redis at {self.config.redis_host}:{self.config.redis_port}")
            
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise
    
    async def register_worker(self) -> None:
        """Register this worker in Redis."""
        try:
            worker_info = {
                'id': self.worker_id,
                'started_at': datetime.utcnow().isoformat(),
                'status': 'active'
            }
            
            await self.redis_client.hset(
                self.workers_key,
                self.worker_id,
                json.dumps(worker_info)
            )
            
            logger.info(f"Worker registered: {self.worker_id}")
            
        except Exception as e:
            logger.error(f"Failed to register worker: {e}")
    
    async def unregister_worker(self) -> None:
        """Unregister this worker from Redis."""
        try:
            await self.redis_client.hdel(self.workers_key, self.worker_id)
            logger.info(f"Worker unregistered: {self.worker_id}")
        except Exception as e:
            logger.error(f"Failed to unregister worker: {e}")
    
    async def add_urls(self, urls: List[str], depth: int = 0) -> None:
        """
        Add URLs to distributed queue.
        
        Args:
            urls: List of URLs to add
            depth: Current depth
        """
        try:
            for url in urls:
                # Check if already visited
                is_visited = await self.redis_client.sismember(
                    self.visited_key,
                    url.encode()
                )
                
                if not is_visited:
                    item = json.dumps({'url': url, 'depth': depth})
                    await self.redis_client.rpush(self.queue_key, item)
                    
            logger.info(f"Added {len(urls)} URLs to queue")
            
        except Exception as e:
            logger.error(f"Failed to add URLs: {e}")
    
    async def get_url(self, timeout: int = 5) -> Optional[tuple]:
        """
        Get next URL from distributed queue.
        
        Args:
            timeout: Timeout in seconds
            
        Returns:
            Tuple of (url, depth) or None
        """
        try:
            # Block and wait for URL
            result = await self.redis_client.blpop(self.queue_key, timeout=timeout)
            
            if result:
                _, item = result
                data = json.loads(item.decode())
                return data['url'], data['depth']
                
        except Exception as e:
            logger.error(f"Failed to get URL: {e}")
        
        return None
    
    async def mark_visited(self, url: str) -> None:
        """Mark URL as visited in distributed set."""
        try:
            await self.redis_client.sadd(self.visited_key, url.encode())
        except Exception as e:
            logger.error(f"Failed to mark visited: {e}")
    
    async def is_visited(self, url: str) -> bool:
        """Check if URL has been visited."""
        try:
            return await self.redis_client.sismember(self.visited_key, url.encode())
        except Exception as e:
            logger.error(f"Failed to check visited: {e}")
            return False
    
    async def save_result(self, result: CrawlResult) -> None:
        """Save crawl result to Redis."""
        try:
            result_data = json.dumps(result.to_dict())
            await self.redis_client.rpush(self.results_key, result_data)
        except Exception as e:
            logger.error(f"Failed to save result: {e}")
    
    async def get_results(self) -> List[dict]:
        """Get all crawl results."""
        try:
            results = await self.redis_client.lrange(self.results_key, 0, -1)
            return [json.loads(r.decode()) for r in results]
        except Exception as e:
            logger.error(f"Failed to get results: {e}")
            return []
    
    async def get_queue_size(self) -> int:
        """Get size of URL queue."""
        try:
            return await self.redis_client.llen(self.queue_key)
        except Exception as e:
            logger.error(f"Failed to get queue size: {e}")
            return 0
    
    async def get_visited_count(self) -> int:
        """Get count of visited URLs."""
        try:
            return await self.redis_client.scard(self.visited_key)
        except Exception as e:
            logger.error(f"Failed to get visited count: {e}")
            return 0
    
    async def run_master(self, start_urls: List[str], max_depth: int = 5) -> None:
        """
        Run as master node - initialize queue.
        
        Args:
            start_urls: Starting URLs
            max_depth: Maximum crawl depth
        """
        await self.connect()
        
        # Clear existing data
        await self.redis_client.delete(self.queue_key)
        await self.redis_client.delete(self.visited_key)
        await self.redis_client.delete(self.results_key)
        
        logger.info("Master node initialized - cleared existing data")
        
        # Add start URLs
        await self.add_urls(start_urls, depth=0)
        
        logger.info(f"Added {len(start_urls)} start URLs")
        logger.info("Master setup complete - workers can now connect")
    
    async def run_worker(self) -> None:
        """Run as worker node - process URLs from queue."""
        await self.connect()
        await self.register_worker()
        await self.crawler.initialize()
        
        try:
            logger.info(f"Worker {self.worker_id} started")
            
            while True:
                # Get URL from queue
                item = await self.get_url(timeout=5)
                
                if not item:
                    # Check if queue is empty
                    queue_size = await self.get_queue_size()
                    if queue_size == 0:
                        logger.info("Queue is empty - worker stopping")
                        break
                    continue
                
                url, depth = item
                
                # Mark as visited
                await self.mark_visited(url)
                
                # Crawl the page
                result = await self.crawler._crawl_page(url, depth)
                
                # Save result
                await self.save_result(result)
                
                # Add new links to queue if successful
                if result.success and depth < self.config.max_depth:
                    filtered_links = self.crawler.scope_manager.filter_urls(result.links)
                    await self.add_urls(filtered_links, depth + 1)
                
                # Log progress
                visited = await self.get_visited_count()
                queue = await self.get_queue_size()
                logger.info(f"Progress: visited={visited}, queue={queue}")
                
        finally:
            await self.unregister_worker()
            await self.crawler.close()
    
    async def close(self) -> None:
        """Close connections."""
        if self.redis_client:
            await self.redis_client.close()
