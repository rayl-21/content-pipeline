"""Unified web scraper with strategy pattern for different scraping methods.

This module consolidates all scraping functionality into a single, configurable class
that eliminates special cases and provides a clean interface for web scraping.
"""

import logging
import random
import re
import time
from enum import Enum
from typing import Dict, List, Optional, Any, Callable, Tuple
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
    RSS_FALLBACK = "rss_fallback"
    NONE = "none"


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
        
        # Enhanced statistics
        self.stats = {
            'total': 0,
            'success': 0,
            'failed': 0,
            'rss_fallback': 0,
            'high_confidence': 0,  # confidence >= 0.7
            'medium_confidence': 0,  # 0.4 <= confidence < 0.7
            'low_confidence': 0,  # confidence < 0.4
            'total_confidence': 0.0,
            'failure_reasons': {}
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
        """Scrape a single article with RSS fallback.
        
        Args:
            article: Article object with URL to scrape
            
        Returns:
            Updated Article object with scraped content or RSS fallback
        """
        self.stats['total'] += 1
        
        try:
            # Apply delay
            time.sleep(self.delay)
            
            # Get content based on strategy (now returns tuple)
            content, confidence = self._scrape_with_strategy(article.url)
            
            if content and len(content.strip()) > 100:
                # Full content successfully extracted
                article.content = content
                article.scraping_success = True
                article.scraping_strategy = self.strategy
                article.extraction_confidence = confidence
                article.failure_reason = ""
                self.stats['success'] += 1
                
                # Track confidence levels
                self.stats['total_confidence'] += confidence
                if confidence >= 0.7:
                    self.stats['high_confidence'] += 1
                elif confidence >= 0.4:
                    self.stats['medium_confidence'] += 1
                else:
                    self.stats['low_confidence'] += 1
                
                logger.info(f"Successfully scraped full content (confidence {confidence:.2f}): {article.title[:50]}")
            elif hasattr(article, 'description') and article.description:
                # Fallback to RSS description
                article.content = article.description
                article.scraping_success = True
                article.scraping_strategy = ScrapingStrategy.RSS_FALLBACK
                article.extraction_confidence = 0.3  # Low confidence for RSS fallback
                article.failure_reason = "Content extraction failed, using RSS description"
                self.stats['success'] += 1
                self.stats['rss_fallback'] += 1
                self.stats['low_confidence'] += 1
                self.stats['total_confidence'] += 0.3
                logger.warning(f"Using RSS description as fallback: {article.title[:50]}")
            else:
                # Complete failure - no content and no description
                article.content = ""
                article.scraping_success = False
                article.scraping_strategy = ScrapingStrategy.NONE
                article.extraction_confidence = 0.0
                article.failure_reason = "No content extracted and no RSS description available"
                self.stats['failed'] += 1
                
                # Track failure reason
                reason = "No RSS fallback"
                self.stats['failure_reasons'][reason] = self.stats['failure_reasons'].get(reason, 0) + 1
                
                logger.error(f"No content extracted and no RSS fallback: {article.title[:50]}")
                
        except Exception as e:
            # Handle exceptions with fallback
            self.stats['failed'] += 1
            error_msg = str(e)
            logger.error(f"Scraping failed for {article.url}: {error_msg}")
            
            # Track failure reason
            error_type = type(e).__name__
            self.stats['failure_reasons'][error_type] = self.stats['failure_reasons'].get(error_type, 0) + 1
            
            # Try RSS fallback even on exception
            if hasattr(article, 'description') and article.description:
                article.content = article.description
                article.scraping_success = True
                article.scraping_strategy = ScrapingStrategy.RSS_FALLBACK
                article.extraction_confidence = 0.3
                article.failure_reason = f"Scraping error: {error_msg[:200]}, using RSS fallback"
                self.stats['rss_fallback'] += 1
                self.stats['low_confidence'] += 1
                self.stats['total_confidence'] += 0.3
                logger.warning(f"Using RSS fallback after error: {article.title[:50]}")
            else:
                article.content = ""
                article.scraping_success = False
                article.scraping_strategy = ScrapingStrategy.NONE
                article.extraction_confidence = 0.0
                article.failure_reason = f"Scraping error: {error_msg[:200]}"
            
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
    
    def _scrape_with_strategy(self, url: str) -> Tuple[str, float]:
        """Scrape content using the configured strategy.
        
        Args:
            url: URL to scrape
            
        Returns:
            Tuple of (extracted content, confidence score)
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
                result = scraper(url)
                if result and result[0]:  # Check if content exists
                    return result
            except Exception as e:
                logger.debug(f"Attempt {attempt + 1} failed: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
        
        return "", 0.0
    
    def _scrape_basic(self, url: str) -> Tuple[str, float]:
        """Basic scraping with requests."""
        response = self.session.get(url, timeout=self.timeout)
        response.raise_for_status()
        return self._extract_content(response.text)
    
    def _scrape_enhanced(self, url: str) -> Tuple[str, float]:
        """Enhanced scraping with user-agent rotation."""
        # Rotate user agent
        self.session.headers['User-Agent'] = random.choice(self.USER_AGENTS)
        
        # Add referer for better success rate
        domain = urlparse(url).netloc
        self.session.headers['Referer'] = f"https://{domain}/"
        
        response = self.session.get(url, timeout=self.timeout)
        response.raise_for_status()
        return self._extract_content(response.text)
    
    def _scrape_cloudscraper(self, url: str) -> Tuple[str, float]:
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
    
    def _scrape_mcp_playwright(self, url: str) -> Tuple[str, float]:
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
                    text = snapshot.get('text', '')
                    # High confidence for MCP Playwright since it's JS-rendered
                    confidence = 0.9 if len(text) > 100 else 0.3
                    return text, confidence
                text = str(snapshot)
                confidence = 0.8 if len(text) > 100 else 0.3
                return text, confidence
                
        except Exception as e:
            logger.error(f"MCP Playwright failed: {e}")
            
        return self._scrape_enhanced(url)
    
    def _extract_content(self, html: str) -> tuple[str, float]:
        """Extract article content from HTML with confidence scoring.
        
        Args:
            html: Raw HTML content
            
        Returns:
            Tuple of (extracted text content, confidence score 0.0-1.0)
        """
        soup = BeautifulSoup(html, 'html.parser')
        confidence = 0.0
        
        # First, check if this is a paywalled or gated content page
        # Look for common paywall indicators
        paywall_indicators = ['iframe.omedagate', '.paywall', '.subscriber-only', '.premium-content']
        for indicator in paywall_indicators:
            if soup.select_one(indicator):
                logger.debug(f"Paywall/gated content detected: {indicator}")
                confidence = 0.1  # Very low confidence for paywalled content
                # Still try to extract what's available
                break
        
        # Check if this might be a landing/index page (multiple article cards)
        article_cards = soup.select('.post-card, .article-card, .entry-card')
        if len(article_cards) > 2:
            logger.debug(f"Detected landing page with {len(article_cards)} article cards")
            # This is likely not an article page
            return "", 0.0
        
        # Try each selector until we find content
        for i, selector in enumerate(self.CONTENT_SELECTORS):
            element = soup.select_one(selector)
            if element:
                # Remove unwanted elements
                for tag in element.select('script, style, nav, header, footer, aside, .related-posts, .newsletter-signup'):
                    tag.decompose()
                
                # Get text and clean it
                text = element.get_text(separator='\n', strip=True)
                logger.debug(f"Selector '{selector}' found {len(text)} chars of text")
                
                if len(text) > 100:  # Minimum content threshold
                    # Calculate confidence based on selector priority and content quality
                    selector_confidence = 1.0 - (i * 0.05)  # Higher priority selectors = higher confidence
                    
                    # Content quality checks
                    word_count = len(text.split())
                    sentence_count = len(re.split(r'[.!?]+', text))
                    avg_sentence_length = word_count / max(sentence_count, 1)
                    
                    # Confidence factors
                    length_confidence = min(word_count / 500, 1.0)  # 500+ words = full confidence
                    structure_confidence = 1.0 if 10 < avg_sentence_length < 30 else 0.7
                    
                    # Check for article-like patterns
                    has_paragraphs = '\n' in text
                    pattern_confidence = 1.0 if has_paragraphs else 0.8
                    
                    confidence = min(
                        selector_confidence * 0.4 +  # Selector quality
                        length_confidence * 0.3 +     # Content length
                        structure_confidence * 0.2 +  # Sentence structure
                        pattern_confidence * 0.1,      # Article patterns
                        1.0
                    )
                    
                    logger.debug(f"Using selector '{selector}' with confidence {confidence:.2f}")
                    return self._clean_text(text), confidence
        
        # Enhanced fallback: Try article.post specifically for FreightCaviar
        article_post = soup.select_one('article.post')
        if article_post:
            # Remove unwanted elements
            for tag in article_post.select('script, style, nav, header, footer, aside'):
                tag.decompose()
            text = article_post.get_text(separator='\n', strip=True)
            logger.debug(f"article.post selector found {len(text)} chars")
            if len(text) > 100:
                word_count = len(text.split())
                confidence = min(word_count / 500, 0.6)  # Max 0.6 confidence for fallback
                logger.debug(f"Using article.post fallback with confidence {confidence:.2f}")
                return self._clean_text(text), confidence
        
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
                    word_count = len(text.split())
                    confidence = min(word_count / 500, 0.5)  # Max 0.5 confidence for paragraph fallback
                    return self._clean_text(text), confidence
        
        # Final fallback: Check for any content div/section
        content_containers = soup.select('div.content, section.content, div.article-body, section.article-body')
        for container in content_containers:
            text = container.get_text(separator='\n', strip=True)
            if len(text) > 100:
                word_count = len(text.split())
                confidence = min(word_count / 500, 0.4)  # Max 0.4 confidence for generic container
                logger.debug(f"Found content in fallback container: {len(text)} chars, confidence {confidence:.2f}")
                return self._clean_text(text), confidence
        
        logger.warning("No content could be extracted from any selector")
        return "", 0.0
    
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
        """Log detailed scraping statistics."""
        total = self.stats['total']
        if total > 0:
            success_rate = (self.stats['success'] / total) * 100
            avg_confidence = self.stats['total_confidence'] / max(self.stats['success'], 1)
            
            logger.info(f"Scraping complete: {self.stats['success']}/{total} "
                       f"successful ({success_rate:.1f}%)")
            logger.info(f"Average confidence: {avg_confidence:.2f}")
            logger.info(f"Confidence breakdown - High: {self.stats['high_confidence']}, "
                       f"Medium: {self.stats['medium_confidence']}, "
                       f"Low: {self.stats['low_confidence']}")
            logger.info(f"RSS fallbacks used: {self.stats['rss_fallback']}")
            
            if self.stats['failure_reasons']:
                logger.info("Failure reasons:")
                for reason, count in self.stats['failure_reasons'].items():
                    logger.info(f"  - {reason}: {count}")
    
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