"""Rich terminal dashboard for StealthCrawler v17/v18 (God Mode compatible)."""

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

class Dashboard:
    """
    Rich terminal dashboard for real-time crawl monitoring.

    Features:
    - Live progress updates
    - Statistics display
    - Error tracking
    - Performance metrics
    """

    def __init__(self, logger=None):
        if logger is None:
            logger = logging.getLogger(__name__)
        self.logger = logger
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
        return Panel(
            "[bold cyan]StealthCrawler v17/v18[/bold cyan] - Real-time Dashboard",
            style="bold white on blue"
        )

    def render_stats(self) -> Table:
        table = Table(title="Statistics", show_header=True, header_style="bold magenta")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", justify="right", style="green")
        runtime = "N/A"
        if self.stats['start_time']:
            elapsed = (datetime.now() - self.stats['start_time']).total_seconds()
            runtime = f"{int(elapsed)}s"
        table.add_row("Visited URLs", str(self.stats['visited']))
        table.add_row("Queue Size", str(self.stats['queue_size']))
        table.add_row("Successful", str(self.stats['success']))
        table.add_row("Errors", str(self.stats['errors']))
        table.add_row("Success Rate", f"{self._calc_success_rate():.1f}%")
        table.add_row("Crawl Rate", f"{self.stats['rate']:.2f} pages/s")
        table.add_row("Runtime", runtime)
        return table

    def render_progress(self) -> Panel:
        progress = Progress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeRemainingColumn(),
        )
        total = self.stats['visited'] + self.stats['queue_size']
        if total == 0:
            total = 1
        task = progress.add_task(
            "[cyan]Crawling...",
            total=total
        )
        progress.update(task, completed=self.stats['visited'])
        return Panel(progress, title="Progress", border_style="green")

    def render_footer(self) -> Table:
        table = Table(title="Recent Activity", show_header=True, header_style="bold yellow")
        table.add_column("Time", style="dim")
        table.add_column("Event", style="white")
        table.add_column("Status", justify="center")
        table.add_row(
            datetime.now().strftime("%H:%M:%S"),
            "Crawl started",
            "[green]✓[/green]"
        )
        return table

    def update_stats(self, **kwargs) -> None:
        for key, value in kwargs.items():
            if key in self.stats:
                self.stats[key] = value

    def _calc_success_rate(self) -> float:
        total = self.stats['success'] + self.stats['errors']
        if total == 0:
            return 0.0
        return (self.stats['success'] / total) * 100

    async def run(self, crawl_state) -> None:
        self.stats['start_time'] = datetime.now()
        self.create_layout()

        def get_success_and_error_counts():
            results = getattr(crawl_state, 'results', {})
            if isinstance(results, dict):
                values = results.values()
            elif isinstance(results, list):
                values = results
            else:
                values = []
            return (
                sum(1 for r in values if (isinstance(r, dict) and not r.get('error'))),
                sum(1 for r in values if (isinstance(r, dict) and r.get('error')))
            )

        with Live(self.layout, refresh_per_second=2, console=self.console) as live:
            while getattr(crawl_state, 'url_queue', None) and not getattr(crawl_state.url_queue, 'empty', lambda: True)():
                self.update_stats(
                    visited=len(getattr(crawl_state, 'visited_urls', [])),
                    queue_size=getattr(crawl_state, 'url_queue').qsize() if getattr(crawl_state, 'url_queue', None) else 0,
                    success=get_success_and_error_counts()[0],
                    errors=get_success_and_error_counts()[1]
                )
                if self.stats['start_time']:
                    elapsed = (datetime.now() - self.stats['start_time']).total_seconds()
                    if elapsed > 0:
                        self.stats['rate'] = self.stats['visited'] / elapsed
                self.layout["header"].update(self.render_header())
                self.layout["stats"].update(self.render_stats())
                self.layout["progress"].update(self.render_progress())
                self.layout["footer"].update(self.render_footer())
                await asyncio.sleep(0.5)
        self.console.print("\n[bold green]✓ Crawl completed![/bold green]\n")
        self.console.print(self.render_stats())

# Alias for God Mode main.py compatibility
DashboardManager = Dashboard
