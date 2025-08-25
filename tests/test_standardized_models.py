#!/usr/bin/env python3
"""
Test script for standardized data models and Google Sheets integration.

This script validates:
1. Data model creation and validation
2. Backward compatibility
3. Data sanitization
4. Google Sheets integration
"""

import sys
import unittest
from datetime import datetime
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from src.content_pipeline.core.models import (
    Article, ContentIdea, SummaryReport,
    SourceFeed, ScrapingStrategy, ContentType,
    Priority, ContentStatus,
    validate_url, sanitize_text
)


class TestDataValidation(unittest.TestCase):
    """Test data validation functions."""
    
    def test_url_validation(self):
        """Test URL validation."""
        # Valid URLs
        self.assertTrue(validate_url("http://example.com"))
        self.assertTrue(validate_url("https://www.example.com/path"))
        self.assertTrue(validate_url("https://example.com:8080/path?query=value"))
        
        # Invalid URLs
        self.assertFalse(validate_url("not a url"))
        self.assertFalse(validate_url("example.com"))  # Missing scheme
        self.assertFalse(validate_url(""))
        self.assertFalse(validate_url("http://"))  # Missing netloc
    
    def test_text_sanitization(self):
        """Test text sanitization."""
        # Test control character removal
        text_with_control = "Hello\x00World\x07Test"
        self.assertEqual(sanitize_text(text_with_control), "Hello World Test")
        
        # Test whitespace normalization
        text_with_spaces = "Hello   \n\n  World    Test"
        self.assertEqual(sanitize_text(text_with_spaces), "Hello World Test")
        
        # Test max length
        long_text = "a" * 100
        self.assertEqual(sanitize_text(long_text, max_length=10), "aaaaaaa...")
        
        # Test empty string
        self.assertEqual(sanitize_text(""), "")
        self.assertEqual(sanitize_text(None), "")


class TestArticleModel(unittest.TestCase):
    """Test Article data model."""
    
    def setUp(self):
        """Set up test data."""
        self.valid_article_data = {
            "url": "https://example.com/article",
            "title": "Test Article",
            "published_date": datetime.now(),
            "source_feed": SourceFeed.FREIGHT_WAVES
        }
    
    def test_article_creation(self):
        """Test creating a valid article."""
        article = Article(**self.valid_article_data)
        
        self.assertIsNotNone(article.id)
        self.assertEqual(article.url, "https://example.com/article")
        self.assertEqual(article.title, "Test Article")
        self.assertEqual(article.source_feed, SourceFeed.FREIGHT_WAVES)
        self.assertFalse(article.scraping_success)
        self.assertEqual(article.word_count, 0)
    
    def test_article_with_content(self):
        """Test article with content and word count calculation."""
        data = self.valid_article_data.copy()
        data["content"] = "This is a test article with some content."
        
        article = Article(**data)
        self.assertEqual(article.word_count, 8)
    
    def test_article_validation(self):
        """Test article validation."""
        # Invalid URL
        data = self.valid_article_data.copy()
        data["url"] = "not a url"
        
        with self.assertRaises(ValueError) as context:
            Article(**data)
        self.assertIn("Invalid URL", str(context.exception))
        
        # Empty title
        data = self.valid_article_data.copy()
        data["title"] = "   "  # Will be sanitized to empty
        
        with self.assertRaises(ValueError) as context:
            Article(**data)
        self.assertIn("Title cannot be empty", str(context.exception))
    
    def test_article_backward_compatibility(self):
        """Test backward compatibility properties."""
        article = Article(**self.valid_article_data)
        
        # Test summary property
        article.summary = "Test summary"
        self.assertEqual(article.description, "Test summary")
        self.assertEqual(article.summary, "Test summary")
        
        # Test scraped property
        article.scraped = True
        self.assertTrue(article.scraping_success)
        self.assertTrue(article.scraped)
        
        # Test source property
        article.source = "FreightCaviar"
        self.assertEqual(article.source_feed, SourceFeed.FREIGHT_CAVIAR)
        self.assertEqual(article.source, "FreightCaviar")
    
    def test_article_to_dict(self):
        """Test article serialization to dictionary."""
        article = Article(**self.valid_article_data)
        article_dict = article.to_dict()
        
        self.assertIn("id", article_dict)
        self.assertEqual(article_dict["url"], "https://example.com/article")
        self.assertEqual(article_dict["title"], "Test Article")
        self.assertEqual(article_dict["source_feed"], "FreightWaves")
        self.assertEqual(article_dict["scraping_strategy"], "none")
        self.assertFalse(article_dict["scraping_success"])
    
    def test_article_to_sheet_row(self):
        """Test article conversion to sheet row."""
        article = Article(**self.valid_article_data)
        row = article.to_sheet_row()
        
        self.assertEqual(len(row), 15)  # Number of columns
        self.assertEqual(row[1], "https://example.com/article")  # URL
        self.assertEqual(row[2], "Test Article")  # Title
        self.assertEqual(row[7], "FreightWaves")  # Source Feed
        self.assertEqual(row[9], "No")  # Scraping Success


