#!/usr/bin/env python3
"""
Quick script to verify the Google Sheets schema is standardized correctly.
"""

import sys
from pathlib import Path

# Add parent directory to path to import our modules
sys.path.append(str(Path(__file__).parent.parent))

from src.content_pipeline.config import PipelineConfig
from src.content_pipeline.sheets.google_sheets import GoogleSheetsManager


def verify_schema():
    """Verify that the Google Sheets have the correct standardized schema."""
    config = PipelineConfig()
    sheets_manager = GoogleSheetsManager(
        credentials_path=config.credentials_path,
        spreadsheet_id=config.spreadsheet_id
    )
    
    print("=" * 60)
    print("GOOGLE SHEETS SCHEMA VERIFICATION")
    print("=" * 60)
    
    # Test connection
    if not sheets_manager.test_connection():
        print("✗ Failed to connect to Google Sheets")
        return False
    
    print("✓ Connected successfully\n")
    
    # Import Article model to get the current schema
    from src.content_pipeline.core.models import Article
    
    # Check Articles sheet
    print("📋 Articles Sheet:")
    try:
        worksheet = sheets_manager.spreadsheet.worksheet("Articles")
        headers = worksheet.row_values(1)
        data_rows = len(worksheet.get_all_values()) - 1  # Subtract header row
        
        # Get expected headers from the Article model
        expected_headers = Article.sheet_headers()
        
        if headers == expected_headers:
            print(f"  ✓ Headers match standardized schema ({len(headers)} columns)")
        else:
            print(f"  ⚠️  Headers mismatch detected!")
            print(f"  Expected {len(expected_headers)} columns: {expected_headers}")
            print(f"  Found {len(headers)} columns: {headers}")
            
            # Identify missing and extra columns
            missing = set(expected_headers) - set(headers)
            extra = set(headers) - set(expected_headers)
            
            if missing:
                print(f"  Missing columns: {list(missing)}")
            if extra:
                print(f"  Extra columns: {list(extra)}")
            
            # Check if it's just missing the new fields
            if missing == {"Extraction Confidence", "Failure Reason"}:
                print("\n  ℹ️  The sheet is missing the new extraction_confidence and failure_reason fields.")
                print("     Run the migration script to update the schema.")
        
        print(f"  📊 Data rows: {data_rows}")
        
    except Exception as e:
        print(f"  ✗ Error: {e}")
    
    # Check Content Ideas sheet
    print("\n📋 Content Ideas Sheet:")
    try:
        worksheet = sheets_manager.spreadsheet.worksheet("Content Ideas")
        headers = worksheet.row_values(1)
        data_rows = len(worksheet.get_all_values()) - 1
        
        expected_headers = [
            "ID", "Idea Title", "Idea Description", "Target Audience",
            "Content Type", "Priority", "Keywords", "Source Articles",
            "Created At", "Status", "Themes"
        ]
        
        if headers == expected_headers:
            print(f"  ✓ Headers match standardized schema ({len(headers)} columns)")
        else:
            print(f"  ✗ Headers don't match. Expected: {expected_headers}")
            print(f"    Got: {headers}")
        
        print(f"  📊 Data rows: {data_rows}")
        
    except Exception as e:
        print(f"  ✗ Error: {e}")
    
    # Check Summary Report sheet
    print("\n📋 Summary Report Sheet:")
    try:
        worksheet = sheets_manager.spreadsheet.worksheet("Summary Report")
        headers = worksheet.row_values(1)
        data_rows = len(worksheet.get_all_values()) - 1
        
        expected_headers = [
            "Run ID", "Run Date", "Total Articles Fetched",
            "Articles Scraped Successfully", "Scraping Success Rate",
            "Ideas Generated", "Processing Time (seconds)",
            "Errors", "Feed Statistics"
        ]
        
        if headers == expected_headers:
            print(f"  ✓ Headers match standardized schema ({len(headers)} columns)")
        else:
            print(f"  ✗ Headers don't match. Expected: {expected_headers}")
            print(f"    Got: {headers}")
        
        print(f"  📊 Data rows: {data_rows}")
        
        # Show latest run if available
        if data_rows > 0:
            latest_row = worksheet.row_values(2)  # Get first data row
            print(f"\n  📈 Latest Run:")
            print(f"     - Date: {latest_row[1] if len(latest_row) > 1 else 'N/A'}")
            print(f"     - Articles: {latest_row[2] if len(latest_row) > 2 else 'N/A'}")
            print(f"     - Success Rate: {latest_row[4] if len(latest_row) > 4 else 'N/A'}")
            print(f"     - Ideas Generated: {latest_row[5] if len(latest_row) > 5 else 'N/A'}")
        
    except Exception as e:
        print(f"  ✗ Error: {e}")
    
    print("\n" + "=" * 60)
    print("✓ SCHEMA VERIFICATION COMPLETE")
    print(f"  Sheet URL: {sheets_manager.spreadsheet.url}")
    print("=" * 60)


if __name__ == "__main__":
    verify_schema()