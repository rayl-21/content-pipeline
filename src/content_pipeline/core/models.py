"""Standardized data models for the content pipeline with validation and type safety."""

import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any
from urllib.parse import urlparse


class SourceFeed(str, Enum):
    """Enumeration of available source feeds."""
    FREIGHT_WAVES = "FreightWaves"
    FREIGHT_CAVIAR = "FreightCaviar"
    CUSTOM = "Custom"


class ScrapingStrategy(str, Enum):
    """Enumeration of scraping strategies."""
    BASIC = "basic"
    ENHANCED = "enhanced"
    CLOUDSCRAPER = "cloudscraper"
    MCP_PLAYWRIGHT = "mcp_playwright"
    RSS_FALLBACK = "rss_fallback"
    NONE = "none"


class ContentType(str, Enum):
    """Enumeration of content types for ideas."""
    BLOG_POST = "blog"
    VIDEO = "video"
    INFOGRAPHIC = "infographic"
    PODCAST = "podcast"
    SOCIAL_MEDIA = "social_media"
    NEWSLETTER = "newsletter"
    WHITEPAPER = "whitepaper"


class Priority(str, Enum):
    """Priority levels for content ideas."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ContentStatus(str, Enum):
    """Status tracking for content ideas."""
    PROPOSED = "proposed"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    REJECTED = "rejected"
    ON_HOLD = "on_hold"


def validate_url(url: str) -> bool:
    """Validate if a string is a valid URL."""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False


def sanitize_text(text: str, max_length: Optional[int] = None) -> str:
    """Sanitize text by removing control characters and limiting length."""
    if not text:
        return ""
    
    # Remove control characters except spaces, newlines and tabs
    # This regex preserves spaces (0x20), tabs (0x09), and newlines (0x0A, 0x0D)
    sanitized = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', ' ', text)
    
    # Normalize whitespace (multiple spaces/tabs/newlines to single space)
    sanitized = re.sub(r'\s+', ' ', sanitized).strip()
    
    # Apply max length if specified
    if max_length and len(sanitized) > max_length:
        sanitized = sanitized[:max_length-3] + "..."
    
    return sanitized


@dataclass
class Article:
    """
    Represents a standardized news article with validation and metadata.
    
    Attributes:
        id: Unique identifier (UUID)
        url: Article URL (unique, validated)
        title: Article title (required, max 500 chars)
        description: Article summary/description
        content: Full article content
        author: Article author (max 200 chars)
        published_date: When the article was published
        source_feed: Which feed the article came from
        scraping_strategy: Strategy used to scrape the article
        scraping_success: Whether scraping was successful
        created_at: When the article was added to our system
        updated_at: When the article was last updated
        word_count: Calculated word count of content
        keywords: List of keywords/tags
        categories: List of categories
    """
    # Required fields
    url: str
    title: str
    published_date: datetime
    source_feed: SourceFeed
    
    # Optional fields with defaults
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    description: str = ""
    content: str = ""
    author: str = ""
    scraping_strategy: ScrapingStrategy = ScrapingStrategy.NONE
    scraping_success: bool = False
    extraction_confidence: float = 0.0  # 0.0 to 1.0 confidence score
    failure_reason: str = ""  # Detailed failure reason if scraping failed
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    word_count: int = 0
    keywords: List[str] = field(default_factory=list)
    categories: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Validate and sanitize data after initialization."""
        # Validate URL
        if not validate_url(self.url):
            raise ValueError(f"Invalid URL: {self.url}")
        
        # Sanitize text fields
        self.title = sanitize_text(self.title, max_length=500)
        if not self.title:
            raise ValueError("Title cannot be empty")
        
        self.description = sanitize_text(self.description)
        self.author = sanitize_text(self.author, max_length=200)
        
        # Calculate word count if content exists
        if self.content:
            self.word_count = len(self.content.split())
        
        # Ensure lists are properly initialized
        if self.keywords is None:
            self.keywords = []
        if self.categories is None:
            self.categories = []
        
        # Clean up lists
        self.keywords = [sanitize_text(k, max_length=50) for k in self.keywords if k]
        self.categories = [sanitize_text(c, max_length=100) for c in self.categories if c]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert article to dictionary for serialization."""
        return {
            "id": self.id,
            "url": self.url,
            "title": self.title,
            "description": self.description,
            "content": self.content,
            "author": self.author,
            "published_date": self.published_date.isoformat() if self.published_date else None,
            "source_feed": self.source_feed.value if isinstance(self.source_feed, Enum) else self.source_feed,
            "scraping_strategy": self.scraping_strategy.value if isinstance(self.scraping_strategy, Enum) else self.scraping_strategy,
            "scraping_success": self.scraping_success,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "word_count": self.word_count,
            "extraction_confidence": self.extraction_confidence,
            "failure_reason": self.failure_reason,
            "keywords": self.keywords,
            "categories": self.categories
        }
    
    def to_sheet_row(self) -> List[Any]:
        """Convert article to a row format for Google Sheets."""
        return [
            self.id,
            self.url,
            self.title,
            self.description,
            self.content,  # Full content, no truncation in data layer
            self.author,
            self.published_date.strftime("%Y-%m-%d %H:%M:%S") if self.published_date else "",
            self.source_feed.value if isinstance(self.source_feed, Enum) else self.source_feed,
            self.scraping_strategy.value if isinstance(self.scraping_strategy, Enum) else self.scraping_strategy,
            "Yes" if self.scraping_success else "No",
            self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else "",
            self.updated_at.strftime("%Y-%m-%d %H:%M:%S") if self.updated_at else "",
            self.word_count,
            f"{self.extraction_confidence:.2f}" if self.extraction_confidence else "0.00",
            self.failure_reason,
            ", ".join(self.keywords) if self.keywords else "",
            ", ".join(self.categories) if self.categories else ""
        ]
    
    @staticmethod
    def sheet_headers() -> List[str]:
        """Return standardized headers for Google Sheets."""
        return [
            "ID",
            "URL",
            "Title",
            "Description",
            "Content",
            "Author",
            "Published Date",
            "Source Feed",
            "Scraping Strategy",
            "Scraping Success",
            "Created At",
            "Updated At",
            "Word Count",
            "Extraction Confidence",
            "Failure Reason",
            "Keywords",
            "Categories"
        ]
    
    # Backward compatibility properties
    @property
    def summary(self) -> str:
        """Legacy property mapping to description."""
        return self.description
    
    @summary.setter
    def summary(self, value: str):
        """Legacy property setter mapping to description."""
        self.description = value
    
    @property
    def scraped(self) -> bool:
        """Legacy property mapping to scraping_success."""
        return self.scraping_success
    
    @scraped.setter
    def scraped(self, value: bool):
        """Legacy property setter mapping to scraping_success."""
        self.scraping_success = value
    
    @property
    def source(self) -> str:
        """Legacy property mapping to source_feed."""
        return self.source_feed.value if isinstance(self.source_feed, Enum) else self.source_feed
    
    @source.setter
    def source(self, value: str):
        """Legacy property setter mapping to source_feed."""
        # Try to map to enum, fallback to CUSTOM
        for feed in SourceFeed:
            if feed.value.lower() == str(value).lower():
                self.source_feed = feed
                return
        self.source_feed = SourceFeed.CUSTOM


@dataclass
class ContentIdea:
    """
    Represents a standardized content idea with lifecycle tracking.
    
    Attributes:
        id: Unique identifier (UUID)
        idea_title: Title of the content idea (required)
        idea_description: Detailed description of the idea
        target_audience: Who this content is for
        content_type: Type of content (blog, video, etc.)
        priority: Priority level
        keywords: SEO keywords
        source_articles: List of article IDs that inspired this idea
        created_at: When the idea was created
        status: Current status of the idea
        themes: Content themes
    """
    # Required fields
    idea_title: str
    content_type: ContentType
    
    # Optional fields with defaults
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    idea_description: str = ""
    target_audience: str = ""
    priority: Priority = Priority.MEDIUM
    keywords: List[str] = field(default_factory=list)
    source_articles: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    status: ContentStatus = ContentStatus.PROPOSED
    themes: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Validate and sanitize data after initialization."""
        # Sanitize text fields
        self.idea_title = sanitize_text(self.idea_title, max_length=200)
        if not self.idea_title:
            raise ValueError("Idea title cannot be empty")
        
        self.idea_description = sanitize_text(self.idea_description)
        self.target_audience = sanitize_text(self.target_audience, max_length=100)
        
        # Ensure lists are properly initialized
        if self.keywords is None:
            self.keywords = []
        if self.source_articles is None:
            self.source_articles = []
        if self.themes is None:
            self.themes = []
        
        # Clean up lists
        self.keywords = [sanitize_text(k, max_length=50) for k in self.keywords if k]
        self.themes = [sanitize_text(t, max_length=100) for t in self.themes if t]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert content idea to dictionary for serialization."""
        return {
            "id": self.id,
            "idea_title": self.idea_title,
            "idea_description": self.idea_description,
            "target_audience": self.target_audience,
            "content_type": self.content_type.value if isinstance(self.content_type, Enum) else self.content_type,
            "priority": self.priority.value if isinstance(self.priority, Enum) else self.priority,
            "keywords": self.keywords,
            "source_articles": self.source_articles,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "status": self.status.value if isinstance(self.status, Enum) else self.status,
            "themes": self.themes
        }
    
    def to_sheet_row(self) -> List[Any]:
        """Convert content idea to a row format for Google Sheets."""
        return [
            self.id,
            self.idea_title,
            self.idea_description,
            self.target_audience,
            self.content_type.value if isinstance(self.content_type, Enum) else self.content_type,
            self.priority.value if isinstance(self.priority, Enum) else self.priority,
            ", ".join(self.keywords) if self.keywords else "",
            ", ".join(self.source_articles) if self.source_articles else "",
            self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else "",
            self.status.value if isinstance(self.status, Enum) else self.status,
            ", ".join(self.themes) if self.themes else ""
        ]
    
    @staticmethod
    def sheet_headers() -> List[str]:
        """Return standardized headers for Google Sheets."""
        return [
            "ID",
            "Idea Title",
            "Idea Description",
            "Target Audience",
            "Content Type",
            "Priority",
            "Keywords",
            "Source Articles",
            "Created At",
            "Status",
            "Themes"
        ]
    
    # Backward compatibility properties
    @property
    def title(self) -> str:
        """Legacy property mapping to idea_title."""
        return self.idea_title
    
    @title.setter
    def title(self, value: str):
        """Legacy property setter mapping to idea_title."""
        self.idea_title = value
    
    @property
    def description(self) -> str:
        """Legacy property mapping to idea_description."""
        return self.idea_description
    
    @description.setter
    def description(self, value: str):
        """Legacy property setter mapping to idea_description."""
        self.idea_description = value


@dataclass
class SummaryReport:
    """
    Represents a pipeline run summary with structured metrics.
    
    Attributes:
        run_id: Unique identifier for this run
        run_date: When the pipeline was run
        total_articles_fetched: Total number of articles fetched
        articles_scraped_successfully: Number of successfully scraped articles
        scraping_success_rate: Percentage of successful scrapes
        ideas_generated: Number of content ideas generated
        processing_time_seconds: Total processing time
        errors: List of errors encountered
        feed_statistics: Per-feed statistics
    """
    # Required fields
    run_date: datetime
    total_articles_fetched: int
    articles_scraped_successfully: int
    ideas_generated: int
    
    # Optional fields with defaults
    run_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    scraping_success_rate: float = 0.0
    processing_time_seconds: float = 0.0
    errors: List[Dict[str, Any]] = field(default_factory=list)
    feed_statistics: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    def __post_init__(self):
        """Calculate derived fields after initialization."""
        # Calculate success rate
        if self.total_articles_fetched > 0:
            self.scraping_success_rate = (
                self.articles_scraped_successfully / self.total_articles_fetched * 100
            )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert summary report to dictionary for serialization."""
        return {
            "run_id": self.run_id,
            "run_date": self.run_date.isoformat() if self.run_date else None,
            "total_articles_fetched": self.total_articles_fetched,
            "articles_scraped_successfully": self.articles_scraped_successfully,
            "scraping_success_rate": round(self.scraping_success_rate, 2),
            "ideas_generated": self.ideas_generated,
            "processing_time_seconds": round(self.processing_time_seconds, 2),
            "errors": self.errors,
            "feed_statistics": self.feed_statistics
        }
    
    def to_sheet_row(self) -> List[Any]:
        """Convert summary report to a row format for Google Sheets."""
        import json
        
        return [
            self.run_id,
            self.run_date.strftime("%Y-%m-%d %H:%M:%S") if self.run_date else "",
            self.total_articles_fetched,
            self.articles_scraped_successfully,
            f"{self.scraping_success_rate:.1f}%",
            self.ideas_generated,
            round(self.processing_time_seconds, 2),
            json.dumps(self.errors) if self.errors else "[]",
            json.dumps(self.feed_statistics) if self.feed_statistics else "{}"
        ]
    
    @staticmethod
    def sheet_headers() -> List[str]:
        """Return standardized headers for Google Sheets."""
        return [
            "Run ID",
            "Run Date",
            "Total Articles Fetched",
            "Articles Scraped Successfully",
            "Scraping Success Rate",
            "Ideas Generated",
            "Processing Time (seconds)",
            "Errors",
            "Feed Statistics"
        ]