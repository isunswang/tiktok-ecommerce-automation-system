#!/usr/bin/env python
"""Script to run 1688 spider with various options."""

import argparse
import os
import sys

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, project_root)


def run_spider():
    parser = argparse.ArgumentParser(description="Run 1688 product spider")
    parser.add_argument("keyword", nargs="?", default="", help="Search keyword")
    parser.add_argument("-p", "--pages", type=int, default=5, help="Max pages to crawl")
    parser.add_argument("--mock", action="store_true", help="Use mock data")
    parser.add_argument("--playwright", action="store_true", help="Use Playwright for rendering")
    parser.add_argument("--details", action="store_true", help="Crawl product detail pages")
    parser.add_argument("-o", "--output", help="Output file (JSON format)")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")

    args = parser.parse_args()

    # Set environment variables
    if args.mock:
        os.environ["ALIBABA_1688_MOCK_MODE"] = "true"

    # Build scrapy command
    cmd_parts = ["scrapy", "crawl", "alibaba"]

    if args.keyword:
        cmd_parts.extend(["-a", f"keyword={args.keyword}"])

    cmd_parts.extend(["-a", f"max_pages={args.pages}"])

    if args.mock:
        cmd_parts.extend(["-a", "mock_mode=true"])

    if args.playwright:
        cmd_parts.extend(["-a", "use_playwright=true"])

    if args.details:
        cmd_parts.extend(["-a", "crawl_details=true"])

    if args.output:
        cmd_parts.extend(["-o", args.output])

    if args.verbose:
        cmd_parts.extend(["--loglevel=DEBUG"])

    # Run spider
    import subprocess
    print(f"Running: {' '.join(cmd_parts)}")
    subprocess.run(cmd_parts, cwd=os.path.dirname(__file__))


if __name__ == "__main__":
    run_spider()
