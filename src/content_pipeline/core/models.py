"""Data models for the content pipeline."""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional


@dataclass
class Article:
    """Represents a news article."""
    title: str
    url: str
    published_date: datetime
    description: str
    content: str = ""
    content_ideas: List[str] = None
    
    def __post_init__(self):
        if self.content_ideas is None:
            self.content_ideas = []


@dataclass
class ContentIdea:
    """Represents a brainstormed content idea."""
    title: str
    description: str
    keywords: List[str]
    content_type: str  # "blog", "social", "video", etc.