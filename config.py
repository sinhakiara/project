<<<<<<< HEAD
"""Configuration management for StealthCrawler v17."""

from dataclasses import dataclass, field
from typing import Optional, List
import os
=======
"""
StealthCrawler v17 - Configuration Management
"""
import os
from dataclasses import dataclass, field
from typing import List, Optional
>>>>>>> main
from dotenv import load_dotenv

load_dotenv()


@dataclass
class CrawlerConfig:
    """Main crawler configuration."""
    
<<<<<<< HEAD
    # General Settings
    crawler_name: str = os.getenv("CRAWLER_NAME", "StealthCrawler")
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    max_workers: int = int(os.getenv("MAX_WORKERS", "10"))
    max_depth: int = int(os.getenv("MAX_DEPTH", "5"))
    timeout: int = int(os.getenv("TIMEOUT", "30000"))
    
    # Stealth Settings
    headless: bool = os.getenv("HEADLESS", "true").lower() == "true"
    user_agent_rotation: bool = os.getenv("USER_AGENT_ROTATION", "true").lower() == "true"
    fingerprint_randomization: bool = os.getenv("FINGERPRINT_RANDOMIZATION", "true").lower() == "true"
    
    # Rate Limiting
    requests_per_second: float = float(os.getenv("REQUESTS_PER_SECOND", "2"))
    adaptive_rate_limit: bool = os.getenv("ADAPTIVE_RATE_LIMIT", "true").lower() == "true"
    backoff_factor: float = float(os.getenv("BACKOFF_FACTOR", "2.0"))
    max_backoff: int = int(os.getenv("MAX_BACKOFF", "60"))
    
    # Proxy Settings
    use_proxy: bool = os.getenv("USE_PROXY", "false").lower() == "true"
    proxy_list_file: str = os.getenv("PROXY_LIST_FILE", "proxies.txt")
    proxy_rotation: bool = os.getenv("PROXY_ROTATION", "true").lower() == "true"
    proxy_health_check: bool = os.getenv("PROXY_HEALTH_CHECK", "true").lower() == "true"
    
    # Tor Settings
    use_tor: bool = os.getenv("USE_TOR", "false").lower() == "true"
    tor_socks_port: int = int(os.getenv("TOR_SOCKS_PORT", "9050"))
    tor_control_port: int = int(os.getenv("TOR_CONTROL_PORT", "9051"))
    tor_password: Optional[str] = os.getenv("TOR_PASSWORD")
    
    # Authentication
    auth_method: str = os.getenv("AUTH_METHOD", "none")
    auth_username: Optional[str] = os.getenv("AUTH_USERNAME")
    auth_password: Optional[str] = os.getenv("AUTH_PASSWORD")
    oauth2_client_id: Optional[str] = os.getenv("OAUTH2_CLIENT_ID")
    oauth2_client_secret: Optional[str] = os.getenv("OAUTH2_CLIENT_SECRET")
    oauth2_token_url: Optional[str] = os.getenv("OAUTH2_TOKEN_URL")
    
    # CAPTCHA
    captcha_solver: str = os.getenv("CAPTCHA_SOLVER", "none")
    captcha_api_key: Optional[str] = os.getenv("CAPTCHA_API_KEY")
    two_captcha_api_key: Optional[str] = os.getenv("TWO_CAPTCHA_API_KEY")
    anti_captcha_api_key: Optional[str] = os.getenv("ANTI_CAPTCHA_API_KEY")
    
    # AI Vision Analysis
    openai_api_key: Optional[str] = os.getenv("OPENAI_API_KEY")
    anthropic_api_key: Optional[str] = os.getenv("ANTHROPIC_API_KEY")
    vision_analysis_enabled: bool = os.getenv("VISION_ANALYSIS_ENABLED", "false").lower() == "true"
    
    # Distributed Crawling
    redis_host: str = os.getenv("REDIS_HOST", "localhost")
    redis_port: int = int(os.getenv("REDIS_PORT", "6379"))
    redis_db: int = int(os.getenv("REDIS_DB", "0"))
    redis_password: Optional[str] = os.getenv("REDIS_PASSWORD")
    distributed_mode: bool = os.getenv("DISTRIBUTED_MODE", "false").lower() == "true"
    
    # API Server
    api_enabled: bool = os.getenv("API_ENABLED", "false").lower() == "true"
    api_host: str = os.getenv("API_HOST", "0.0.0.0")
    api_port: int = int(os.getenv("API_PORT", "8000"))
    api_workers: int = int(os.getenv("API_WORKERS", "4"))
    
    # Webhooks
    webhook_enabled: bool = os.getenv("WEBHOOK_ENABLED", "false").lower() == "true"
    slack_webhook_url: Optional[str] = os.getenv("SLACK_WEBHOOK_URL")
    discord_webhook_url: Optional[str] = os.getenv("DISCORD_WEBHOOK_URL")
    teams_webhook_url: Optional[str] = os.getenv("TEAMS_WEBHOOK_URL")
    
    # Export Settings
    export_format: str = os.getenv("EXPORT_FORMAT", "json")
    export_dir: str = os.getenv("EXPORT_DIR", "output")
    save_screenshots: bool = os.getenv("SAVE_SCREENSHOTS", "true").lower() == "true"
    save_html: bool = os.getenv("SAVE_HTML", "true").lower() == "true"
    
    # Elasticsearch
    elasticsearch_enabled: bool = os.getenv("ELASTICSEARCH_ENABLED", "false").lower() == "true"
    elasticsearch_host: str = os.getenv("ELASTICSEARCH_HOST", "localhost")
    elasticsearch_port: int = int(os.getenv("ELASTICSEARCH_PORT", "9200"))
    elasticsearch_index: str = os.getenv("ELASTICSEARCH_INDEX", "stealth-crawler")
    
    # Checkpointing
    checkpoint_enabled: bool = os.getenv("CHECKPOINT_ENABLED", "true").lower() == "true"
    checkpoint_dir: str = os.getenv("CHECKPOINT_DIR", "checkpoints")
    checkpoint_interval: int = int(os.getenv("CHECKPOINT_INTERVAL", "300"))
    
    # Scope Management
    scope_mode: str = os.getenv("SCOPE_MODE", "strict")
    allow_subdomains: bool = os.getenv("ALLOW_SUBDOMAINS", "true").lower() == "true"
    respect_robots_txt: bool = os.getenv("RESPECT_ROBOTS_TXT", "true").lower() == "true"
    
    # Browser Settings
    browser_type: str = os.getenv("BROWSER_TYPE", "chromium")
    browser_args: List[str] = field(default_factory=lambda: os.getenv(
        "BROWSER_ARGS", 
        "--disable-blink-features=AutomationControlled"
    ).split(","))
    viewport_width: int = int(os.getenv("VIEWPORT_WIDTH", "1920"))
    viewport_height: int = int(os.getenv("VIEWPORT_HEIGHT", "1080"))


def get_config() -> CrawlerConfig:
    """Get the current crawler configuration."""
    return CrawlerConfig()
=======
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
>>>>>>> main
