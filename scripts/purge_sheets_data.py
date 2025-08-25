#!/usr/bin/env python3
"""
One-time script to purge and standardize Google Sheets data.

This script:
1. Backs up existing data to JSON files
2. Clears all sheets
3. Sets up new headers with standardized schema
4. Optionally migrates old data to new format

Usage:
    python scripts/purge_sheets_data.py [--backup-only] [--migrate]
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add parent directory to path to import our modules
sys.path.append(str(Path(__file__).parent.parent))

from src.content_pipeline.config import PipelineConfig
from src.content_pipeline.core.models import (
    Article, ContentIdea, SummaryReport,
    SourceFeed, ContentType, 
    Priority, ContentStatus
)
from src.content_pipeline.sheets.google_sheets import GoogleSheetsManager


class SheetsPurgeManager:
    """Manages the purging and migration of Google Sheets data."""
    
    def __init__(self):
        """Initialize the purge manager."""
        config = PipelineConfig()
        self.sheets_manager = GoogleSheetsManager(
            credentials_path=config.credentials_path,
            spreadsheet_id=config.spreadsheet_id
        )
        
        # Create backup directory
        self.backup_dir = Path("backups") / datetime.now().strftime("%Y%m%d_%H%M%S")
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"Initialized purge manager. Backups will be saved to: {self.backup_dir}")
    
    def backup_sheet(self, sheet_name: str) -> Optional[List[List[Any]]]:
        """Backup a single sheet to JSON file.
        
        Args:
            sheet_name: Name of the sheet to backup
            
        Returns:
            The backed up data or None if sheet doesn't exist
        """
        try:
            worksheet = self.sheets_manager.spreadsheet.worksheet(sheet_name)
            data = worksheet.get_all_values()
            
            if data:
                # Save to JSON file
                backup_file = self.backup_dir / f"{sheet_name.replace(' ', '_').lower()}.json"
                with open(backup_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                
                print(f"✓ Backed up {sheet_name}: {len(data)} rows to {backup_file}")
                return data
            else:
                print(f"  {sheet_name} is empty, skipping backup")
                return []
                
        except Exception as e:
            print(f"✗ Failed to backup {sheet_name}: {e}")
            return None
    
    def backup_all_sheets(self) -> Dict[str, List[List[Any]]]:
        """Backup all sheets to JSON files.
        
        Returns:
            Dictionary of sheet name to data
        """
        print("\n=== BACKING UP EXISTING DATA ===")
        
        backups = {}
        sheets_to_backup = ["Articles", "Content Ideas", "Summary", "Summary Report"]
        
        for sheet_name in sheets_to_backup:
            data = self.backup_sheet(sheet_name)
            if data is not None:
                backups[sheet_name] = data
        
        # Also backup any other sheets that might exist
        try:
            all_worksheets = self.sheets_manager.spreadsheet.worksheets()
            for worksheet in all_worksheets:
                if worksheet.title not in sheets_to_backup and worksheet.title not in backups:
                    data = self.backup_sheet(worksheet.title)
                    if data is not None:
                        backups[worksheet.title] = data
        except Exception as e:
            print(f"Warning: Could not enumerate all worksheets: {e}")
        
        print(f"\nBackup complete. {len(backups)} sheets backed up to {self.backup_dir}")
        return backups
    
    def clear_sheet(self, sheet_name: str) -> bool:
        """Clear all data from a sheet.
        
        Args:
            sheet_name: Name of the sheet to clear
            
        Returns:
            True if successful, False otherwise
        """
        try:
            worksheet = self.sheets_manager._get_or_create_worksheet(sheet_name)
            worksheet.clear()
            print(f"✓ Cleared {sheet_name}")
            return True
        except Exception as e:
            print(f"✗ Failed to clear {sheet_name}: {e}")
            return False
    
    def setup_standardized_headers(self):
        """Set up new standardized headers for all sheets."""
        print("\n=== SETTING UP STANDARDIZED HEADERS ===")
        
        # Articles sheet
        try:
            worksheet = self.sheets_manager._get_or_create_worksheet("Articles")
            worksheet.clear()
            headers = Article.sheet_headers()
            worksheet.append_row(headers)
            worksheet.format('1:1', {
                'backgroundColor': {'red': 0.8, 'green': 0.8, 'blue': 0.8},
                'textFormat': {'bold': True}
            })
            print(f"✓ Set up Articles headers ({len(headers)} columns)")
        except Exception as e:
            print(f"✗ Failed to set up Articles headers: {e}")
        
        # Content Ideas sheet
        try:
            worksheet = self.sheets_manager._get_or_create_worksheet("Content Ideas")
            worksheet.clear()
            headers = ContentIdea.sheet_headers()
            worksheet.append_row(headers)
            worksheet.format('1:1', {
                'backgroundColor': {'red': 0.8, 'green': 0.9, 'blue': 0.8},
                'textFormat': {'bold': True}
            })
            print(f"✓ Set up Content Ideas headers ({len(headers)} columns)")
        except Exception as e:
            print(f"✗ Failed to set up Content Ideas headers: {e}")
        
        # Summary Report sheet (new structured format)
        try:
            worksheet = self.sheets_manager._get_or_create_worksheet("Summary Report")
            worksheet.clear()
            headers = SummaryReport.sheet_headers()
            worksheet.append_row(headers)
            worksheet.format('1:1', {
                'backgroundColor': {'red': 0.2, 'green': 0.6, 'blue': 0.9},
                'textFormat': {'bold': True, 'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}}
            })
            print(f"✓ Set up Summary Report headers ({len(headers)} columns)")
        except Exception as e:
            print(f"✗ Failed to set up Summary Report headers: {e}")
        
        # Remove or rename old Summary sheet if it exists
        try:
            old_summary = self.sheets_manager.spreadsheet.worksheet("Summary")
            old_summary.update_title("Summary (Old)")
            print("✓ Renamed old Summary sheet to 'Summary (Old)'")
        except:
            pass  # Sheet doesn't exist or rename failed, that's okay
    
    def migrate_articles(self, old_data: List[List[Any]]) -> List[Article]:
        """Migrate old article data to new format.
        
        Args:
            old_data: Old article data from backup
            
        Returns:
            List of migrated Article objects
        """
        if not old_data or len(old_data) < 2:
            return []
        
        articles = []
        headers = old_data[0] if old_data else []
        
        # Map old column names to indices
        col_map = {header.lower(): i for i, header in enumerate(headers)}
        
        for row in old_data[1:]:  # Skip header row
            try:
                # Extract data with fallbacks
                url = row[col_map.get('url', 1)] if len(row) > col_map.get('url', 1) else ""
                title = row[col_map.get('title', 0)] if len(row) > col_map.get('title', 0) else ""
                
                if not url or not title:
                    continue  # Skip invalid rows
                
                # Parse published date
                pub_date_str = row[col_map.get('published date', 2)] if len(row) > col_map.get('published date', 2) else ""
                try:
                    published_date = datetime.strptime(pub_date_str, "%Y-%m-%d %H:%M:%S")
                except:
                    published_date = datetime.now()  # Fallback to now
                
                # Determine source feed
                source_str = row[col_map.get('source', 8)] if len(row) > col_map.get('source', 8) else ""
                source_feed = SourceFeed.CUSTOM
                for feed in SourceFeed:
                    if feed.value.lower() == source_str.lower():
                        source_feed = feed
                        break
                
                # Create article with new standardized format
                article = Article(
                    url=url,
                    title=title,
                    published_date=published_date,
                    source_feed=source_feed,
                    description=row[col_map.get('summary', 4)] if len(row) > col_map.get('summary', 4) else "",
                    content=row[col_map.get('content', 5)] if len(row) > col_map.get('content', 5) else "",
                    author=row[col_map.get('author', 3)] if len(row) > col_map.get('author', 3) else "",
                    scraping_success=str(row[col_map.get('scraped', 7)]).lower() == "true" if len(row) > col_map.get('scraped', 7) else False,
                    categories=[c.strip() for c in row[col_map.get('categories', 6)].split(',') if c.strip()] if len(row) > col_map.get('categories', 6) else []
                )
                
                articles.append(article)
                
            except Exception as e:
                print(f"  Warning: Failed to migrate article row: {e}")
                continue
        
        print(f"  Migrated {len(articles)} articles")
        return articles
    
    def migrate_content_ideas(self, old_data: List[List[Any]]) -> List[ContentIdea]:
        """Migrate old content idea data to new format.
        
        Args:
            old_data: Old content idea data from backup
            
        Returns:
            List of migrated ContentIdea objects
        """
        if not old_data or len(old_data) < 2:
            return []
        
        ideas = []
        headers = old_data[0] if old_data else []
        
        # Map old column names to indices
        col_map = {header.lower(): i for i, header in enumerate(headers)}
        
        for row in old_data[1:]:  # Skip header row
            try:
                # Extract data with fallbacks
                title = row[col_map.get('title', 0)] if len(row) > col_map.get('title', 0) else ""
                content_type_str = row[col_map.get('content type', 1)] if len(row) > col_map.get('content type', 1) else "blog"
                
                if not title:
                    continue  # Skip invalid rows
                
                # Map old content type to new enum
                content_type = ContentType.BLOG_POST  # Default
                type_mapping = {
                    "blog post": ContentType.BLOG_POST,
                    "video script": ContentType.VIDEO,
                    "social media post": ContentType.SOCIAL_MEDIA,
                    "podcast": ContentType.PODCAST,
                    "infographic": ContentType.INFOGRAPHIC
                }
                for old_type, new_type in type_mapping.items():
                    if old_type in content_type_str.lower():
                        content_type = new_type
                        break
                
                # Create content idea with new standardized format
                idea = ContentIdea(
                    idea_title=title,
                    content_type=content_type,
                    keywords=[k.strip() for k in row[col_map.get('keywords', 2)].split(',') if k.strip()] if len(row) > col_map.get('keywords', 2) else [],
                    themes=[t.strip() for t in row[col_map.get('themes', 3)].split(',') if t.strip()] if len(row) > col_map.get('themes', 3) else [],
                    source_articles=row[col_map.get('source articles', 4)].split('\n') if len(row) > col_map.get('source articles', 4) else [],
                    priority=Priority.MEDIUM,  # Default priority
                    status=ContentStatus.PROPOSED  # Default status
                )
                
                ideas.append(idea)
                
            except Exception as e:
                print(f"  Warning: Failed to migrate content idea row: {e}")
                continue
        
        print(f"  Migrated {len(ideas)} content ideas")
        return ideas
    
    def write_migrated_data(self, articles: List[Article], ideas: List[ContentIdea]):
        """Write migrated data back to sheets.
        
        Args:
            articles: Migrated articles
            ideas: Migrated content ideas
        """
        print("\n=== WRITING MIGRATED DATA ===")
        
        # Write articles
        if articles:
            try:
                worksheet = self.sheets_manager.spreadsheet.worksheet("Articles")
                rows = [article.to_sheet_row() for article in articles]
                if rows:
                    worksheet.append_rows(rows, value_input_option='USER_ENTERED')
                    print(f"✓ Wrote {len(articles)} migrated articles")
            except Exception as e:
                print(f"✗ Failed to write articles: {e}")
        
        # Write content ideas
        if ideas:
            try:
                worksheet = self.sheets_manager.spreadsheet.worksheet("Content Ideas")
                rows = [idea.to_sheet_row() for idea in ideas]
                if rows:
                    worksheet.append_rows(rows, value_input_option='USER_ENTERED')
                    print(f"✓ Wrote {len(ideas)} migrated content ideas")
            except Exception as e:
                print(f"✗ Failed to write content ideas: {e}")
    
    def run(self, backup_only: bool = False, migrate: bool = False):
        """Run the purge process.
        
        Args:
            backup_only: If True, only backup data without clearing
            migrate: If True, migrate old data to new format after clearing
        """
        print("=" * 60)
        print("GOOGLE SHEETS DATA PURGE AND STANDARDIZATION")
        print("=" * 60)
        
        # Test connection first
        if not self.sheets_manager.test_connection():
            print("✗ Failed to connect to Google Sheets. Check credentials and permissions.")
            return False
        
        print("✓ Connected to Google Sheets successfully")
        
        # Step 1: Backup all data
        backups = self.backup_all_sheets()
        
        if backup_only:
            print("\n✓ Backup complete. Exiting (--backup-only mode)")
            return True
        
        # Step 2: Clear all sheets
        print("\n=== CLEARING EXISTING SHEETS ===")
        for sheet_name in ["Articles", "Content Ideas", "Summary", "Summary Report"]:
            self.clear_sheet(sheet_name)
        
        # Step 3: Set up new standardized headers
        self.setup_standardized_headers()
        
        # Step 4: Optionally migrate old data
        if migrate and backups:
            print("\n=== MIGRATING OLD DATA TO NEW FORMAT ===")
            
            # Migrate articles
            if "Articles" in backups:
                articles = self.migrate_articles(backups["Articles"])
            else:
                articles = []
            
            # Migrate content ideas
            if "Content Ideas" in backups:
                ideas = self.migrate_content_ideas(backups["Content Ideas"])
            else:
                ideas = []
            
            # Write migrated data
            if articles or ideas:
                self.write_migrated_data(articles, ideas)
            else:
                print("  No data to migrate")
        
        print("\n" + "=" * 60)
        print("✓ PURGE AND STANDARDIZATION COMPLETE")
        print(f"  Backups saved to: {self.backup_dir}")
        print(f"  Sheets URL: {self.sheets_manager.spreadsheet.url}")
        print("=" * 60)
        
        return True


def main():
    """Main entry point for the purge script."""
    parser = argparse.ArgumentParser(
        description="Purge and standardize Google Sheets data for content pipeline"
    )
    parser.add_argument(
        "--backup-only",
        action="store_true",
        help="Only backup data without clearing sheets"
    )
    parser.add_argument(
        "--migrate",
        action="store_true",
        help="Migrate old data to new format after clearing"
    )
    
    args = parser.parse_args()
    
    # Confirm destructive action
    if not args.backup_only:
        print("WARNING: This script will CLEAR ALL DATA from Google Sheets!")
        print("Backups will be created first, but this action cannot be easily undone.")
        print()
        response = input("Are you sure you want to continue? (yes/no): ")
        if response.lower() != "yes":
            print("Aborted.")
            sys.exit(0)
    
    # Run the purge
    purge_manager = SheetsPurgeManager()
    success = purge_manager.run(
        backup_only=args.backup_only,
        migrate=args.migrate
    )
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()