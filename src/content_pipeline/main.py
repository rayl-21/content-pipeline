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
from content_pipeline.config import PipelineConfig, DEFAULT_CONFIG


class ContentPipeline:
    """Main content pipeline orchestrator."""
    
    def __init__(self, config: 'PipelineConfig' = None):
        """Initialize the content pipeline with configuration."""
        if config is None:
            from .config import DEFAULT_CONFIG
            config = DEFAULT_CONFIG
        
        self.config = config
        self.credentials_path = config.credentials_path
        self.spreadsheet_id = config.spreadsheet_id
        
        # Initialize components
        self.web_scraper = WebScraper(
            delay=config.scraper_delay,
            timeout=config.scraper_timeout
        )
        self.idea_generator = IdeaGenerator()
        self.sheets_manager = GoogleSheetsManager(
            config.credentials_path, 
            config.spreadsheet_id
        )
        
        # Create RSS monitors for each feed
        self.rss_monitors = {}
        for feed in config.get_enabled_feeds():
            self.rss_monitors[feed.name] = RSSMonitor(
                feed.url, 
                timeout=config.scraper_timeout
            )
    
    def run_pipeline(self) -> bool:
        """Run the complete content pipeline for all configured feeds."""
        print("🚀 Starting Content Pipeline...")
        print(f"📋 Processing {len(self.config.get_enabled_feeds())} feeds")
        
        # Step 1: Test connections
        print("🔗 Testing connections...")
        if not self._test_connections():
            print("❌ Connection tests failed. Exiting.")
            return False
        print("✅ All connections successful")
        
        all_articles = []
        
        # Step 2: Fetch RSS articles from all feeds
        for feed in self.config.get_enabled_feeds():
            print(f"\n📡 Fetching articles from {feed.name}...")
            print(f"   URL: {feed.url}")
            print(f"   Article limit: {feed.article_limit}")
            
            monitor = self.rss_monitors[feed.name]
            articles = monitor.fetch_latest_articles(feed.article_limit)
            
            if articles:
                print(f"✅ Found {len(articles)} articles from {feed.name}")
                # Add source information to each article
                for article in articles:
                    article.source = feed.name
                all_articles.extend(articles)
            else:
                print(f"⚠️ No articles found from {feed.name}")
        
        if not all_articles:
            print("❌ No articles found from any feed. Exiting.")
            return False
        
        print(f"\n📊 Total articles collected: {len(all_articles)}")
        
        # Step 3: Scrape full content
        print("\n🕷️ Scraping full article content...")
        for i, article in enumerate(all_articles, 1):
            print(f"   [{i}/{len(all_articles)}] {article.title[:50]}... (from {article.source})")
            all_articles[i-1] = self.web_scraper.scrape_article_content(article)
        print("✅ Content scraping completed")
        
        # Step 4: Generate content ideas
        print("\n💡 Generating content ideas...")
        content_ideas = self.idea_generator.generate_ideas(all_articles)
        print(f"✅ Generated {len(content_ideas)} content ideas")
        
        # Step 5: Save to Google Sheets
        print("\n📊 Saving results to Google Sheets...")
        success = True
        
        # Save articles
        if not self.sheets_manager.save_articles(all_articles):
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
        if not self.sheets_manager.save_summary_report(all_articles, content_ideas):
            print("⚠️ Failed to save summary report")
            success = False
        else:
            print("✅ Summary report saved successfully")
        
        if success:
            print("\n🎉 Content pipeline completed successfully!")
            print(f"📊 Check your Google Sheet: https://docs.google.com/spreadsheets/d/{self.spreadsheet_id}")
            self.print_feed_summary(all_articles)
        else:
            print("\n⚠️ Pipeline completed with some errors")
        
        return success
    
    def _test_connections(self) -> bool:
        """Test all external connections."""
        # Test RSS feeds
        for feed in self.config.get_enabled_feeds():
            monitor = self.rss_monitors[feed.name]
            if not monitor.is_feed_accessible():
                print(f"❌ RSS feed '{feed.name}' is not accessible: {feed.url}")
                return False
            print(f"✅ RSS feed '{feed.name}' is accessible")
        
        # Test Google Sheets
        if not self.sheets_manager.test_connection():
            print("❌ Google Sheets connection failed")
            return False
        
        return True
    
    def print_feed_summary(self, articles: List['Article']):
        """Print summary of articles by feed source."""
        print("\n" + "="*60)
        print("CONTENT PIPELINE SUMMARY BY FEED")
        print("="*60)
        
        # Group articles by source
        articles_by_source = {}
        for article in articles:
            source = getattr(article, 'source', 'Unknown')
            if source not in articles_by_source:
                articles_by_source[source] = []
            articles_by_source[source].append(article)
        
        # Print summary for each source
        for source, source_articles in articles_by_source.items():
            print(f"\n📰 {source} ({len(source_articles)} articles):")
            for i, article in enumerate(source_articles[:3], 1):
                print(f"  {i}. {article.title[:60]}...")
        
        print("\n" + "="*60)
    
    def print_summary(self, articles: List['Article'], ideas: List['ContentIdea']):
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
    """Main entry point with configurable options."""
    import argparse
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Run the content pipeline')
    parser.add_argument(
        '--freightwaves-limit', 
        type=int, 
        default=5,
        help='Number of articles to fetch from FreightWaves (default: 5)'
    )
    parser.add_argument(
        '--freightcaviar-limit', 
        type=int, 
        default=5,
        help='Number of articles to fetch from FreightCaviar (default: 5)'
    )
    parser.add_argument(
        '--disable-freightwaves',
        action='store_true',
        help='Disable FreightWaves feed'
    )
    parser.add_argument(
        '--disable-freightcaviar',
        action='store_true',
        help='Disable FreightCaviar feed'
    )
    
    args = parser.parse_args()
    
    # Check if credentials file exists
    credentials_path = "content-pipeline-bot-key.json"
    if not os.path.exists(credentials_path):
        print(f"❌ Credentials file not found: {credentials_path}")
        print("Please make sure the Google service account key file is in the current directory.")
        sys.exit(1)
    
    # Create configuration based on command line arguments
    from content_pipeline.config import FeedConfig, PipelineConfig
    
    feeds = []
    
    if not args.disable_freightwaves:
        feeds.append(FeedConfig(
            name="FreightWaves",
            url="https://www.freightwaves.com/feed",
            article_limit=args.freightwaves_limit,
            enabled=True
        ))
    
    if not args.disable_freightcaviar:
        feeds.append(FeedConfig(
            name="FreightCaviar",
            url="https://www.freightcaviar.com/latest/rss",
            article_limit=args.freightcaviar_limit,
            enabled=True
        ))
    
    if not feeds:
        print("❌ All feeds are disabled. Please enable at least one feed.")
        sys.exit(1)
    
    config = PipelineConfig(
        feeds=feeds,
        credentials_path=credentials_path
    )
    
    print(f"🔧 Configuration:")
    for feed in config.get_enabled_feeds():
        print(f"   • {feed.name}: {feed.article_limit} articles")
    print()
    
    # Create and run the pipeline
    pipeline = ContentPipeline(config)
    success = pipeline.run_pipeline()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()