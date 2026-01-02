"""Rich terminal dashboard for StealthCrawler v17."""

import asyncio
import logging
from typing import Optional
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich.layout import Layout
from rich.panel import Panel
from rich.progress import Progress, BarColumn, TextColumn, TimeRemainingColumn

logger = logging.getLogger(__name__)


class Dashboard:
    """
    Rich terminal dashboard for real-time crawl monitoring.
    
    Features:
    - Live progress updates
    - Statistics display
    - Error tracking
    - Performance metrics
    """
    
    def __init__(self):
        self.console = Console()
        self.layout = Layout()
        self.stats = {
            'visited': 0,
            'queue_size': 0,
            'success': 0,
            'errors': 0,
            'start_time': None,
            'rate': 0.0
        }
        
    def create_layout(self) -> Layout:
        """Create dashboard layout."""
        self.layout.split(
            Layout(name="header", size=3),
            Layout(name="body"),
            Layout(name="footer", size=7)
        )
        
        self.layout["body"].split_row(
            Layout(name="stats"),
            Layout(name="progress")
        )
        
        return self.layout
    
    def render_header(self) -> Panel:
        """Render header panel."""
        return Panel(
            "[bold cyan]StealthCrawler v17[/bold cyan] - Real-time Dashboard",
            style="bold white on blue"
        )
    
    def render_stats(self) -> Table:
        """Render statistics table."""
        table = Table(title="Statistics", show_header=True, header_style="bold magenta")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", justify="right", style="green")
        
        # Calculate runtime
        runtime = "N/A"
        if self.stats['start_time']:
            elapsed = (datetime.now() - self.stats['start_time']).total_seconds()
            runtime = f"{int(elapsed)}s"
        
        # Add rows
        table.add_row("Visited URLs", str(self.stats['visited']))
        table.add_row("Queue Size", str(self.stats['queue_size']))
        table.add_row("Successful", str(self.stats['success']))
        table.add_row("Errors", str(self.stats['errors']))
        table.add_row("Success Rate", f"{self._calc_success_rate():.1f}%")
        table.add_row("Crawl Rate", f"{self.stats['rate']:.2f} pages/s")
        table.add_row("Runtime", runtime)
        
        return table
    
    def render_progress(self) -> Panel:
        """Render progress panel."""
        progress = Progress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeRemainingColumn(),
        )
        
        # Add tasks (example)
        task = progress.add_task(
            "[cyan]Crawling...",
            total=self.stats['visited'] + self.stats['queue_size'] or 100
        )
        progress.update(task, completed=self.stats['visited'])
        
        return Panel(progress, title="Progress", border_style="green")
    
    def render_footer(self) -> Table:
        """Render footer with recent activity."""
        table = Table(title="Recent Activity", show_header=True, header_style="bold yellow")
        table.add_column("Time", style="dim")
        table.add_column("Event", style="white")
        table.add_column("Status", justify="center")
        
        # Placeholder for recent events
        table.add_row(
            datetime.now().strftime("%H:%M:%S"),
            "Crawl started",
            "[green]✓[/green]"
        )
        
        return table
    
    def update_stats(self, **kwargs) -> None:
        """Update dashboard statistics."""
        for key, value in kwargs.items():
            if key in self.stats:
                self.stats[key] = value
    
    def _calc_success_rate(self) -> float:
        """Calculate success rate."""
        total = self.stats['success'] + self.stats['errors']
        if total == 0:
            return 0.0
        return (self.stats['success'] / total) * 100
    
    async def run(self, crawler) -> None:
        """
        Run dashboard with live updates.
        
        Args:
            crawler: StealthCrawler instance to monitor
        """
        self.stats['start_time'] = datetime.now()
        self.create_layout()
        
        with Live(self.layout, refresh_per_second=2, console=self.console) as live:
            while crawler.running or not crawler.queue.empty():
                # Update stats from crawler
                self.update_stats(
                    visited=len(crawler.visited),
                    queue_size=crawler.queue.qsize(),
                    success=sum(1 for r in crawler.results if r.success),
                    errors=sum(1 for r in crawler.results if not r.success)
                )
                
                # Calculate rate
                if self.stats['start_time']:
                    elapsed = (datetime.now() - self.stats['start_time']).total_seconds()
                    if elapsed > 0:
                        self.stats['rate'] = self.stats['visited'] / elapsed
                
                # Update layout
                self.layout["header"].update(self.render_header())
                self.layout["stats"].update(self.render_stats())
                self.layout["progress"].update(self.render_progress())
                self.layout["footer"].update(self.render_footer())
                
                await asyncio.sleep(0.5)
        
        # Final update
        self.console.print("\n[bold green]✓ Crawl completed![/bold green]\n")
        self.console.print(self.render_stats())
