"""CLI interface for StealthCrawler v17."""

import argparse
import asyncio
import logging
import sys
from typing import List

from config import CrawlerConfig, get_config
from stealth_crawler import StealthCrawler
from scope_manager import create_scope_manager
from checkpoint import CheckpointManager
from distributed import DistributedCrawler
from api_server import start_api_server
from exporters import export_results


def setup_logging(log_level: str) -> None:
    """Setup logging configuration."""
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('crawler.log')
        ]
    )


async def crawl_command(args) -> None:
    """Execute the crawl command."""
    config = get_config()
    config.log_level = args.log_level
    setup_logging(config.log_level)
    
    logger = logging.getLogger(__name__)
    logger.info("Starting StealthCrawler v17")
    
    # Create scope manager
    scope_manager = create_scope_manager(
        in_scope=args.in_scope,
        out_of_scope=args.out_of_scope
    )
    
    # Create crawler
    crawler = StealthCrawler(config)
    crawler.scope_manager = scope_manager
    
    try:
        # Initialize and crawl
        await crawler.initialize()
        results = await crawler.crawl(args.urls, max_depth=args.depth)
        
        # Export results
        if args.output:
            export_results(results, args.output, format=args.format)
            logger.info(f"Results exported to {args.output}")
        
        logger.info(f"Crawl completed: {len(results)} pages crawled")
        
    finally:
        await crawler.close()


async def distributed_command(args) -> None:
    """Execute the distributed crawl command."""
    config = get_config()
    config.distributed_mode = True
    setup_logging(config.log_level)
    
    logger = logging.getLogger(__name__)
    logger.info("Starting distributed crawler")
    
    # Create distributed crawler
    crawler = DistributedCrawler(config, worker_id=args.worker_id)
    
    try:
        if args.master:
            # Run as master
            await crawler.run_master(args.urls, max_depth=args.depth)
        else:
            # Run as worker
            await crawler.run_worker()
    finally:
        await crawler.close()


async def server_command(args) -> None:
    """Execute the API server command."""
    config = get_config()
    config.api_enabled = True
    config.api_port = args.port
    config.api_host = args.host
    setup_logging(config.log_level)
    
    logger = logging.getLogger(__name__)
    logger.info(f"Starting API server on {args.host}:{args.port}")
    
    await start_api_server(config)


async def resume_command(args) -> None:
    """Execute the resume command to continue from checkpoint."""
    config = get_config()
    setup_logging(config.log_level)
    
    logger = logging.getLogger(__name__)
    logger.info(f"Resuming from checkpoint: {args.checkpoint}")
    
    # Load checkpoint
    checkpoint_manager = CheckpointManager(config.checkpoint_dir)
    state = checkpoint_manager.load(args.checkpoint)
    
    if not state:
        logger.error(f"Checkpoint not found: {args.checkpoint}")
        return
    
    # Create crawler with restored state
    crawler = StealthCrawler(config)
    crawler.visited = set(state.get('visited', []))
    
    # Create scope manager
    scope_manager = create_scope_manager(
        in_scope=state.get('in_scope', []),
        out_of_scope=state.get('out_of_scope', [])
    )
    crawler.scope_manager = scope_manager
    
    try:
        await crawler.initialize()
        
        # Add remaining URLs to queue
        for url, depth in state.get('queue', []):
            await crawler.queue.put((url, depth))
        
        # Continue crawling
        results = await crawler.crawl([], max_depth=state.get('max_depth', config.max_depth))
        
        # Export results
        if args.output:
            export_results(results, args.output, format=args.format)
            logger.info(f"Results exported to {args.output}")
        
        logger.info(f"Crawl resumed and completed: {len(results)} pages crawled")
        
    finally:
        await crawler.close()


