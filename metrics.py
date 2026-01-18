class CrawlerMetrics:
    """
    Tracks run-time metrics for the crawler job.
    Suitable for dashboard, reporting, and analytics.
    """
    def __init__(self, logger=None):
        self.pages_crawled = 0
        self.error_count = 0
        self.success_count = 0
        self.start_time = None
        self.end_time = None
        self.logger = logger

    def record_page(self, url=None, result=None, success=True):
        self.pages_crawled += 1
        if success:
            self.success_count += 1
        else:
            self.error_count += 1

    def reset(self):
        self.pages_crawled = 0
        self.success_count = 0
        self.error_count = 0
        self.start_time = None
        self.end_time = None

    def as_dict(self):
        return {
            "pages_crawled": self.pages_crawled,
            "errors": self.error_count,
            "success": self.success_count,
            "started": self.start_time,
            "ended": self.end_time,
        }

    def log_summary(self):
        """Log a crawl summary using the logger, or print if logger not present."""
        summary = self.as_dict()
        lines = [
            "====== Crawler Metrics Summary ======",
            f"Pages crawled: {summary['pages_crawled']}",
            f"Successes: {summary['success']}",
            f"Errors: {summary['errors']}",
            f"Started: {summary['started']}",
            f"Ended: {summary['ended']}",
        ]
        summary_text = "\n".join(lines)
        if self.logger:
            self.logger.info(summary_text)
        else:
            print(summary_text)

    def __repr__(self):
        return (f"<CrawlerMetrics crawled:{self.pages_crawled} "
                f"success:{self.success_count} error:{self.error_count}>")

