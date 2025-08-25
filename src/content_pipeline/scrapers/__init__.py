"""Scrapers package for content pipeline.

This package provides web scraping functionality with multiple strategies.
"""

from content_pipeline.scrapers.scraper import (
    WebScraper as UnifiedScraper,
    ScrapingStrategy,
    create_scraper
)
from content_pipeline.scrapers.web_scraper import WebScraper  # Legacy compatibility
from content_pipeline.scrapers.rss_monitor import RSSMonitor

__all__ = [
    'UnifiedScraper',
    'WebScraper',
    'ScrapingStrategy',
    'create_scraper',
    'RSSMonitor'
]