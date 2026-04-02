"""Scrapy settings for 1688 product scraper."""

BOT_NAME = "scraper"
SPIDER_MODULES = ["scraper.spiders"]
NEWSPIDER_MODULE = "scraper.spiders"

# Crawl responsibly by identifying yourself
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

# Obey robots.txt rules
ROBOTSTXT_OBEY = False

# Configure maximum concurrent requests
CONCURRENT_REQUESTS = 4

# Download delay
DOWNLOAD_DELAY = 2.0

# Disable cookies (to reduce fingerprinting)
COOKIES_ENABLED = False

# Disable Telnet Console
TELNETCONSOLE_ENABLED = False

# Override the default request headers
DEFAULT_REQUEST_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}

# Enable and configure AutoThrottle
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 2.0
AUTOTHROTTLE_MAX_DELAY = 10.0
AUTOTHROTTLE_TARGET_CONCURRENCY = 2.0

# Enable and configure HTTP caching
HTTPCACHE_ENABLED = True
HTTPCACHE_EXPIRATION_SECS = 86400
HTTPCACHE_DIR = "httpcache"
HTTPCACHE_IGNORE_HTTP_CODES = [500, 502, 503, 504]

# Item Pipelines
ITEM_PIPELINES = {
    "scraper.pipelines.DataCleanPipeline": 100,
    "scraper.pipelines.DuplicatesFilterPipeline": 200,
    "scraper.pipelines.JsonWriterPipeline": 300,
    "scraper.pipelines.DatabaseStoragePipeline": 400,
}

# Downloader Middlewares
DOWNLOADER_MIDDLEWARES = {
    "scraper.middlewares.RandomUserAgentMiddleware": 400,
    "scraper.middlewares.RateLimitMiddleware": 500,
}

# Retry settings
RETRY_ENABLED = True
RETRY_TIMES = 3
RETRY_HTTP_CODES = [500, 502, 503, 504, 403, 429]

# Timeout
DOWNLOAD_TIMEOUT = 30

# Log level
LOG_LEVEL = "INFO"
LOG_FILE = None

# Output directory
OUTPUT_DIR = "output"

# Environment-specific settings (overridden by env vars)
SCRAPER_DOWNLOAD_DELAY = 2.0
SCRAPER_CONCURRENCY = 4
