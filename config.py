"""
StealthCrawler v17 - Configuration Management
"""
import os
from dataclasses import dataclass, field
from typing import List, Optional
from dotenv import load_dotenv

load_dotenv()


@dataclass
class CrawlerConfig:
    """Main crawler configuration."""
    
    # Target settings
    start_urls: List[str] = field(default_factory=list)
    in_scope: List[str] = field(default_factory=list)
    out_scope: List[str] = field(default_factory=list)
    
    # Crawl limits
    max_pages: int = int(os.getenv("MAX_PAGES", "1000"))
    max_depth: int = int(os.getenv("MAX_DEPTH", "10"))
    max_concurrent: int = int(os.getenv("MAX_CONCURRENT", "10"))
    
    # Rate limiting
    rate_limit: float = float(os.getenv("RATE_LIMIT", "5.0"))
    respect_robots_txt: bool = True
    
    # Stealth settings
    stealth_mode: bool = True
    randomize_fingerprint: bool = True
    human_simulation: bool = True
    
    # Browser settings
    headless: bool = True
    browser_type: str = "chromium"
    viewport_width: int = 1920
    viewport_height: int = 1080
    
    # Timeout settings
    page_timeout: int = 30000
    navigation_timeout: int = 60000
    
    # Output settings
    output_dir: str = "output"
    screenshot_on_error: bool = True
    
    # Logging
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Authentication
    auth_email: Optional[str] = os.getenv("CRAWLER_EMAIL")
    auth_password: Optional[str] = os.getenv("CRAWLER_PASSWORD")
    auth_api_key: Optional[str] = os.getenv("CRAWLER_API_KEY")
    auth_token: Optional[str] = os.getenv("CRAWLER_TOKEN")
    
    # Proxy settings
    proxy_list: List[str] = field(default_factory=list)
    rotate_proxy: bool = False
    
    # Distributed settings
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    worker_id: Optional[str] = None
    
    # Checkpoint settings
    checkpoint_enabled: bool = True
    checkpoint_interval: int = 100
    checkpoint_dir: str = "checkpoints"
    
    # Export settings
    export_format: str = "json"
    
    # Webhook settings
    slack_webhook: Optional[str] = os.getenv("SLACK_WEBHOOK_URL")
    discord_webhook: Optional[str] = os.getenv("DISCORD_WEBHOOK_URL")
    teams_webhook: Optional[str] = os.getenv("TEAMS_WEBHOOK_URL")
    
    # AI settings
    openai_api_key: Optional[str] = os.getenv("OPENAI_API_KEY")
    anthropic_api_key: Optional[str] = os.getenv("ANTHROPIC_API_KEY")
    
    # CAPTCHA settings
    twocaptcha_key: Optional[str] = os.getenv("TWOCAPTCHA_API_KEY")
    anticaptcha_key: Optional[str] = os.getenv("ANTICAPTCHA_API_KEY")
    capmonster_key: Optional[str] = os.getenv("CAPMONSTER_API_KEY")
    
    # Tor settings
    use_tor: bool = False
    tor_socks_port: int = int(os.getenv("TOR_SOCKS_PORT", "9050"))
    tor_control_port: int = int(os.getenv("TOR_CONTROL_PORT", "9051"))
    tor_control_password: Optional[str] = os.getenv("TOR_CONTROL_PASSWORD")


@dataclass
class ServerConfig:
    """API Server configuration."""
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 4
    reload: bool = False


def load_config(**kwargs) -> CrawlerConfig:
    """Load configuration with optional overrides."""
    return CrawlerConfig(**kwargs)


def load_server_config(**kwargs) -> ServerConfig:
    """Load server configuration."""
    return ServerConfig(**kwargs)
