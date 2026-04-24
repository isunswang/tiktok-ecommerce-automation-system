"""Scrapy settings for 1688 product scraper."""

import os

BOT_NAME = "scraper"
SPIDER_MODULES = ["scraper.spiders"]
NEWSPIDER_MODULE = "scraper.spiders"

# Crawl responsibly by identifying yourself
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"

# Obey robots.txt rules (set to False for 1688 as we need to crawl)
ROBOTSTXT_OBEY = False

# Configure maximum concurrent requests (conservative to avoid blocking)
CONCURRENT_REQUESTS = 2
CONCURRENT_REQUESTS_PER_DOMAIN = 2

# Download delay (seconds between requests)
DOWNLOAD_DELAY = 3.0
RANDOMIZE_DOWNLOAD_DELAY = True

# Disable cookies (to reduce fingerprinting)
COOKIES_ENABLED = False

# Disable Telnet Console
TELNETCONSOLE_ENABLED = False

# Override the default request headers
DEFAULT_REQUEST_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
}

# Enable and configure AutoThrottle
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 2.0
AUTOTHROTTLE_MAX_DELAY = 30.0
AUTOTHROTTLE_TARGET_CONCURRENCY = 1.5
AUTOTHROTTLE_DEBUG = False

# Enable and configure HTTP caching (useful for development)
HTTPCACHE_ENABLED = True
HTTPCACHE_EXPIRATION_SECS = 3600  # 1 hour
HTTPCACHE_DIR = "httpcache"
HTTPCACHE_IGNORE_HTTP_CODES = [500, 502, 503, 504, 403, 429]
HTTPCACHE_STORAGE = "scrapy.extensions.httpcache.FilesystemCacheStorage"

# Item Pipelines
ITEM_PIPELINES = {
    "scraper.pipelines.DataCleanPipeline": 100,
    "scraper.pipelines.DuplicatesFilterPipeline": 200,
    "scraper.pipelines.JsonWriterPipeline": 300,
    "scraper.pipelines.DatabasePipeline": 400,
}

# Downloader Middlewares
DOWNLOADER_MIDDLEWARES = {
    "scraper.middlewares.RandomUserAgentMiddleware": 400,
    "scraper.middlewares.RateLimitMiddleware": 500,
    "scraper.middlewares.ProxyMiddleware": 600,
}

# Retry settings
RETRY_ENABLED = True
RETRY_TIMES = 3
RETRY_HTTP_CODES = [500, 502, 503, 504, 403, 429, 520, 521, 522]
RETRY_DELAY = 5

# Timeout
DOWNLOAD_TIMEOUT = 60

# Log level
LOG_LEVEL = "INFO"
LOG_FILE = None

# Output directory
OUTPUT_DIR = "output"

# Environment-specific settings (can be overridden by env vars)
SCRAPER_DOWNLOAD_DELAY = float(os.getenv("SCRAPER_DOWNLOAD_DELAY", "3.0"))
SCRAPER_CONCURRENCY = int(os.getenv("SCRAPER_CONCURRENCY", "2"))
SCRAPER_DELAY_JITTER = float(os.getenv("SCRAPER_DELAY_JITTER", "1.0"))

# Proxy settings (set via environment or settings)
PROXY_LIST = []  # List of proxy URLs, e.g., ["http://proxy1:8080", "http://proxy2:8080"]
PROXY_API = os.getenv("PROXY_API", "")  # API endpoint to fetch proxies

# 1688 specific settings
ALIBABA_1688_MOCK_MODE = os.getenv("ALIBABA_1688_MOCK_MODE", "true").lower() == "true"

# Playwright settings (for dynamic content)
PLAYWRIGHT_BROWSER_TYPE = "chromium"
PLAYWRIGHT_LAUNCH_OPTIONS = {
    "headless": True,
    "args": [
        "--disable-blink-features=AutomationControlled",
        "--disable-dev-shm-usage",
        "--no-sandbox",
    ],
}

# Playwright download handlers (uncomment to enable)
# DOWNLOAD_HANDLERS = {
#     "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
#     "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
# }

# Extensions
EXTENSIONS = {
    "scrapy.extensions.logstats.LogStats": 100,
    "scrapy.extensions.telnet.TelnetConsole": None,  # Disable
}

# Stats collection
STATS_CLASS = "scrapy.statscollectors.StatsCollector"
STATS_DUMP = True

# Depth limit (for breadth-first crawling)
DEPTH_LIMIT = 0  # No limit

# Scheduler
SCHEDULER = "scrapy.core.scheduler.Scheduler"
SCHEDULER_MEMORY_QUEUE = "scrapy.squeues.LifoMemoryQueue"
SCHEDULER_DISK_QUEUE = "scrapy.squeues.PickleLifoDiskQueue"

# Auto-spider discovery
SPIDER_LOADER_WARN_ONLY = True

# Max active requests per spider
MAX_ACTIVE_REQUESTS = 8
