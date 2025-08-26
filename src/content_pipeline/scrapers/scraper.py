"""Unified web scraper with strategy pattern for different scraping methods.

This module consolidates all scraping functionality into a single, configurable class
that eliminates special cases and provides a clean interface for web scraping.
"""

import logging
import random
import time
from enum import Enum
from typing import Dict, List, Optional, Any, Callable
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

from content_pipeline.core.models import Article

logger = logging.getLogger(__name__)


class ScrapingStrategy(Enum):
    """Available scraping strategies."""
    BASIC = "basic"
    ENHANCED = "enhanced"
    CLOUDSCRAPER = "cloudscraper"
    MCP_PLAYWRIGHT = "mcp_playwright"


class WebScraper:
    """Unified web scraper with configurable strategies.
    
    This scraper follows the principle of simplicity - one class, one purpose,
    with strategies for different scraping methods instead of multiple classes.
    """
    
    # Default user agents for rotation
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
    ]
    
    # Content extraction selectors (order matters - most specific first)
    CONTENT_SELECTORS = [
        '#entry-content',  # FreightWaves specific ID
        '.entry-content',  # FreightWaves and WordPress sites
        'div.entry-content',
        'article.post',  # FreightCaviar and Ghost blogs
        'article[role="main"]',
        'main article.post',  # More specific for FreightCaviar
        'main article',
        'div.article-content',
        'div.post-content',
        'div.content-body',  # Additional content patterns
        'section.post-content',
        'div.content',
        'article',
        'main',
    ]
    
    def __init__(self,
                 strategy: ScrapingStrategy = ScrapingStrategy.BASIC,
                 delay: float = 1.0,
                 timeout: int = 10,
                 max_retries: int = 3,
                 mcp_functions: Optional[Dict[str, Callable]] = None):
        """Initialize the scraper.
        
        Args:
            strategy: Scraping strategy to use
            delay: Delay between requests in seconds
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            mcp_functions: Optional MCP functions for Playwright strategy
        """
        self.strategy = strategy
        self.delay = delay
        self.timeout = timeout
        self.max_retries = max_retries
        self.mcp_functions = mcp_functions or {}
        
        # Initialize session
        self.session = self._create_session()
        
        # Statistics
        self.stats = {
            'total': 0,
            'success': 0,
            'failed': 0
        }
    
    def _create_session(self) -> requests.Session:
        """Create and configure a requests session."""
        session = requests.Session()
        session.headers.update({
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate',  # Removed 'br' as it may cause issues
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': random.choice(self.USER_AGENTS)
        })
        return session
    
    def scrape_article(self, article: Article) -> Article:
        """Scrape a single article.
        
        Args:
            article: Article object with URL to scrape
            
        Returns:
            Updated Article object with scraped content
        """
        self.stats['total'] += 1
        
        try:
            # Apply delay
            time.sleep(self.delay)
            
            # Get content based on strategy
            content = self._scrape_with_strategy(article.url)
            
            if content:
                article.content = content
                self.stats['success'] += 1
                logger.info(f"Successfully scraped: {article.title[:50]}")
            else:
                self.stats['failed'] += 1
                logger.warning(f"No content extracted: {article.title[:50]}")
                
        except Exception as e:
            self.stats['failed'] += 1
            logger.error(f"Scraping failed for {article.url}: {e}")
            article.content = ""
            
        return article
    
    def scrape_articles(self, articles: List[Article]) -> List[Article]:
        """Scrape multiple articles.
        
        Args:
            articles: List of Article objects to scrape
            
        Returns:
            List of updated Article objects
        """
        logger.info(f"Scraping {len(articles)} articles with {self.strategy.value} strategy")
        
        scraped = []
        for i, article in enumerate(articles, 1):
            logger.info(f"Progress: {i}/{len(articles)}")
            scraped.append(self.scrape_article(article))
            
            # Add random delay between articles
            if i < len(articles):
                delay = random.uniform(self.delay, self.delay * 2)
                time.sleep(delay)
        
        self._log_stats()
        return scraped
    
    def _scrape_with_strategy(self, url: str) -> Optional[str]:
        """Scrape content using the configured strategy.
        
        Args:
            url: URL to scrape
            
        Returns:
            Extracted content or None
        """
        strategies = {
            ScrapingStrategy.BASIC: self._scrape_basic,
            ScrapingStrategy.ENHANCED: self._scrape_enhanced,
            ScrapingStrategy.CLOUDSCRAPER: self._scrape_cloudscraper,
            ScrapingStrategy.MCP_PLAYWRIGHT: self._scrape_mcp_playwright
        }
        
        scraper = strategies.get(self.strategy, self._scrape_basic)
        
        # Try with retries
        for attempt in range(self.max_retries):
            try:
                content = scraper(url)
                if content:
                    return content
            except Exception as e:
                logger.debug(f"Attempt {attempt + 1} failed: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
        
        return None
    
    def _scrape_basic(self, url: str) -> Optional[str]:
        """Basic scraping with requests."""
        response = self.session.get(url, timeout=self.timeout)
        response.raise_for_status()
        return self._extract_content(response.text)
    
    def _scrape_enhanced(self, url: str) -> Optional[str]:
        """Enhanced scraping with user-agent rotation."""
        # Rotate user agent
        self.session.headers['User-Agent'] = random.choice(self.USER_AGENTS)
        
        # Add referer for better success rate
        domain = urlparse(url).netloc
        self.session.headers['Referer'] = f"https://{domain}/"
        
        response = self.session.get(url, timeout=self.timeout)
        response.raise_for_status()
        return self._extract_content(response.text)
    
    def _scrape_cloudscraper(self, url: str) -> Optional[str]:
        """Scraping with cloudscraper for Cloudflare bypass."""
        try:
            import cloudscraper
            scraper = cloudscraper.create_scraper()
            response = scraper.get(url, timeout=self.timeout)
            response.raise_for_status()
            return self._extract_content(response.text)
        except ImportError:
            logger.warning("cloudscraper not installed, falling back to enhanced")
            return self._scrape_enhanced(url)
    
    def _scrape_mcp_playwright(self, url: str) -> Optional[str]:
        """Scraping with MCP Playwright functions."""
        if not self.mcp_functions:
            logger.warning("MCP functions not available, falling back to enhanced")
            return self._scrape_enhanced(url)
        
        try:
            # Navigate to URL
            nav_func = self.mcp_functions.get('mcp__playwright__browser_navigate')
            if nav_func:
                nav_func(url=url)
                
            # Wait for content
            wait_func = self.mcp_functions.get('mcp__playwright__browser_wait_for')
            if wait_func:
                wait_func(time=3)
            
            # Get snapshot
            snapshot_func = self.mcp_functions.get('mcp__playwright__browser_snapshot')
            if snapshot_func:
                snapshot = snapshot_func()
                # Extract text from snapshot
                if isinstance(snapshot, dict):
                    return snapshot.get('text', '')
                return str(snapshot)
                
        except Exception as e:
            logger.error(f"MCP Playwright failed: {e}")
            
        return self._scrape_enhanced(url)
    
    def _extract_content(self, html: str) -> str:
        """Extract article content from HTML.
        
        Args:
            html: Raw HTML content
            
        Returns:
            Extracted text content
        """
        soup = BeautifulSoup(html, 'html.parser')
        
        # First, check if this is a paywalled or gated content page
        # Look for common paywall indicators
        paywall_indicators = ['iframe.omedagate', '.paywall', '.subscriber-only', '.premium-content']
        for indicator in paywall_indicators:
            if soup.select_one(indicator):
                logger.debug(f"Paywall/gated content detected: {indicator}")
                # Still try to extract what's available
                break
        
        # Try each selector until we find content
        for selector in self.CONTENT_SELECTORS:
            element = soup.select_one(selector)
            if element:
                # Remove unwanted elements
                for tag in element.select('script, style, nav, header, footer, aside, .related-posts, .newsletter-signup'):
                    tag.decompose()
                
                # Get text and clean it
                text = element.get_text(separator='\n', strip=True)
                logger.debug(f"Selector '{selector}' found {len(text)} chars of text")
                if len(text) > 100:  # Minimum content threshold
                    logger.debug(f"Using selector '{selector}' for content extraction")
                    return self._clean_text(text)
        
        # Enhanced fallback: Try article.post specifically for FreightCaviar
        article_post = soup.select_one('article.post')
        if article_post:
            # Remove unwanted elements
            for tag in article_post.select('script, style, nav, header, footer, aside'):
                tag.decompose()
            text = article_post.get_text(separator='\n', strip=True)
            logger.debug(f"article.post selector found {len(text)} chars")
            if len(text) > 100:
                logger.debug("Using article.post for content extraction")
                return self._clean_text(text)
        
        # Check if this might be a landing/index page (multiple article cards)
        article_cards = soup.select('.post-card, .article-card, .entry-card')
        if len(article_cards) > 2:
            logger.debug(f"Detected landing page with {len(article_cards)} article cards")
            # This is likely not an article page, return empty
            return ""
        
        # Fallback: get all paragraphs
        paragraphs = soup.find_all('p')
        logger.debug(f"Found {len(paragraphs)} paragraph tags")
        if paragraphs:
            # Filter out very short paragraphs (likely navigation or metadata)
            valid_paragraphs = [p for p in paragraphs if len(p.get_text(strip=True)) > 30]
            if valid_paragraphs:
                text = '\n'.join(p.get_text(strip=True) for p in valid_paragraphs)
                logger.debug(f"Valid paragraphs contain {len(text)} chars of text")
                if len(text) > 100:
                    return self._clean_text(text)
        
        # Final fallback: Check for any content div/section
        content_containers = soup.select('div.content, section.content, div.article-body, section.article-body')
        for container in content_containers:
            text = container.get_text(separator='\n', strip=True)
            if len(text) > 100:
                logger.debug(f"Found content in fallback container: {len(text)} chars")
                return self._clean_text(text)
        
        logger.warning("No content could be extracted from any selector")
        return ""
    
    def _clean_text(self, text: str) -> str:
        """Clean extracted text.
        
        Args:
            text: Raw extracted text
            
        Returns:
            Cleaned text
        """
        # Remove excessive whitespace
        lines = []
        for line in text.split('\n'):
            line = ' '.join(line.split())  # Normalize whitespace
            if line:  # Keep non-empty lines
                lines.append(line)
        
        # Join with single newlines
        return '\n'.join(lines)
    
    def _log_stats(self):
        """Log scraping statistics."""
        total = self.stats['total']
        if total > 0:
            success_rate = (self.stats['success'] / total) * 100
            logger.info(f"Scraping complete: {self.stats['success']}/{total} "
                       f"successful ({success_rate:.1f}%)")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get scraping statistics.
        
        Returns:
            Dictionary of statistics
        """
        return self.stats.copy()
    
    def close(self):
        """Clean up resources."""
        if hasattr(self, 'session'):
            self.session.close()


# Factory function for backward compatibility
def create_scraper(strategy: str = "enhanced", **kwargs) -> WebScraper:
    """Create a web scraper with the specified strategy.
    
    Args:
        strategy: Strategy name ('basic', 'enhanced', 'cloudscraper', 'mcp_playwright')
        **kwargs: Additional arguments for WebScraper
        
    Returns:
        Configured WebScraper instance with robust defaults
    """
    strategy_map = {
        'basic': ScrapingStrategy.BASIC,
        'enhanced': ScrapingStrategy.ENHANCED,
        'cloudscraper': ScrapingStrategy.CLOUDSCRAPER,
        'mcp_playwright': ScrapingStrategy.MCP_PLAYWRIGHT,
        'mcp': ScrapingStrategy.MCP_PLAYWRIGHT,  # Alias
        'legacy': ScrapingStrategy.BASIC,  # For backward compatibility
        'unified': ScrapingStrategy.ENHANCED,  # Default unified behavior
    }
    
    scraping_strategy = strategy_map.get(strategy, ScrapingStrategy.ENHANCED)
    
    # Set robust defaults for production reliability
    defaults = {
        'delay': 2.0,  # Increased from 1.0 to avoid rate limiting
        'timeout': 20,  # Increased from 10 for slower connections
        'max_retries': 5  # Increased from 3 for better resilience
    }
    
    # Override defaults with provided kwargs
    for key, value in kwargs.items():
        defaults[key] = value
    
    return WebScraper(strategy=scraping_strategy, **defaults)