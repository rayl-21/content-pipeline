"""Legacy web scraper module for backward compatibility.

This module provides the WebScraper class for backward compatibility.
It internally uses the new unified scraper implementation.
"""

from typing import Optional
from content_pipeline.core.models import Article
from content_pipeline.scrapers.scraper import WebScraper as UnifiedScraper, ScrapingStrategy


class WebScraper:
    """Legacy web scraper wrapper for backward compatibility."""
    
    def __init__(self, delay: float = 1.0, timeout: int = 10):
        """Initialize web scraper.
        
        Args:
            delay: Delay between requests in seconds
            timeout: Request timeout in seconds
        """
        # Use the unified scraper with basic strategy for backward compatibility
        self._scraper = UnifiedScraper(
            strategy=ScrapingStrategy.BASIC,
            delay=delay,
            timeout=timeout
        )
        self.delay = delay
        self.timeout = timeout
        self.session = self._scraper.session
    
    def scrape_article_content(self, article: Article) -> Article:
        """Scrape the full content of an article.
        
        Args:
            article: Article object with URL to scrape
            
        Returns:
            Updated Article object with full content
        """
        return self._scraper.scrape_article(article)
    
    def scrape_article(self, article: Article) -> Article:
        """Alias for scrape_article_content for compatibility."""
        return self.scrape_article_content(article)
    
    def _extract_content(self, html: str) -> str:
        """Extract article content from HTML.
        
        Args:
            html: Raw HTML content
            
        Returns:
            Extracted text content
        """
        return self._scraper._extract_content(html)
    
    def _clean_text(self, text: str) -> str:
        """Clean extracted text.
        
        Args:
            text: Raw extracted text
            
        Returns:
            Cleaned text
        """
        return self._scraper._clean_text(text)
    
    def test_url(self, url: str) -> bool:
        """Test if a URL is accessible.
        
        Args:
            url: URL to test
            
        Returns:
            True if accessible, False otherwise
        """
        try:
            response = self.session.head(url, timeout=self.timeout, allow_redirects=True)
            return response.status_code < 400
        except Exception:
            return False
    
    def close(self):
        """Clean up resources."""
        self._scraper.close()