class TestContentIdeaModel(unittest.TestCase):
    """Test ContentIdea data model."""
    
    def setUp(self):
        """Set up test data."""
        self.valid_idea_data = {
            "idea_title": "Test Content Idea",
            "content_type": ContentType.BLOG_POST
        }
    
    def test_idea_creation(self):
        """Test creating a valid content idea."""
        idea = ContentIdea(**self.valid_idea_data)
        
        self.assertIsNotNone(idea.id)
        self.assertEqual(idea.idea_title, "Test Content Idea")
        self.assertEqual(idea.content_type, ContentType.BLOG_POST)
        self.assertEqual(idea.priority, Priority.MEDIUM)
        self.assertEqual(idea.status, ContentStatus.PROPOSED)
    
    def test_idea_with_details(self):
        """Test content idea with additional details."""
        data = self.valid_idea_data.copy()
        data["idea_description"] = "Detailed description"
        data["target_audience"] = "Logistics professionals"
        data["priority"] = Priority.HIGH
        data["keywords"] = ["logistics", "supply chain"]
        
        idea = ContentIdea(**data)
        
        self.assertEqual(idea.idea_description, "Detailed description")
        self.assertEqual(idea.target_audience, "Logistics professionals")
        self.assertEqual(idea.priority, Priority.HIGH)
        self.assertEqual(len(idea.keywords), 2)
    
    def test_idea_validation(self):
        """Test content idea validation."""
        # Empty title
        data = self.valid_idea_data.copy()
        data["idea_title"] = "   "
        
        with self.assertRaises(ValueError) as context:
            ContentIdea(**data)
        self.assertIn("Idea title cannot be empty", str(context.exception))
    
    def test_idea_backward_compatibility(self):
        """Test backward compatibility properties."""
        idea = ContentIdea(**self.valid_idea_data)
        
        # Test title property
        idea.title = "New Title"
        self.assertEqual(idea.idea_title, "New Title")
        self.assertEqual(idea.title, "New Title")
        
        # Test description property
        idea.description = "New Description"
        self.assertEqual(idea.idea_description, "New Description")
        self.assertEqual(idea.description, "New Description")
    
    def test_idea_to_sheet_row(self):
        """Test content idea conversion to sheet row."""
        idea = ContentIdea(**self.valid_idea_data)
        row = idea.to_sheet_row()
        
        self.assertEqual(len(row), 11)  # Number of columns
        self.assertEqual(row[1], "Test Content Idea")  # Title
        self.assertEqual(row[4], "blog")  # Content Type
        self.assertEqual(row[5], "medium")  # Priority
        self.assertEqual(row[9], "proposed")  # Status


