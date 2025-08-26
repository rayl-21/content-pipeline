"""Configuration settings for the content pipeline."""

from dataclasses import dataclass
from typing import List


@dataclass
class FeedConfig:
    """Configuration for a single RSS feed."""
    name: str
    url: str
    article_limit: int = 5
    enabled: bool = True


@dataclass
class PipelineConfig:
    """Main configuration for the content pipeline."""
    # RSS Feeds to monitor
    feeds: List[FeedConfig] = None
    
    # Google Sheets configuration
    credentials_path: str = "content-pipeline-bot-key.json"
    spreadsheet_id: str = "1t01HICK7cCGFK2XDebagMjjfSnN0t04t_c8o0IJh7lQ"
    
    # Scraping configuration - Updated for production reliability
    scraper_delay: float = 2.0  # Increased from 1.0 to avoid rate limiting
    scraper_timeout: int = 20  # Increased from 10 for slower connections
    
    # Default article limit if not specified per feed
    default_article_limit: int = 5
    
    def __post_init__(self):
        """Initialize default feeds if none provided."""
        if self.feeds is None:
            self.feeds = [
                FeedConfig(
                    name="FreightWaves",
                    url="https://www.freightwaves.com/feed",
                    article_limit=5,
                    enabled=True
                ),
                FeedConfig(
                    name="FreightCaviar",
                    url="https://www.freightcaviar.com/latest/rss",
                    article_limit=5,
                    enabled=True
                )
            ]
    
    def get_enabled_feeds(self) -> List[FeedConfig]:
        """Get only enabled feeds."""
        return [feed for feed in self.feeds if feed.enabled]
    
    def get_total_article_limit(self) -> int:
        """Get total number of articles to process across all feeds."""
        return sum(feed.article_limit for feed in self.get_enabled_feeds())
    
    def get_google_sheets_credentials_path(self) -> str:
        """Get Google Sheets credentials path from environment or default."""
        import os
        return os.getenv('GOOGLE_SHEETS_CREDENTIALS_PATH', self.credentials_path)
    
    def get_google_sheets_spreadsheet_id(self) -> str:
        """Get Google Sheets spreadsheet ID from environment or default."""
        import os
        return os.getenv('GOOGLE_SHEETS_SPREADSHEET_ID', self.spreadsheet_id)


# Default configuration instance
DEFAULT_CONFIG = PipelineConfig()