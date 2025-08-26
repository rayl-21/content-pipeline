"""RSS feed monitoring and article extraction."""

import feedparser
import requests
from datetime import datetime, timezone
from typing import List, Optional
from urllib.parse import urlparse

from ..core.models import Article, SourceFeed


class RSSMonitor:
    """Monitors RSS feeds and extracts article information."""
    
    def __init__(self, feed_url: str, timeout: int = 10):
        """Initialize RSS monitor.
        
        Args:
            feed_url: URL of the RSS feed to monitor
            timeout: Request timeout in seconds
        """
        self.feed_url = feed_url
        self.timeout = timeout
    
    def is_feed_accessible(self) -> bool:
        """Test if the RSS feed is accessible.
        
        Returns:
            True if feed is accessible, False otherwise
        """
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (compatible; ContentPipeline/1.0)',
                'Accept': 'application/rss+xml, application/xml, text/xml, */*',
            }
            response = requests.get(self.feed_url, timeout=self.timeout, headers=headers)
            return response.status_code == 200
        except Exception:
            return False
    
    def fetch_latest_articles(self, limit: int = 5) -> List[Article]:
        """Fetch the latest articles from the RSS feed.
        
        Args:
            limit: Maximum number of articles to fetch
            
        Returns:
            List of Article objects
        """
        try:
            # Set user agent for feedparser for better compatibility
            feedparser.USER_AGENT = "Mozilla/5.0 (compatible; ContentPipeline/1.0)"
            
            # Parse the RSS feed
            feed = feedparser.parse(self.feed_url)
            
            if not feed.entries:
                return []
            
            articles = []
            for entry in feed.entries[:limit]:
                article = self._parse_entry(entry)
                if article:
                    articles.append(article)
            
            return articles
            
        except Exception as e:
            print(f"Error fetching RSS feed: {e}")
            return []
    
    def _parse_entry(self, entry) -> Optional[Article]:
        """Parse a feed entry into an Article object.
        
        Args:
            entry: RSS feed entry
            
        Returns:
            Article object or None if parsing fails
        """
        try:
            # Extract basic information
            title = getattr(entry, 'title', 'No Title')
            url = getattr(entry, 'link', '')
            
            # Parse published date
            published_date = datetime.now(timezone.utc)
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                try:
                    published_date = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
                except (TypeError, ValueError):
                    pass
            elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                try:
                    published_date = datetime(*entry.updated_parsed[:6], tzinfo=timezone.utc)
                except (TypeError, ValueError):
                    pass
            
            # Extract summary/description
            description = ''
            if hasattr(entry, 'summary'):
                description = entry.summary
            elif hasattr(entry, 'description'):
                description = entry.description
            
            # Extract author
            author = getattr(entry, 'author', '')
            
            # Extract categories/tags
            categories = []
            if hasattr(entry, 'tags'):
                categories = [tag.term for tag in entry.tags if hasattr(tag, 'term')]
            
            # Determine source feed from URL
            source_feed = SourceFeed.CUSTOM
            if 'freightwaves' in url.lower():
                source_feed = SourceFeed.FREIGHT_WAVES
            elif 'freightcaviar' in url.lower():
                source_feed = SourceFeed.FREIGHT_CAVIAR
            
            return Article(
                title=title,
                url=url,
                published_date=published_date,
                description=description,  # Using standardized field name
                author=author,
                categories=categories,
                source_feed=source_feed  # Add source feed
            )
            
        except Exception as e:
            print(f"Error parsing entry: {e}")
            return None
    
    def get_feed_info(self) -> dict:
        """Get information about the RSS feed.
        
        Returns:
            Dictionary containing feed metadata
        """
        try:
            feed = feedparser.parse(self.feed_url)
            
            return {
                'title': getattr(feed.feed, 'title', 'Unknown Feed'),
                'description': getattr(feed.feed, 'description', ''),
                'link': getattr(feed.feed, 'link', ''),
                'language': getattr(feed.feed, 'language', ''),
                'updated': getattr(feed.feed, 'updated', ''),
                'total_entries': len(feed.entries)
            }
            
        except Exception as e:
            return {'error': str(e)}