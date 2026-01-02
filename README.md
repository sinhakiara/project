# 🕵️ StealthCrawler v17

**Advanced web crawler with stealth capabilities, distributed crawling, and AI-powered analysis**

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 🚀 Features

### Core Capabilities
- **🎭 Stealth Mode**: Browser fingerprint randomization, anti-detection measures
- **⚡ High Performance**: Async/await architecture with concurrent workers
- **🎯 Advanced Scope Management**: Wildcard patterns (`*.domain.com`, `**.domain.com`) with exclusion priority
- **🌐 Distributed Crawling**: Redis-based coordination for multi-worker deployments
- **📊 Multiple Export Formats**: JSON, CSV, XML, HTML reports
- **🔄 Resume Capability**: Checkpoint system to resume interrupted crawls

### Advanced Features
- **🤖 AI Vision Analysis**: OpenAI GPT-4 Vision and Anthropic Claude integration
- **🔐 Multi-Strategy Authentication**: Basic, OAuth2, form-based login
- **🧩 CAPTCHA Solving**: 2Captcha and Anti-Captcha integration
- **🔀 Proxy Management**: Rotation with health checking
- **🧅 Tor Support**: Anonymous crawling via Tor network
- **📡 Protocol Detection**: WebSocket, GraphQL, SSE, REST API detection
- **🎨 Rich Dashboard**: Real-time terminal UI with live statistics
- **📨 Webhook Notifications**: Slack, Discord, Microsoft Teams integration
- **🔍 Pattern Learning**: Self-learning URL pattern detection

