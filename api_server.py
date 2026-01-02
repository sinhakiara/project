"""FastAPI REST API server for StealthCrawler v17."""

import asyncio
import logging
from typing import List, Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
import uvicorn

from config import CrawlerConfig
from stealth_crawler import StealthCrawler
from scope_manager import create_scope_manager

logger = logging.getLogger(__name__)

app = FastAPI(title="StealthCrawler API", version="17.0.0")

# Store active crawlers
active_crawlers = {}


class CrawlRequest(BaseModel):
    """Crawl request model."""
    start_urls: List[str]
    max_depth: int = 5
    in_scope: List[str] = []
    out_of_scope: List[str] = []


class CrawlStatus(BaseModel):
    """Crawl status model."""
    crawl_id: str
    status: str
    visited_count: int
    queue_size: int
    results_count: int


class CrawlResult(BaseModel):
    """Crawl result model."""
    url: str
    status: int
    success: bool
    title: Optional[str] = None
    depth: int
    timestamp: str


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "StealthCrawler API",
        "version": "17.0.0",
        "status": "running"
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.post("/crawl/start")
async def start_crawl(request: CrawlRequest, background_tasks: BackgroundTasks):
    """
    Start a new crawl job.
    
    Args:
        request: Crawl request parameters
        background_tasks: FastAPI background tasks
        
    Returns:
        Crawl job information
    """
    try:
        # Generate crawl ID
        from utils import generate_id
        crawl_id = generate_id("crawl-")
        
        # Create crawler
        config = CrawlerConfig()
        crawler = StealthCrawler(config)
        
        # Configure scope
        scope_manager = create_scope_manager(
            in_scope=request.in_scope,
            out_of_scope=request.out_of_scope
        )
        crawler.scope_manager = scope_manager
        
        # Store crawler
        active_crawlers[crawl_id] = {
            'crawler': crawler,
            'status': 'starting',
            'config': request
        }
        
        # Start crawl in background
        background_tasks.add_task(
            run_crawl,
            crawl_id,
            crawler,
            request.start_urls,
            request.max_depth
        )
        
        logger.info(f"Started crawl job: {crawl_id}")
        
        return {
            "crawl_id": crawl_id,
            "status": "started",
            "start_urls": request.start_urls,
            "max_depth": request.max_depth
        }
        
    except Exception as e:
        logger.error(f"Failed to start crawl: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def run_crawl(crawl_id: str, crawler: StealthCrawler, start_urls: List[str], max_depth: int):
    """Background task to run crawl."""
    try:
        active_crawlers[crawl_id]['status'] = 'running'
        
        await crawler.initialize()
        results = await crawler.crawl(start_urls, max_depth=max_depth)
        
        active_crawlers[crawl_id]['status'] = 'completed'
        active_crawlers[crawl_id]['results'] = results
        
        await crawler.close()
        
        logger.info(f"Crawl {crawl_id} completed with {len(results)} results")
        
    except Exception as e:
        logger.error(f"Crawl {crawl_id} failed: {e}")
        active_crawlers[crawl_id]['status'] = 'failed'
        active_crawlers[crawl_id]['error'] = str(e)


@app.get("/crawl/{crawl_id}/status")
async def get_crawl_status(crawl_id: str):
    """
    Get status of a crawl job.
    
    Args:
        crawl_id: Crawl job ID
        
    Returns:
        Crawl status information
    """
    if crawl_id not in active_crawlers:
        raise HTTPException(status_code=404, detail="Crawl not found")
    
    job = active_crawlers[crawl_id]
    crawler = job['crawler']
    
    return {
        "crawl_id": crawl_id,
        "status": job['status'],
        "visited_count": len(crawler.visited),
        "queue_size": crawler.queue.qsize(),
        "results_count": len(crawler.results)
    }


@app.get("/crawl/{crawl_id}/results")
async def get_crawl_results(crawl_id: str, limit: int = 100, offset: int = 0):
    """
    Get results of a crawl job.
    
    Args:
        crawl_id: Crawl job ID
        limit: Maximum number of results to return
        offset: Offset for pagination
        
    Returns:
        List of crawl results
    """
    if crawl_id not in active_crawlers:
        raise HTTPException(status_code=404, detail="Crawl not found")
    
    job = active_crawlers[crawl_id]
    
    if job['status'] not in ['completed', 'running']:
        raise HTTPException(status_code=400, detail="Crawl not ready")
    
    crawler = job['crawler']
    results = crawler.results[offset:offset + limit]
    
    return {
        "crawl_id": crawl_id,
        "total": len(crawler.results),
        "limit": limit,
        "offset": offset,
        "results": [r.to_dict() for r in results]
    }


@app.delete("/crawl/{crawl_id}")
async def stop_crawl(crawl_id: str):
    """
    Stop and delete a crawl job.
    
    Args:
        crawl_id: Crawl job ID
        
    Returns:
        Deletion confirmation
    """
    if crawl_id not in active_crawlers:
        raise HTTPException(status_code=404, detail="Crawl not found")
    
    job = active_crawlers[crawl_id]
    
    # Stop crawler if running
    if job['status'] == 'running':
        job['crawler'].running = False
    
    # Close browser
    if job['crawler'].browser:
        await job['crawler'].close()
    
    # Remove from active crawlers
    del active_crawlers[crawl_id]
    
    logger.info(f"Crawl {crawl_id} stopped and deleted")
    
    return {"status": "deleted", "crawl_id": crawl_id}


@app.get("/crawl/list")
async def list_crawls():
    """
    List all active crawl jobs.
    
    Returns:
        List of crawl jobs
    """
    jobs = []
    
    for crawl_id, job in active_crawlers.items():
        jobs.append({
            "crawl_id": crawl_id,
            "status": job['status'],
            "visited_count": len(job['crawler'].visited),
            "results_count": len(job['crawler'].results)
        })
    
    return {"jobs": jobs, "total": len(jobs)}


async def start_api_server(config: CrawlerConfig):
    """
    Start the API server.
    
    Args:
        config: Crawler configuration
    """
    logger.info(f"Starting API server on {config.api_host}:{config.api_port}")
    
    config_uvicorn = uvicorn.Config(
        app,
        host=config.api_host,
        port=config.api_port,
        log_level=config.log_level.lower()
    )
    
    server = uvicorn.Server(config_uvicorn)
    await server.serve()
