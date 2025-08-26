#!/usr/bin/env python3
"""
Test script to verify article saving works with the new schema.
Creates a test article with extraction_confidence and failure_reason fields.
"""

import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path to import our modules
sys.path.append(str(Path(__file__).parent.parent))

from src.content_pipeline.config import PipelineConfig
from src.content_pipeline.sheets.google_sheets import GoogleSheetsManager
from src.content_pipeline.core.models import Article, SourceFeed, ScrapingStrategy


def test_article_saving():
    """Test saving an article with the new fields."""
    config = PipelineConfig()
    sheets_manager = GoogleSheetsManager(
        credentials_path=config.credentials_path,
        spreadsheet_id=config.spreadsheet_id
    )
    
    print("=" * 60)
    print("TESTING ARTICLE SAVING WITH NEW SCHEMA")
    print("=" * 60)
    
    # Test connection
    if not sheets_manager.test_connection():
        print("✗ Failed to connect to Google Sheets")
        return False
    
    print("✓ Connected successfully\n")
    
    # Create a test article with new fields populated
    test_article = Article(
        url="https://example.com/test-migration-article",
        title="Test Migration Article - Verify New Schema",
        description="This is a test article to verify the new extraction_confidence and failure_reason fields work correctly",
        content="This is the full content of the test article. It includes detailed information about testing the new schema migration.",
        author="Migration Test Bot",
        published_date=datetime.now(),
        source_feed=SourceFeed.FREIGHT_WAVES,
        scraping_strategy=ScrapingStrategy.RSS_FALLBACK,
        scraping_success=False,
        extraction_confidence=0.85,  # New field
        failure_reason="Content extraction partially failed - using RSS fallback",  # New field
        keywords=["test", "migration", "schema"],
        categories=["Testing", "Development"]
    )
    
    print("📝 Test Article Details:")
    print(f"  URL: {test_article.url}")
    print(f"  Title: {test_article.title}")
    print(f"  Strategy: {test_article.scraping_strategy.value}")
    print(f"  Extraction Confidence: {test_article.extraction_confidence}")
    print(f"  Failure Reason: {test_article.failure_reason}")
    print()
    
    # Save the test article
    print("💾 Saving test article to Google Sheets...")
    success = sheets_manager.save_articles([test_article], upsert=True)
    
    if success:
        print("✓ Article saved successfully!")
        
        # Verify the article was saved correctly
        print("\n🔍 Verifying saved data...")
        try:
            worksheet = sheets_manager.spreadsheet.worksheet("Articles")
            all_values = worksheet.get_all_values()
            
            # Find our test article (search from the end as it should be recent)
            for row in reversed(all_values[1:]):  # Skip header
                if len(row) > 1 and row[1] == test_article.url:
                    print("✓ Found test article in sheets!")
                    
                    # Check the new fields
                    headers = all_values[0]
                    extraction_conf_idx = headers.index("Extraction Confidence")
                    failure_reason_idx = headers.index("Failure Reason")
                    
                    saved_confidence = row[extraction_conf_idx] if extraction_conf_idx < len(row) else ""
                    saved_reason = row[failure_reason_idx] if failure_reason_idx < len(row) else ""
                    
                    print(f"  Saved Extraction Confidence: {saved_confidence}")
                    print(f"  Saved Failure Reason: {saved_reason}")
                    
                    # Validate values
                    if saved_confidence == "0.85":
                        print("  ✓ Extraction confidence saved correctly")
                    else:
                        print(f"  ⚠️  Extraction confidence mismatch: expected '0.85', got '{saved_confidence}'")
                    
                    if saved_reason == test_article.failure_reason:
                        print("  ✓ Failure reason saved correctly")
                    else:
                        print(f"  ⚠️  Failure reason mismatch")
                    
                    break
            else:
                print("⚠️  Test article not found in sheets")
                
        except Exception as e:
            print(f"✗ Error verifying saved data: {e}")
    else:
        print("✗ Failed to save article")
        return False
    
    print("\n" + "=" * 60)
    print("✓ TEST COMPLETED")
    print("=" * 60)
    
    # Test updating the same article
    print("\n📝 Testing UPSERT functionality...")
    test_article.extraction_confidence = 0.95
    test_article.failure_reason = "Updated: Full content extracted successfully"
    test_article.content += " This content was updated."
    
    success = sheets_manager.save_articles([test_article], upsert=True)
    
    if success:
        print("✓ Article updated successfully!")
        
        # Verify update
        worksheet = sheets_manager.spreadsheet.worksheet("Articles")
        all_values = worksheet.get_all_values()
        headers = all_values[0]
        
        for row in reversed(all_values[1:]):
            if len(row) > 1 and row[1] == test_article.url:
                extraction_conf_idx = headers.index("Extraction Confidence")
                failure_reason_idx = headers.index("Failure Reason")
                
                saved_confidence = row[extraction_conf_idx] if extraction_conf_idx < len(row) else ""
                saved_reason = row[failure_reason_idx] if failure_reason_idx < len(row) else ""
                
                if saved_confidence == "0.95":
                    print("✓ Updated extraction confidence correctly")
                if "Updated:" in saved_reason:
                    print("✓ Updated failure reason correctly")
                break
    
    return True


if __name__ == "__main__":
    test_article_saving()