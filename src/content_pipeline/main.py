"""Main application orchestrator for the content pipeline."""

import os
import sys
import logging
from pathlib import Path
from typing import List, Optional, Dict, Callable

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from content_pipeline.scrapers.rss_monitor import RSSMonitor
from content_pipeline.scrapers.scraper import create_scraper
from content_pipeline.brainstorm.idea_generator import IdeaGenerator
from content_pipeline.sheets.google_sheets import GoogleSheetsManager
from content_pipeline.core.models import Article
from content_pipeline.config import PipelineConfig, FeedConfig, DEFAULT_CONFIG

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ContentPipeline:
    """Main content pipeline orchestrator with configurable scraping strategies."""
    
    def __init__(self, 
                 config: Optional[PipelineConfig] = None,
                 scraping_strategy: str = "enhanced",
                 mcp_functions: Optional[Dict[str, Callable]] = None):
        """Initialize the content pipeline with configuration.
        
        Args:
            config: Pipeline configuration
            scraping_strategy: Scraping strategy ('basic', 'enhanced', 'cloudscraper', 'mcp_playwright')
            mcp_functions: Optional MCP functions for Playwright strategy
        """
        self.config = config or DEFAULT_CONFIG
        self.credentials_path = self.config.credentials_path
        self.spreadsheet_id = self.config.spreadsheet_id
        self.scraping_strategy = scraping_strategy
        
        # Initialize components
        self.web_scraper = create_scraper(
            strategy=scraping_strategy,
            delay=self.config.scraper_delay,
            timeout=self.config.scraper_timeout,
            mcp_functions=mcp_functions
        )
        
        self.idea_generator = IdeaGenerator()
        self.sheets_manager = GoogleSheetsManager(
            self.config.credentials_path, 
            self.config.spreadsheet_id
        )
        
        # Create RSS monitors for each feed
        self.rss_monitors = {}
        for feed in self.config.get_enabled_feeds():
            self.rss_monitors[feed.name] = RSSMonitor(
                feed.url, 
                timeout=self.config.scraper_timeout
            )
        
        logger.info(f"ContentPipeline initialized with {scraping_strategy} strategy")
    
    def run_pipeline(self) -> bool:
        """Run the complete content pipeline for all configured feeds."""
        print("🚀 Starting Content Pipeline...")
        print(f"📋 Processing {len(self.config.get_enabled_feeds())} feeds")
        print(f"🔧 Scraping strategy: {self.scraping_strategy}")
        
        # Step 1: Test connections
        print("\n🔗 Testing connections...")
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
        print(f"\n🕷️ Scraping full article content using {self.scraping_strategy} strategy...")
        scraped_articles = self.web_scraper.scrape_articles(all_articles)
        print("✅ Content scraping completed")
        
        # Log enhanced scraping statistics
        stats = self.web_scraper.get_stats()
        success_rate = (stats['success'] / stats['total'] * 100) if stats['total'] > 0 else 0
        avg_confidence = stats.get('total_confidence', 0) / max(stats.get('success', 1), 1)
        
        print(f"\n📊 Scraping Statistics:")
        print(f"   Total: {stats['total']} articles")
        print(f"   Success: {stats['success']} ({success_rate:.1f}%)")
        print(f"   Failed: {stats.get('failed', 0)}")
        print(f"   RSS Fallbacks: {stats.get('rss_fallback', 0)}")
        print(f"   Average Confidence: {avg_confidence:.2f}")
        
        # Show confidence breakdown
        if stats.get('high_confidence', 0) or stats.get('medium_confidence', 0) or stats.get('low_confidence', 0):
            print(f"   Confidence Breakdown:")
            print(f"      High (≥0.7): {stats.get('high_confidence', 0)}")
            print(f"      Medium (0.4-0.7): {stats.get('medium_confidence', 0)}")
            print(f"      Low (<0.4): {stats.get('low_confidence', 0)}")
        
        # Show failure reasons if any
        if stats.get('failure_reasons'):
            print(f"   Failure Reasons:")
            for reason, count in stats['failure_reasons'].items():
                print(f"      {reason}: {count}")
        
        # Step 4: Generate content ideas
        print("\n💡 Generating content ideas...")
        content_ideas = self.idea_generator.generate_ideas(scraped_articles)
        print(f"✅ Generated {len(content_ideas)} content ideas")
        
        # Step 5: Save to Google Sheets
        print("\n📊 Saving results to Google Sheets...")
        success = True
        
        # Save articles
        if not self.sheets_manager.save_articles(scraped_articles):
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
        if not self.sheets_manager.save_summary_report(scraped_articles, content_ideas):
            print("⚠️ Failed to save summary report")
            success = False
        else:
            print("✅ Summary report saved successfully")
        
        if success:
            print("\n🎉 Content pipeline completed successfully!")
            print(f"📊 Check your Google Sheet: https://docs.google.com/spreadsheets/d/{self.spreadsheet_id}")
            self.print_feed_summary(scraped_articles)
        else:
            print("\n⚠️ Pipeline completed with some errors")
        
        # Clean up
        self.web_scraper.close()
        
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
    
    def print_feed_summary(self, articles: List[Article]):
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
                title = article.title[:60] if article.title else "No title"
                print(f"  {i}. {title}...")
        
        print("\n" + "="*60)


