"""Scrapy downloaders and spiders middlewares."""

import random
import time

from scrapy import signals


class RandomUserAgentMiddleware:
    """Rotate User-Agent for each request."""

    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/120.0.0.0",
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


class RateLimitMiddleware:
    """Rate limit requests to avoid being blocked."""

    def __init__(self, delay: float = 2.0):
        self.delay = delay
        self.last_request_time: float = 0

    @classmethod
    def from_crawler(cls, crawler):
        delay = crawler.settings.getfloat("SCRAPER_DOWNLOAD_DELAY", 2.0)
        return cls(delay=delay)

    def process_request(self, request, spider):
        now = time.time()
        elapsed = now - self.last_request_time
        if elapsed < self.delay:
            wait_time = self.delay - elapsed + random.uniform(0, 0.5)
            time.sleep(wait_time)
        self.last_request_time = time.time()


class ProxyMiddleware:
    """Proxy rotation middleware (placeholder for future implementation)."""

    def process_request(self, request, spider):
        # TODO: Implement proxy rotation when proxy pool is available
        spider.logger.debug("ProxyMiddleware: No proxy configured, using direct connection")
