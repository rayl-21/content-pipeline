#!/usr/bin/env python
"""Test suite for WebScraper improvements.

This test validates that the scraper correctly handles various article formats
from FreightWaves and FreightCaviar RSS feeds.
"""

import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from content_pipeline.scrapers.scraper import WebScraper, ScrapingStrategy
from content_pipeline.core.models import Article, SourceFeed


class TestWebScraperImprovements(unittest.TestCase):
    """Test the improved WebScraper content extraction."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.scraper = WebScraper(strategy=ScrapingStrategy.ENHANCED, delay=0)
    
    def tearDown(self):
        """Clean up after tests."""
        if hasattr(self, 'scraper'):
            self.scraper.close()
    
    def test_content_selectors_include_freightcaviar_patterns(self):
        """Test that content selectors include FreightCaviar-specific patterns."""
        selectors = self.scraper.CONTENT_SELECTORS
        
        # Check for FreightCaviar-specific selectors
        self.assertIn('article.post', selectors)
        self.assertIn('main article.post', selectors)
        
        # Check for FreightWaves selectors
        self.assertIn('#entry-content', selectors)
        self.assertIn('.entry-content', selectors)
    
    def test_extract_content_with_freightwaves_html(self):
        """Test content extraction with FreightWaves HTML structure."""
        html = """
        <html>
        <body>
            <div id="entry-content">
                <p>This is the main article content from FreightWaves.</p>
                <p>It contains multiple paragraphs of logistics news.</p>
                <p>The scraper should extract all of this text.</p>
            </div>
        </body>
        </html>
        """
        
        content = self.scraper._extract_content(html)
        
        self.assertIn("main article content", content)
        self.assertIn("multiple paragraphs", content)
        self.assertIn("extract all of this", content)
    
    def test_extract_content_with_freightcaviar_html(self):
        """Test content extraction with FreightCaviar HTML structure."""
        html = """
        <html>
        <body>
            <main>
                <article class="post featured content">
                    <p>FreightCaviar newsletter content about trucking industry.</p>
                    <p>Analysis of freight market conditions.</p>
                    <p>Commentary on supply chain disruptions.</p>
                </article>
            </main>
        </body>
        </html>
        """
        
        content = self.scraper._extract_content(html)
        
        self.assertIn("FreightCaviar newsletter", content)
        self.assertIn("freight market", content)
        self.assertIn("supply chain", content)
    
    def test_detect_landing_page(self):
        """Test that landing pages with multiple article cards are detected."""
        html = """
        <html>
        <body>
            <div class="post-card">Article 1 preview</div>
            <div class="post-card">Article 2 preview</div>
            <div class="post-card">Article 3 preview</div>
            <div class="post-card">Article 4 preview</div>
        </body>
        </html>
        """
        
        content = self.scraper._extract_content(html)
        
        # Landing pages should return empty content
        self.assertEqual(content, "")
    
    def test_detect_paywall(self):
        """Test detection of paywalled content."""
        html = """
        <html>
        <body>
            <iframe class="omedagate"></iframe>
            <div class="premium-content">
                <p>This content requires a subscription.</p>
            </div>
        </body>
        </html>
        """
        
        with patch('content_pipeline.scrapers.scraper.logger') as mock_logger:
            content = self.scraper._extract_content(html)
            
            # Check that paywall was detected and logged
            mock_logger.debug.assert_any_call("Paywall/gated content detected: iframe.omedagate")
    
    def test_fallback_to_paragraphs(self):
        """Test fallback to paragraph extraction when selectors don't match."""
        html = """
        <html>
        <body>
            <div class="custom-content">
                <p>This is a paragraph with more than 30 characters of content.</p>
                <p>Another substantial paragraph with important information.</p>
                <p>Short</p>
                <p>Final paragraph with enough content to be included.</p>
            </div>
        </body>
        </html>
        """
        
        content = self.scraper._extract_content(html)
        
        # Should extract valid paragraphs (> 30 chars)
        self.assertIn("more than 30 characters", content)
        self.assertIn("substantial paragraph", content)
        self.assertIn("Final paragraph", content)
        # Short paragraph should be filtered out
        self.assertNotIn("Short", content)
    
    def test_clean_text_removes_excessive_whitespace(self):
        """Test that _clean_text properly normalizes whitespace."""
        text = """
        
        This    has     excessive     spaces.
        
        
        And multiple empty lines.
        
        """
        
        cleaned = self.scraper._clean_text(text)
        
        lines = cleaned.split('\n')
        self.assertEqual(len(lines), 2)
        self.assertEqual(lines[0], "This has excessive spaces.")
        self.assertEqual(lines[1], "And multiple empty lines.")
    
    @patch('requests.Session.get')
    def test_scrape_article_updates_stats(self, mock_get):
        """Test that scraping updates statistics correctly."""
        # Mock successful response
        mock_response = MagicMock()
        mock_response.text = """
        <div id="entry-content">
            <p>Test article content with sufficient length to pass the threshold check.</p>
            <p>More content to ensure we have over 100 characters total.</p>
        </div>
        """
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        article = Article(
            title="Test Article",
            url="https://example.com/article",
            published_date=datetime.now(timezone.utc),
            source_feed=SourceFeed.FREIGHT_WAVES
        )
        
        result = self.scraper.scrape_article(article)
        
        # Check that content was extracted
        self.assertIsNotNone(result.content)
        self.assertIn("Test article content", result.content)
        
        # Check statistics
        stats = self.scraper.get_stats()
        self.assertEqual(stats['total'], 1)
        self.assertEqual(stats['success'], 1)
        self.assertEqual(stats['failed'], 0)
    
    def test_enhanced_content_selectors_order(self):
        """Test that selectors are tried in the correct order (most specific first)."""
        selectors = self.scraper.CONTENT_SELECTORS
        
        # Ensure ID selectors come before class selectors
        id_index = selectors.index('#entry-content')
        class_index = selectors.index('.entry-content')
        self.assertLess(id_index, class_index)
        
        # Ensure specific selectors come before generic ones
        specific_index = selectors.index('main article.post')
        generic_index = selectors.index('article')
        self.assertLess(specific_index, generic_index)


if __name__ == '__main__':
    unittest.main()