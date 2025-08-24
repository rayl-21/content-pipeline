"""Main application orchestrator for the content pipeline."""

import os
import sys
from pathlib import Path
from typing import List

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from content_pipeline.scrapers.rss_monitor import RSSMonitor
from content_pipeline.scrapers.web_scraper import WebScraper
from content_pipeline.brainstorm.idea_generator import IdeaGenerator
from content_pipeline.sheets.google_sheets import GoogleSheetsManager
from content_pipeline.core.models import Article, ContentIdea


class ContentPipeline:
    """Main content pipeline orchestrator."""
    
    def __init__(self, 
                 feed_url: str = "https://www.freightwaves.com/feed",
                 credentials_path: str = "content-pipeline-bot-key.json",
                 spreadsheet_id: str = "1t01HICK7cCGFK2XDebagMjjfSnN0t04t_c8o0IJh7lQ"):
        """Initialize the content pipeline."""
        self.feed_url = feed_url
        self.credentials_path = credentials_path
        self.spreadsheet_id = spreadsheet_id
        
        # Initialize components
        self.rss_monitor = RSSMonitor(feed_url)
        self.web_scraper = WebScraper()
        self.idea_generator = IdeaGenerator()
        self.sheets_manager = GoogleSheetsManager(credentials_path, spreadsheet_id)
    
    def run_pipeline(self, article_limit: int = 5) -> bool:
        """Run the complete content pipeline."""
        print("🚀 Starting Content Pipeline...")
        
        # Step 1: Test connections
        print("🔗 Testing connections...")
        if not self._test_connections():
            print("❌ Connection tests failed. Exiting.")
            return False
        print("✅ All connections successful")
        
        # Step 2: Fetch RSS articles
        print(f"📡 Fetching {article_limit} latest articles from RSS feed...")
        articles = self.rss_monitor.fetch_latest_articles(article_limit)
        if not articles:
            print("❌ No articles found. Exiting.")
            return False
        print(f"✅ Found {len(articles)} articles")
        
        # Step 3: Scrape full content
        print("🕷️ Scraping full article content...")
        for i, article in enumerate(articles, 1):
            print(f"   Scraping article {i}/{len(articles)}: {article.title[:50]}...")
            articles[i-1] = self.web_scraper.scrape_article_content(article)
        print("✅ Content scraping completed")
        
        # Step 4: Generate content ideas
        print("💡 Generating content ideas...")
        content_ideas = self.idea_generator.generate_ideas(articles)
        print(f"✅ Generated {len(content_ideas)} content ideas")
        
        # Step 5: Save to Google Sheets
        print("📊 Saving results to Google Sheets...")
        success = True
        
        # Save articles
        if not self.sheets_manager.save_articles(articles):
            print("⚠️ Failed to save articles")
            success = False
        else:
            print("✅ Articles saved successfully")
        
        # Save content ideas
        if not self.sheets_manager.save_content_ideas(content_ideas):
            print("⚠️ Failed to save content ideas")
            success = False
        else:
            print("✅ Content ideas saved successfully")
        
        # Save summary report
        if not self.sheets_manager.save_summary_report(articles, content_ideas):
            print("⚠️ Failed to save summary report")
            success = False
        else:
            print("✅ Summary report saved successfully")
        
        if success:
            print("🎉 Content pipeline completed successfully!")
            print(f"📊 Check your Google Sheet: https://docs.google.com/spreadsheets/d/{self.spreadsheet_id}")
        else:
            print("⚠️ Pipeline completed with some errors")
        
        return success
    
    def _test_connections(self) -> bool:
        """Test all external connections."""
        # Test RSS feed
        if not self.rss_monitor.is_feed_accessible():
            print("❌ RSS feed is not accessible")
            return False
        
        # Test Google Sheets
        if not self.sheets_manager.test_connection():
            print("❌ Google Sheets connection failed")
            return False
        
        return True
    
    def print_summary(self, articles: List[Article], ideas: List[ContentIdea]):
        """Print a summary of the pipeline results."""
        print("\n" + "="*60)
        print("CONTENT PIPELINE SUMMARY")
        print("="*60)
        
        print(f"\n📰 ARTICLES PROCESSED ({len(articles)}):")
        for i, article in enumerate(articles, 1):
            print(f"  {i}. {article.title}")
            print(f"     URL: {article.url}")
            print(f"     Published: {article.published_date.strftime('%Y-%m-%d %H:%M')}")
            print()
        
        print(f"💡 CONTENT IDEAS GENERATED ({len(ideas)}):")
        for i, idea in enumerate(ideas, 1):
            print(f"  {i}. {idea.title}")
            print(f"     Type: {idea.content_type}")
            print(f"     Keywords: {', '.join(idea.keywords[:3])}...")
            print()
        
        print("="*60)


def main():
    """Main entry point."""
    # Check if credentials file exists
    credentials_path = "content-pipeline-bot-key.json"
    if not os.path.exists(credentials_path):
        print(f"❌ Credentials file not found: {credentials_path}")
        print("Please make sure the Google service account key file is in the current directory.")
        sys.exit(1)
    
    # Create and run the pipeline
    pipeline = ContentPipeline()
    success = pipeline.run_pipeline(article_limit=5)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()