def main():
    """Main entry point with configurable options."""
    import argparse
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Run the content pipeline')
    
    # Feed configuration
    parser.add_argument(
        '--freightwaves-limit', 
        type=int, 
        default=None,
        help='Number of articles to fetch from FreightWaves (default: 5 if enabled)'
    )
    parser.add_argument(
        '--freightcaviar-limit', 
        type=int, 
        default=None,
        help='Number of articles to fetch from FreightCaviar (default: 5 if enabled)'
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
    parser.add_argument(
        '--only',
        choices=['freightwaves', 'freightcaviar'],
        help='Run only the specified feed'
    )
    
    # Scraping strategy
    parser.add_argument(
        '--strategy',
        choices=['basic', 'enhanced', 'cloudscraper', 'mcp', 'mcp_playwright'],
        default='enhanced',
        help='Scraping strategy to use (default: enhanced)'
    )
    
    # Logging level
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='Logging level (default: INFO)'
    )
    
    args = parser.parse_args()
    
    # Configure logging
    logging.getLogger().setLevel(getattr(logging, args.log_level))
    
    # Check if credentials file exists
    credentials_path = "content-pipeline-bot-key.json"
    if not os.path.exists(credentials_path):
        print(f"❌ Credentials file not found: {credentials_path}")
        print("Please make sure the Google service account key file is in the current directory.")
        sys.exit(1)
    
    # Create configuration based on command line arguments
    feeds = []
    
    # Handle --only flag
    if args.only:
        if args.only == 'freightwaves':
            args.disable_freightcaviar = True
        elif args.only == 'freightcaviar':
            args.disable_freightwaves = True
    
    # Configure feeds
    if not args.disable_freightwaves:
        feeds.append(FeedConfig(
            name="FreightWaves",
            url="https://www.freightwaves.com/feed",
            article_limit=args.freightwaves_limit if args.freightwaves_limit is not None else 5,
            enabled=True
        ))
    
    if not args.disable_freightcaviar:
        feeds.append(FeedConfig(
            name="FreightCaviar",
            url="https://www.freightcaviar.com/latest/rss",
            article_limit=args.freightcaviar_limit if args.freightcaviar_limit is not None else 5,
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
    print(f"   Scraping strategy: {args.strategy}")
    for feed in config.get_enabled_feeds():
        print(f"   • {feed.name}: {feed.article_limit} articles")
    print()
    
    # Map strategy aliases
    strategy_map = {
        'mcp': 'mcp_playwright',
    }
    strategy = strategy_map.get(args.strategy, args.strategy)
    
    # Create MCP functions dict if available (for Claude Code environment)
    mcp_functions = None
    if strategy == 'mcp_playwright':
        # Try to detect MCP functions in the environment
        try:
            # In Claude Code, these functions would be available globally
            mcp_functions = {
                'mcp__playwright__browser_navigate': globals().get('mcp__playwright__browser_navigate'),
                'mcp__playwright__browser_wait_for': globals().get('mcp__playwright__browser_wait_for'),
                'mcp__playwright__browser_snapshot': globals().get('mcp__playwright__browser_snapshot'),
            }
            # Remove None values
            mcp_functions = {k: v for k, v in mcp_functions.items() if v is not None}
            if not mcp_functions:
                print("⚠️ MCP functions not available, falling back to enhanced strategy")
                strategy = 'enhanced'
                mcp_functions = None
        except Exception as e:
            logger.debug(f"Could not detect MCP functions: {e}")
            print("⚠️ MCP functions not available, falling back to enhanced strategy")
            strategy = 'enhanced'
    
    # Create and run the pipeline
    pipeline = ContentPipeline(
        config=config,
        scraping_strategy=strategy,
        mcp_functions=mcp_functions
    )
    success = pipeline.run_pipeline()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()