"""Web scraping functionality for extracting full article content."""

import requests
from bs4 import BeautifulSoup
from typing import Optional
import time
from urllib.parse import urljoin, urlparse

from content_pipeline.core.models import Article


class WebScraper:
    """Web scraper for extracting full article content."""
    
    def __init__(self, delay: float = 1.0, timeout: int = 10):
        """Initialize web scraper.
        
        Args:
            delay: Delay between requests in seconds
            timeout: Request timeout in seconds
        """
        self.delay = delay
        self.timeout = timeout
        self.session = requests.Session()
        
        # Set a user agent to avoid being blocked
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def scrape_article_content(self, article: Article) -> Article:
        """Scrape the full content of an article.
        
        Args:
            article: Article object with URL to scrape
            
        Returns:
            Updated Article object with full content
        """
        if not article.url:
            return article
        
        try:
            # Add delay between requests
            time.sleep(self.delay)
            
            # Fetch the webpage
            response = self.session.get(article.url, timeout=self.timeout)
            response.raise_for_status()
            
            # Parse HTML content
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract content using various strategies
            content = self._extract_content(soup)
            
            # Update the article with full content
            article.content = content
            article.scraped = True
            
            return article
            
        except Exception as e:
            print(f"Error scraping article {article.url}: {e}")
            article.scraped = False
            return article
    
    def _extract_content(self, soup: BeautifulSoup) -> str:
        """Extract main content from HTML soup.
        
        Args:
            soup: BeautifulSoup object
            
        Returns:
            Extracted content as string
        """
        content_selectors = [
            # Common article content selectors
            'article',
            '.entry-content',
            '.post-content',
            '.article-content',
            '.content',
            '.post-body',
            '.article-body',
            'main',
            # Fallback to paragraphs
            'p'
        ]
        
        for selector in content_selectors:
            elements = soup.select(selector)
            if elements:
                # If we found article/main containers, use them
                if selector in ['article', 'main', '.entry-content', '.post-content', '.article-content']:
                    content_parts = []
                    for element in elements[:1]:  # Take first match for containers
                        # Extract text from paragraphs within the container
                        paragraphs = element.find_all('p')
                        if paragraphs:
                            content_parts.extend([p.get_text().strip() for p in paragraphs if p.get_text().strip()])
                        else:
                            # Fallback to element text
                            text = element.get_text().strip()
                            if text:
                                content_parts.append(text)
                    
                    if content_parts:
                        return '\n\n'.join(content_parts)
                
                # For paragraph selectors, take multiple paragraphs
                elif selector == 'p':
                    paragraphs = [p.get_text().strip() for p in elements if p.get_text().strip()]
                    if len(paragraphs) >= 3:  # Only use if we have substantial content
                        return '\n\n'.join(paragraphs)
        
        # Final fallback - extract all text
        return soup.get_text().strip()
    
    def _clean_text(self, text: str) -> str:
        """Clean extracted text.
        
        Args:
            text: Raw text to clean
            
        Returns:
            Cleaned text
        """
        if not text:
            return ""
        
        # Split into lines and clean each line
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            if line and len(line) > 10:  # Filter out very short lines
                cleaned_lines.append(line)
        
        # Join with double newlines for paragraphs
        return '\n\n'.join(cleaned_lines)
    
    def test_url(self, url: str) -> bool:
        """Test if a URL is accessible.
        
        Args:
            url: URL to test
            
        Returns:
            True if URL is accessible, False otherwise
        """
        try:
            response = self.session.head(url, timeout=self.timeout)
            return response.status_code == 200
        except Exception:
            return False
    
    def close(self):
        """Close the session."""
        self.session.close()