def scope_test_command(args) -> None:
    """Execute the scope test command."""
    setup_logging(args.log_level)
    
    logger = logging.getLogger(__name__)
    logger.info("Testing scope configuration")
    
    # Create scope manager
    scope_manager = create_scope_manager(
        in_scope=args.in_scope,
        out_of_scope=args.out_of_scope
    )
    
    # Display scope summary
    summary = scope_manager.get_scope_summary()
    print("\n=== Scope Configuration ===")
    print(f"In-scope patterns: {summary['in_scope_count']}")
    for pattern in summary['in_scope_patterns']:
        print(f"  + {pattern}")
    
    print(f"\nOut-of-scope patterns: {summary['out_of_scope_count']}")
    for pattern in summary['out_of_scope_patterns']:
        print(f"  - {pattern}")
    
    # Test URLs if provided
    if args.test_urls:
        print("\n=== URL Tests ===")
        for url in args.test_urls:
            result = scope_manager.test_url(url)
            status = "✓ IN SCOPE" if result['in_scope'] else "✗ OUT OF SCOPE"
            print(f"\n{url}")
            print(f"  Status: {status}")
            print(f"  Domain: {result['domain']}")
            print(f"  Reason: {result['reason']}")
            if result['matches_in_scope']:
                print(f"  Matches in-scope: {', '.join(result['matches_in_scope'])}")
            if result['matches_out_of_scope']:
                print(f"  Matches out-of-scope: {', '.join(result['matches_out_of_scope'])}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='StealthCrawler v17 - Advanced web crawler with stealth capabilities',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # Global arguments
    parser.add_argument('--log-level', default='INFO', 
                       choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                       help='Set logging level')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Crawl command
    crawl_parser = subparsers.add_parser('crawl', help='Start a new crawl')
    crawl_parser.add_argument('urls', nargs='+', help='Starting URLs')
    crawl_parser.add_argument('--depth', type=int, default=5, help='Maximum crawl depth')
    crawl_parser.add_argument('--in-scope', nargs='*', default=[], 
                             help='In-scope domain patterns (e.g., *.example.com)')
    crawl_parser.add_argument('--out-of-scope', nargs='*', default=[], 
                             help='Out-of-scope domain patterns')
    crawl_parser.add_argument('--output', '-o', help='Output file path')
    crawl_parser.add_argument('--format', default='json', 
                             choices=['json', 'csv', 'xml', 'html'],
                             help='Output format')
    
    # Distributed command
    distributed_parser = subparsers.add_parser('distributed', help='Run distributed crawl')
    distributed_parser.add_argument('--master', action='store_true', help='Run as master')
    distributed_parser.add_argument('--worker-id', default='worker-1', help='Worker ID')
    distributed_parser.add_argument('urls', nargs='*', default=[], help='Starting URLs (master only)')
    distributed_parser.add_argument('--depth', type=int, default=5, help='Maximum crawl depth')
    
    # Server command
    server_parser = subparsers.add_parser('server', help='Start API server')
    server_parser.add_argument('--host', default='0.0.0.0', help='Server host')
    server_parser.add_argument('--port', type=int, default=8000, help='Server port')
    
    # Resume command
    resume_parser = subparsers.add_parser('resume', help='Resume from checkpoint')
    resume_parser.add_argument('checkpoint', help='Checkpoint name or ID')
    resume_parser.add_argument('--output', '-o', help='Output file path')
    resume_parser.add_argument('--format', default='json',
                              choices=['json', 'csv', 'xml', 'html'],
                              help='Output format')
    
    # Scope test command
    scope_parser = subparsers.add_parser('scope-test', help='Test scope configuration')
    scope_parser.add_argument('--in-scope', nargs='*', default=[],
                             help='In-scope domain patterns')
    scope_parser.add_argument('--out-of-scope', nargs='*', default=[],
                             help='Out-of-scope domain patterns')
    scope_parser.add_argument('--test-urls', nargs='*', default=[],
                             help='URLs to test against scope')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Execute command
    if args.command == 'crawl':
        asyncio.run(crawl_command(args))
    elif args.command == 'distributed':
        asyncio.run(distributed_command(args))
    elif args.command == 'server':
        asyncio.run(server_command(args))
    elif args.command == 'resume':
        asyncio.run(resume_command(args))
    elif args.command == 'scope-test':
        scope_test_command(args)


if __name__ == '__main__':
    main()
