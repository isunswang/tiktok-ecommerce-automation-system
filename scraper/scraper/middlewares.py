"""Scrapy downloaders and spiders middlewares."""

import logging
import random
import time
from typing import Optional

from scrapy import signals

logger = logging.getLogger(__name__)


class RandomUserAgentMiddleware:
    """Rotate User-Agent for each request."""

    USER_AGENTS = [
        # Chrome on Windows
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        # Chrome on Mac
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        # Firefox on Windows
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
        # Edge on Windows
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0",
        # Safari on Mac
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Safari/605.1.15",
        # Chrome on Linux
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    ]

    @classmethod
    def from_crawler(cls, crawler):
        middleware = cls()
        crawler.signals.connect(middleware.spider_opened, signal=signals.spider_opened)
        return middleware

    def spider_opened(self, spider):
        spider.logger.info("RandomUserAgentMiddleware enabled")

    def process_request(self, request, spider):
        request.headers["User-Agent"] = random.choice(self.USER_AGENTS)
        # Add common headers to mimic real browser
        request.headers["Accept"] = "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8"
        request.headers["Accept-Language"] = "zh-CN,zh;q=0.9,en;q=0.8"
        request.headers["Accept-Encoding"] = "gzip, deflate, br"
        request.headers["Cache-Control"] = "no-cache"
        request.headers["Pragma"] = "no-cache"


class RateLimitMiddleware:
    """Rate limit requests to avoid being blocked."""

    def __init__(self, delay: float = 2.0, jitter: float = 0.5):
        self.delay = delay
        self.jitter = jitter
        self.last_request_time: float = 0

    @classmethod
    def from_crawler(cls, crawler):
        delay = crawler.settings.getfloat("SCRAPER_DOWNLOAD_DELAY", 2.0)
        jitter = crawler.settings.getfloat("SCRAPER_DELAY_JITTER", 0.5)
        return cls(delay=delay, jitter=jitter)

    def process_request(self, request, spider):
        now = time.time()
        elapsed = now - self.last_request_time
        target_delay = self.delay + random.uniform(0, self.jitter)
        if elapsed < target_delay:
            wait_time = target_delay - elapsed
            time.sleep(wait_time)
        self.last_request_time = time.time()


class ProxyMiddleware:
    """Proxy rotation middleware for bypassing IP restrictions.

    Supports multiple proxy sources:
    - Static proxy list from settings
    - Dynamic proxy pool (API-based)
    - Local proxy server
    """

    def __init__(self, proxy_list: list[str] | None = None, proxy_api: str | None = None):
        self.proxy_list = proxy_list or []
        self.proxy_api = proxy_api
        self.proxy_index = 0
        self.bad_proxies: set[str] = set()

    @classmethod
    def from_crawler(cls, crawler):
        proxy_list = crawler.settings.getlist("PROXY_LIST", [])
        proxy_api = crawler.settings.get("PROXY_API", None)
        middleware = cls(proxy_list=proxy_list, proxy_api=proxy_api)
        crawler.signals.connect(middleware.spider_opened, signal=signals.spider_opened)
        crawler.signals.connect(middleware.spider_closed, signal=signals.spider_closed)
        return middleware

    def spider_opened(self, spider):
        spider.logger.info(f"ProxyMiddleware enabled with {len(self.proxy_list)} proxies")

    def spider_closed(self, spider):
        spider.logger.info(f"ProxyMiddleware: {len(self.bad_proxies)} proxies marked as bad")

    def get_proxy(self) -> Optional[str]:
        """Get next available proxy."""
        if not self.proxy_list:
            return None

        # Filter out bad proxies
        available = [p for p in self.proxy_list if p not in self.bad_proxies]
        if not available:
            # All proxies are bad, reset and try again
            self.bad_proxies.clear()
            available = self.proxy_list

        proxy = available[self.proxy_index % len(available)]
        self.proxy_index += 1
        return proxy

    def process_request(self, request, spider):
        if "dont_proxy" in request.meta:
            return

        proxy = self.get_proxy()
        if proxy:
            request.meta["proxy"] = proxy
            spider.logger.debug(f"Using proxy: {proxy[:30]}..." if len(proxy) > 30 else f"Using proxy: {proxy}")

    def process_response(self, request, response, spider):
        """Check if proxy caused issues."""
        if response.status in [403, 429, 503]:
            proxy = request.meta.get("proxy")
            if proxy:
                self.bad_proxies.add(proxy)
                spider.logger.warning(f"Proxy marked as bad: {proxy[:30]}..." if len(str(proxy)) > 30 else f"Proxy marked as bad: {proxy}")
        return response

    def process_exception(self, request, exception, spider):
        """Mark proxy as bad if connection fails."""
        proxy = request.meta.get("proxy")
        if proxy:
            self.bad_proxies.add(proxy)
            spider.logger.warning(f"Proxy failed with exception: {exception}")


class RetryMiddleware:
    """Enhanced retry middleware with backoff."""

    RETRY_EXCEPTIONS = (
        ConnectionError,
        TimeoutError,
    )

    def __init__(self, max_retries: int = 3, backoff_factor: float = 2.0):
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor

    @classmethod
    def from_crawler(cls, crawler):
        max_retries = crawler.settings.getint("RETRY_TIMES", 3)
        backoff_factor = crawler.settings.getfloat("RETRY_BACKOFF_FACTOR", 2.0)
        return cls(max_retries=max_retries, backoff_factor=backoff_factor)

    def process_exception(self, request, exception, spider):
        retry_times = request.meta.get("retry_times", 0)
        if retry_times < self.max_retries and isinstance(exception, self.RETRY_EXCEPTIONS):
            retry_times += 1
            request.meta["retry_times"] = retry_times
            delay = self.backoff_factor ** retry_times
            spider.logger.warning(f"Retrying {request.url} (attempt {retry_times}/{self.max_retries}) after {delay:.1f}s")
            time.sleep(delay)
            return request.copy()
        return None


class CookieMiddleware:
    """Manage cookies for maintaining session state."""

    def __init__(self):
        self.cookies: dict = {}

    @classmethod
    def from_crawler(cls, crawler):
        return cls()

    def process_request(self, request, spider):
        # Don't use cookies for 1688 to avoid tracking
        request.headers.pop("Cookie", None)
