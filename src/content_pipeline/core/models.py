"""Data models for the content pipeline."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional


@dataclass
class Article:
    """Represents a news article."""
    title: str
    url: str
    published_date: datetime
    summary: str = ""
    content: str = ""
    author: str = ""
    categories: List[str] = field(default_factory=list)
    scraped: bool = False
    
    # Legacy field mapping for backward compatibility
    @property
    def description(self) -> str:
        """Legacy property mapping to summary."""
        return self.summary
    
    @description.setter
    def description(self, value: str):
        """Legacy property setter mapping to summary."""
        self.summary = value


@dataclass
class ContentIdea:
    """Represents a brainstormed content idea."""
    title: str
    content_type: str  # "Blog Post", "Social Media Post", "Video Script", etc.
    keywords: List[str] = field(default_factory=list)
    source_articles: List[str] = field(default_factory=list)
    themes: List[str] = field(default_factory=list)
    description: str = ""
    
    def __post_init__(self):
        """Ensure lists are properly initialized."""
        if self.keywords is None:
            self.keywords = []
        if self.source_articles is None:
            self.source_articles = []
        if self.themes is None:
            self.themes = []