## 📋 Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Usage](#usage)
- [Scope Management](#scope-management)
- [Configuration](#configuration)
- [Distributed Crawling](#distributed-crawling)
- [Docker Deployment](#docker-deployment)
- [API Server](#api-server)
- [Testing](#testing)
- [Examples](#examples)
- [Architecture](#architecture)
- [Contributing](#contributing)

## 🔧 Installation

### Prerequisites
- Python 3.11 or higher
- pip package manager

### Standard Installation

```bash
# Clone the repository
git clone https://github.com/Sattyam-Kasar/stealth-crawler.git
cd stealth-crawler

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium

# Or use the quick start script
chmod +x run.sh
./run.sh
```

### Docker Installation

```bash
# Build Docker image
docker build -t stealth-crawler:v17 .

# Or use Docker Compose
docker-compose up -d
```

## ⚡ Quick Start

### Basic Crawl

```bash
# Crawl a single domain
python main.py crawl https://example.com

# Crawl with depth limit
python main.py crawl https://example.com --depth 3

# Export results
python main.py crawl https://example.com --output results.json --format json
```

### With Scope Management

```bash
# Include all subdomains, exclude admin
python main.py crawl https://example.com \
  --in-scope "*.example.com" \
  --out-of-scope "admin.example.com" \
  --depth 5
```

### Test Scope Configuration

```bash
# Test your scope rules
python main.py scope-test \
  --in-scope "*.example.com" "*.test.com" \
  --out-of-scope "admin.example.com" "private.test.com" \
  --test-urls "https://api.example.com" "https://admin.example.com"
```

## 📖 Usage

### Command Line Interface

StealthCrawler provides several commands:

#### 1. Crawl Command

```bash
python main.py crawl [OPTIONS] URLS...

Options:
  --depth INTEGER          Maximum crawl depth (default: 5)
  --in-scope TEXT         In-scope domain patterns (can specify multiple)
  --out-of-scope TEXT     Out-of-scope domain patterns (can specify multiple)
  --output PATH           Output file path
  --format [json|csv|xml|html]  Output format (default: json)
  --log-level [DEBUG|INFO|WARNING|ERROR]  Logging level
```

Example:
```bash
python main.py crawl https://example.com https://test.com \
  --depth 3 \
  --in-scope "*.example.com" "*.test.com" \
  --out-of-scope "admin.example.com" \
  --output crawl_results.json \
  --format json
```

#### 2. Distributed Command

```bash
# Start master node
python main.py distributed --master \
  https://example.com \
  --depth 5

# Start worker nodes
python main.py distributed --worker-id worker-1
python main.py distributed --worker-id worker-2
```

#### 3. API Server Command

```bash
python main.py server --host 0.0.0.0 --port 8000
```

#### 4. Resume Command

```bash
python main.py resume checkpoint-name \
  --output resumed_results.json
```

#### 5. Scope Test Command

```bash
python main.py scope-test \
  --in-scope "*.example.com" \
  --out-of-scope "admin.example.com" \
  --test-urls "https://api.example.com" "https://admin.example.com"
```

## 🎯 Scope Management

### Overview

The scope manager is a **CRITICAL** component that controls which URLs are crawled. It supports:

- ✅ Exact domain matching
- ✅ Wildcard subdomain matching (`*.domain.com`)
- ✅ Nested wildcard matching (`**.domain.com`)
- ✅ **EXCLUSION PRIORITY**: Exclusions always override inclusions

### Wildcard Patterns

#### Single-Level Wildcard (`*.domain.com`)

Matches exactly ONE level of subdomain:

```python
# Pattern: *.example.com
✓ api.example.com       # Matches
✓ admin.example.com     # Matches
✗ example.com           # No match (base domain)
✗ api.v1.example.com    # No match (two levels)
```

#### Multi-Level Wildcard (`**.domain.com`)

Matches ANY number of subdomain levels:

```python
# Pattern: **.example.com
✓ api.example.com           # Matches
✓ api.v1.example.com        # Matches
✓ test.api.v1.example.com   # Matches
✗ example.com               # No match (base domain)
```

### Exclusion Priority (CRITICAL!)

**Exclusions ALWAYS take precedence over inclusions:**

```bash
# Include all subdomains
--in-scope "*.example.com"

# Exclude admin subdomain
--out-of-scope "admin.example.com"

# Results:
# ✓ api.example.com     → IN SCOPE
# ✓ test.example.com    → IN SCOPE
# ✗ admin.example.com   → OUT OF SCOPE (excluded!)
```

### Programmatic Usage

```python
from scope_manager import create_scope_manager

# Create scope manager
scope = create_scope_manager(
    in_scope=['*.example.com', 'test.com'],
    out_of_scope=['admin.example.com', 'private.example.com']
)

# Check if URL is in scope
if scope.is_in_scope('https://api.example.com'):
    print("URL is in scope!")

# Test URL with details
result = scope.test_url('https://admin.example.com')
print(result)
# {
#   'url': 'https://admin.example.com',
#   'domain': 'admin.example.com',
#   'in_scope': False,
#   'reason': 'EXCLUDED',
#   'matches_out_of_scope': ['exact: admin.example.com']
# }
```

## ⚙️ Configuration

### Environment Variables

Create a `.env` file (copy from `.env.example`):

```bash
# General Settings
LOG_LEVEL=INFO
MAX_WORKERS=10
MAX_DEPTH=5

# Stealth Settings
HEADLESS=true
USER_AGENT_ROTATION=true
FINGERPRINT_RANDOMIZATION=true

# Rate Limiting
REQUESTS_PER_SECOND=2
ADAPTIVE_RATE_LIMIT=true

# Proxy Settings
USE_PROXY=false
PROXY_LIST_FILE=proxies.txt

# AI Vision
OPENAI_API_KEY=your-key-here
VISION_ANALYSIS_ENABLED=false

# Distributed Crawling
REDIS_HOST=localhost
REDIS_PORT=6379
DISTRIBUTED_MODE=false

# Webhooks
SLACK_WEBHOOK_URL=https://hooks.slack.com/...
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
```

### Programmatic Configuration

```python
from config import CrawlerConfig

config = CrawlerConfig()
config.max_workers = 20
config.max_depth = 10
config.headless = False
config.requests_per_second = 5

crawler = StealthCrawler(config)
```

## 🌐 Distributed Crawling

### Architecture

StealthCrawler uses Redis for distributed coordination:

- **Master Node**: Initializes the queue with start URLs
- **Worker Nodes**: Process URLs from the shared queue
- **Redis**: Coordinates work and stores results

### Setup

1. **Start Redis**:
```bash
docker run -d -p 6379:6379 redis:7-alpine
```

2. **Configure Workers**:
```bash
# .env
DISTRIBUTED_MODE=true
REDIS_HOST=localhost
REDIS_PORT=6379
```

3. **Run Master**:
```bash
python main.py distributed --master \
  https://example.com \
  --depth 5
```

4. **Run Workers** (in separate terminals/machines):
```bash
python main.py distributed --worker-id worker-1
python main.py distributed --worker-id worker-2
python main.py distributed --worker-id worker-3
```

### Docker Compose

```bash
# Start full distributed stack
docker-compose up -d

# Scale workers
docker-compose up -d --scale crawler-worker=5
```

## 🐳 Docker Deployment

### Build Image

```bash
docker build -t stealth-crawler:v17 .
```

### Run Container

```bash
docker run -it stealth-crawler:v17 \
  python main.py crawl https://example.com
```

### Docker Compose

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

Services included:
- `crawler-api`: REST API server
- `crawler-worker-1/2`: Distributed workers
- `redis`: Coordination
- `elasticsearch`: Data storage
- `tor`: Anonymous crawling

## 🔌 API Server

### Start Server

```bash
python main.py server --host 0.0.0.0 --port 8000
```

### API Endpoints

#### Start Crawl

```bash
curl -X POST http://localhost:8000/crawl/start \
  -H "Content-Type: application/json" \
  -d '{
    "start_urls": ["https://example.com"],
    "max_depth": 5,
    "in_scope": ["*.example.com"],
    "out_of_scope": ["admin.example.com"]
  }'
```

#### Get Status

```bash
curl http://localhost:8000/crawl/{crawl_id}/status
```

#### Get Results

```bash
curl http://localhost:8000/crawl/{crawl_id}/results?limit=100
```

#### List Crawls

```bash
curl http://localhost:8000/crawl/list
```

## 🧪 Testing

### Run All Tests

```bash
# Using pytest
pytest tests/ -v

# Using make
make test
```

### Run with Coverage

```bash
pytest tests/ -v --cov=. --cov-report=html --cov-report=term
```

### Run Specific Tests

```bash
# Test scope manager only
pytest tests/test_scope_manager.py -v

# Test crawler only
pytest tests/test_crawler.py -v
```

### Linting

```bash
make lint
```

## 📚 Examples

### Example 1: Basic E-commerce Crawl

```python
import asyncio
from stealth_crawler import StealthCrawler
from scope_manager import create_scope_manager
from config import CrawlerConfig

async def main():
    config = CrawlerConfig()
    config.max_depth = 3
    
    crawler = StealthCrawler(config)
    crawler.scope_manager = create_scope_manager(
        in_scope=['shop.example.com'],
        out_of_scope=['shop.example.com/admin']
    )
    
    await crawler.initialize()
    results = await crawler.crawl(['https://shop.example.com'])
    await crawler.close()
    
    print(f"Crawled {len(results)} pages")

asyncio.run(main())
```

### Example 2: Multi-Domain with Exclusions

```bash
python main.py crawl \
  https://example.com \
  https://test.com \
  --in-scope "*.example.com" "*.test.com" \
  --out-of-scope "admin.example.com" "private.test.com" "*.internal.example.com" \
  --depth 5 \
  --output multi_domain.json
```

### Example 3: Distributed Crawl with Webhooks

```bash
# .env
DISTRIBUTED_MODE=true
WEBHOOK_ENABLED=true
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL

# Start crawl
python main.py distributed --master \
  https://example.com \
  --depth 10
```

## 🏗️ Architecture

### Components

```
┌─────────────────────────────────────────────────────┐
│                  StealthCrawler v17                 │
├─────────────────────────────────────────────────────┤
│                                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────┐ │
│  │ Scope Manager│  │ Rate Limiter │  │ Stealth  │ │
│  │   (Critical) │  │  (Adaptive)  │  │  Engine  │ │
│  └──────────────┘  └──────────────┘  └──────────┘ │
│                                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────┐ │
│  │   Crawler    │  │  Checkpoint  │  │  Export  │ │
│  │   Workers    │  │   Manager    │  │  Formats │ │
│  └──────────────┘  └──────────────┘  └──────────┘ │
│                                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────┐ │
│  │ Distributed  │  │     API      │  │ Webhooks │ │
│  │   (Redis)    │  │   Server     │  │  Notify  │ │
│  └──────────────┘  └──────────────┘  └──────────┘ │
│                                                     │
└─────────────────────────────────────────────────────┘
```

### File Structure

```
stealth-crawler/
├── main.py                 # CLI entry point
├── stealth_crawler.py      # Core crawler
├── scope_manager.py        # CRITICAL: Scope management
├── config.py               # Configuration
├── utils.py                # Utilities
├── rate_limiter.py         # Rate limiting
├── fingerprint.py          # Fingerprint randomization
├── auth.py                 # Authentication
├── captcha_handler.py      # CAPTCHA solving
├── proxy_manager.py        # Proxy rotation
├── tor_support.py          # Tor integration
├── vision_analysis.py      # AI vision
├── checkpoint.py           # Checkpointing
├── distributed.py          # Distributed crawling
├── api_server.py           # REST API
├── dashboard.py            # Terminal UI
├── webhooks.py             # Notifications
├── exporters.py            # Export formats
├── pattern_library.py      # Pattern learning
├── protocol_detector.py    # Protocol detection
├── requirements.txt        # Dependencies
├── Dockerfile              # Docker build
├── docker-compose.yml      # Docker stack
├── Makefile               # Build commands
├── run.sh                 # Quick start
└── tests/                 # Test suite
    ├── conftest.py
    ├── test_crawler.py
    └── test_scope_manager.py
```

## 🤝 Contributing

Contributions are welcome! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Run the test suite
6. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🙏 Acknowledgments

- Built with [Playwright](https://playwright.dev/)
- Uses [Rich](https://rich.readthedocs.io/) for terminal UI
- Distributed crawling with [Redis](https://redis.io/)
- AI powered by [OpenAI](https://openai.com/) and [Anthropic](https://anthropic.com/)

## 📞 Support

- 📧 Email: support@stealthcrawler.dev
- 💬 Discord: https://discord.gg/stealthcrawler
- 🐛 Issues: https://github.com/Sattyam-Kasar/stealth-crawler/issues

---

**Made with ❤️ by the StealthCrawler Team**