class TestSummaryReportModel(unittest.TestCase):
    """Test SummaryReport data model."""
    
    def setUp(self):
        """Set up test data."""
        self.valid_report_data = {
            "run_date": datetime.now(),
            "total_articles_fetched": 100,
            "articles_scraped_successfully": 85,
            "ideas_generated": 10
        }
    
    def test_report_creation(self):
        """Test creating a valid summary report."""
        report = SummaryReport(**self.valid_report_data)
        
        self.assertIsNotNone(report.run_id)
        self.assertEqual(report.total_articles_fetched, 100)
        self.assertEqual(report.articles_scraped_successfully, 85)
        self.assertEqual(report.ideas_generated, 10)
        self.assertEqual(report.scraping_success_rate, 85.0)
    
    def test_report_with_statistics(self):
        """Test summary report with feed statistics."""
        data = self.valid_report_data.copy()
        data["processing_time_seconds"] = 120.5
        data["feed_statistics"] = {
            "FreightWaves": {"total": 50, "scraped": 45, "failed": 5},
            "FreightCaviar": {"total": 50, "scraped": 40, "failed": 10}
        }
        
        report = SummaryReport(**data)
        
        self.assertEqual(report.processing_time_seconds, 120.5)
        self.assertEqual(len(report.feed_statistics), 2)
        self.assertEqual(report.feed_statistics["FreightWaves"]["total"], 50)
    
    def test_report_success_rate_calculation(self):
        """Test automatic success rate calculation."""
        # Test with successful scrapes
        report = SummaryReport(**self.valid_report_data)
        self.assertEqual(report.scraping_success_rate, 85.0)
        
        # Test with no articles
        data = self.valid_report_data.copy()
        data["total_articles_fetched"] = 0
        data["articles_scraped_successfully"] = 0
        
        report = SummaryReport(**data)
        self.assertEqual(report.scraping_success_rate, 0.0)
    
    def test_report_to_sheet_row(self):
        """Test summary report conversion to sheet row."""
        report = SummaryReport(**self.valid_report_data)
        row = report.to_sheet_row()
        
        self.assertEqual(len(row), 9)  # Number of columns
        self.assertEqual(row[2], 100)  # Total articles
        self.assertEqual(row[3], 85)  # Scraped successfully
        self.assertEqual(row[4], "85.0%")  # Success rate
        self.assertEqual(row[5], 10)  # Ideas generated


class TestEnumerations(unittest.TestCase):
    """Test enumeration values."""
    
    def test_source_feed_enum(self):
        """Test SourceFeed enumeration."""
        self.assertEqual(SourceFeed.FREIGHT_WAVES.value, "FreightWaves")
        self.assertEqual(SourceFeed.FREIGHT_CAVIAR.value, "FreightCaviar")
        self.assertEqual(SourceFeed.CUSTOM.value, "Custom")
    
    def test_scraping_strategy_enum(self):
        """Test ScrapingStrategy enumeration."""
        self.assertEqual(ScrapingStrategy.BASIC.value, "basic")
        self.assertEqual(ScrapingStrategy.ENHANCED.value, "enhanced")
        self.assertEqual(ScrapingStrategy.CLOUDSCRAPER.value, "cloudscraper")
        self.assertEqual(ScrapingStrategy.MCP_PLAYWRIGHT.value, "mcp_playwright")
        self.assertEqual(ScrapingStrategy.NONE.value, "none")
    
    def test_content_type_enum(self):
        """Test ContentType enumeration."""
        self.assertEqual(ContentType.BLOG_POST.value, "blog")
        self.assertEqual(ContentType.VIDEO.value, "video")
        self.assertEqual(ContentType.PODCAST.value, "podcast")
    
    def test_priority_enum(self):
        """Test Priority enumeration."""
        self.assertEqual(Priority.HIGH.value, "high")
        self.assertEqual(Priority.MEDIUM.value, "medium")
        self.assertEqual(Priority.LOW.value, "low")
    
    def test_content_status_enum(self):
        """Test ContentStatus enumeration."""
        self.assertEqual(ContentStatus.PROPOSED.value, "proposed")
        self.assertEqual(ContentStatus.IN_PROGRESS.value, "in_progress")
        self.assertEqual(ContentStatus.COMPLETED.value, "completed")
        self.assertEqual(ContentStatus.REJECTED.value, "rejected")


def run_tests():
    """Run all tests."""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestDataValidation))
    suite.addTests(loader.loadTestsFromTestCase(TestArticleModel))
    suite.addTests(loader.loadTestsFromTestCase(TestContentIdeaModel))
    suite.addTests(loader.loadTestsFromTestCase(TestSummaryReportModel))
    suite.addTests(loader.loadTestsFromTestCase(TestEnumerations))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.wasSuccessful():
        print("\n✓ All tests passed successfully!")
    else:
        print("\n✗ Some tests failed. Please review the output above.")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)