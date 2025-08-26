#!/usr/bin/env python3
"""
Migration script to update Google Sheets schema to include new fields.
Adds extraction_confidence and failure_reason columns to existing Articles sheet.
Preserves all existing data while migrating to the new schema.
"""

import sys
import time
from pathlib import Path
from typing import List, Dict, Any

# Add parent directory to path to import our modules
sys.path.append(str(Path(__file__).parent.parent))

from src.content_pipeline.config import PipelineConfig
from src.content_pipeline.sheets.google_sheets import GoogleSheetsManager
from src.content_pipeline.core.models import Article


class SheetsMigration:
    """Handles migration of Google Sheets to new schema."""
    
    def __init__(self):
        """Initialize migration with Google Sheets connection."""
        config = PipelineConfig()
        self.sheets_manager = GoogleSheetsManager(
            credentials_path=config.credentials_path,
            spreadsheet_id=config.spreadsheet_id
        )
        self.backup_data = {}
    
    def backup_sheet(self, sheet_name: str) -> bool:
        """
        Create an in-memory backup of sheet data.
        
        Args:
            sheet_name: Name of the sheet to backup
            
        Returns:
            True if backup successful, False otherwise
        """
        try:
            worksheet = self.sheets_manager.spreadsheet.worksheet(sheet_name)
            all_data = worksheet.get_all_values()
            
            if all_data:
                self.backup_data[sheet_name] = {
                    'headers': all_data[0] if len(all_data) > 0 else [],
                    'rows': all_data[1:] if len(all_data) > 1 else [],
                    'row_count': len(all_data) - 1
                }
                print(f"  ✓ Backed up {len(all_data) - 1} rows from {sheet_name}")
                return True
            else:
                print(f"  ⚠️  No data to backup in {sheet_name}")
                return True
                
        except Exception as e:
            print(f"  ✗ Error backing up {sheet_name}: {e}")
            return False
    
    def migrate_articles_sheet(self) -> bool:
        """
        Migrate Articles sheet to new schema with extraction_confidence and failure_reason.
        
        Returns:
            True if migration successful, False otherwise
        """
        sheet_name = "Articles"
        
        try:
            # Get worksheet
            worksheet = self.sheets_manager.spreadsheet.worksheet(sheet_name)
            
            # Get current headers
            current_headers = worksheet.row_values(1)
            expected_headers = Article.sheet_headers()
            
            # Check if migration is needed
            if current_headers == expected_headers:
                print(f"  ✓ {sheet_name} sheet already has the correct schema")
                return True
            
            # Identify what needs to be migrated
            missing_columns = set(expected_headers) - set(current_headers)
            
            if missing_columns != {"Extraction Confidence", "Failure Reason"}:
                print(f"  ⚠️  Unexpected schema difference. Missing columns: {missing_columns}")
                response = input("  Continue with migration? (y/n): ")
                if response.lower() != 'y':
                    print("  Migration cancelled")
                    return False
            
            # Backup current data
            print(f"\n📦 Backing up {sheet_name} sheet...")
            if not self.backup_sheet(sheet_name):
                print("  ✗ Backup failed, aborting migration")
                return False
            
            backup = self.backup_data[sheet_name]
            
            # Prepare migrated data
            print(f"\n🔄 Migrating {sheet_name} sheet...")
            
            # Create new rows with migrated data
            migrated_rows = []
            
            # Add new headers
            migrated_rows.append(expected_headers)
            
            # Find indices for insertion
            # New columns go after "Word Count" and before "Keywords"
            word_count_idx = current_headers.index("Word Count") if "Word Count" in current_headers else 12
            
            # Process each data row
            for row in backup['rows']:
                # Ensure row has enough columns
                while len(row) < len(current_headers):
                    row.append("")
                
                # Insert new columns with default values
                new_row = row[:word_count_idx + 1]  # Everything up to and including Word Count
                new_row.append("0.00")  # Extraction Confidence default
                new_row.append("")  # Failure Reason default
                new_row.extend(row[word_count_idx + 1:])  # Keywords, Categories
                
                # Ensure row has correct number of columns
                while len(new_row) < len(expected_headers):
                    new_row.append("")
                
                migrated_rows.append(new_row[:len(expected_headers)])  # Trim if too long
            
            # Clear sheet and write migrated data
            print(f"  📝 Writing migrated data...")
            worksheet.clear()
            
            # Write all rows at once for efficiency
            if migrated_rows:
                update_range = f"A1:{chr(64 + len(expected_headers))}{len(migrated_rows)}"
                worksheet.update(update_range, migrated_rows, value_input_option='USER_ENTERED')
                
                # Format headers
                worksheet.format('1:1', {
                    'backgroundColor': {'red': 0.8, 'green': 0.8, 'blue': 0.8},
                    'textFormat': {'bold': True}
                })
                
                print(f"  ✓ Migrated {len(migrated_rows) - 1} rows successfully")
            
            # Auto-resize columns
            try:
                worksheet.columns_auto_resize(0, len(expected_headers) - 1)
            except:
                pass  # Auto-resize might not be available
            
            return True
            
        except Exception as e:
            print(f"  ✗ Error migrating {sheet_name}: {e}")
            print(f"\n  ⚠️  Migration failed. Data backup is available in memory.")
            print(f"     Consider running the purge script and re-importing data if needed.")
            return False
    
    def verify_migration(self) -> bool:
        """
        Verify that migration was successful.
        
        Returns:
            True if verification passes, False otherwise
        """
        print("\n🔍 Verifying migration...")
        
        try:
            worksheet = self.sheets_manager.spreadsheet.worksheet("Articles")
            current_headers = worksheet.row_values(1)
            expected_headers = Article.sheet_headers()
            
            if current_headers == expected_headers:
                print(f"  ✓ Headers match expected schema")
                
                # Check row count matches
                all_values = worksheet.get_all_values()
                current_rows = len(all_values) - 1
                original_rows = self.backup_data.get("Articles", {}).get("row_count", 0)
                
                if current_rows == original_rows:
                    print(f"  ✓ Row count preserved: {current_rows} rows")
                else:
                    print(f"  ⚠️  Row count mismatch: {original_rows} → {current_rows}")
                
                # Sample a few rows to verify data integrity
                if current_rows > 0:
                    sample_row = worksheet.row_values(2)  # First data row
                    if len(sample_row) >= len(expected_headers):
                        print(f"  ✓ Data structure looks correct")
                        
                        # Check new columns have default values
                        extraction_conf_idx = expected_headers.index("Extraction Confidence")
                        failure_reason_idx = expected_headers.index("Failure Reason")
                        
                        if sample_row[extraction_conf_idx] == "0.00":
                            print(f"  ✓ Extraction Confidence initialized correctly")
                        if sample_row[failure_reason_idx] == "":
                            print(f"  ✓ Failure Reason initialized correctly")
                    else:
                        print(f"  ⚠️  Row has fewer columns than expected")
                
                return True
            else:
                print(f"  ✗ Headers don't match expected schema")
                return False
                
        except Exception as e:
            print(f"  ✗ Error verifying migration: {e}")
            return False
    
    def run(self) -> bool:
        """
        Run the complete migration process.
        
        Returns:
            True if migration successful, False otherwise
        """
        print("=" * 60)
        print("GOOGLE SHEETS SCHEMA MIGRATION")
        print("=" * 60)
        print("\nThis script will migrate your Google Sheets to include:")
        print("  • extraction_confidence field (confidence score 0.0-1.0)")
        print("  • failure_reason field (detailed error messages)")
        print("\n⚠️  IMPORTANT: This will modify your production Google Sheets!")
        
        # Test connection
        print("\n🔌 Testing connection...")
        if not self.sheets_manager.test_connection():
            print("✗ Failed to connect to Google Sheets")
            return False
        
        print("✓ Connected successfully")
        print(f"  Sheet URL: {self.sheets_manager.spreadsheet.url}")
        
        # Confirm before proceeding
        response = input("\n⚠️  Proceed with migration? (yes/no): ")
        if response.lower() not in ['yes', 'y']:
            print("Migration cancelled")
            return False
        
        # Run migration
        if self.migrate_articles_sheet():
            # Verify migration
            if self.verify_migration():
                print("\n" + "=" * 60)
                print("✓ MIGRATION COMPLETED SUCCESSFULLY")
                print("=" * 60)
                print("\nNext steps:")
                print("  1. Run a test with a small batch of articles")
                print("  2. Verify data is being saved correctly")
                print("  3. Monitor for any issues")
                return True
            else:
                print("\n⚠️  Migration verification failed")
                print("Please check the Google Sheets manually")
                return False
        else:
            print("\n✗ Migration failed")
            return False


def main():
    """Main entry point for migration script."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Migrate Google Sheets schema to include new fields")
    parser.add_argument("--auto-confirm", action="store_true", 
                       help="Skip confirmation prompts (use with caution)")
    parser.add_argument("--dry-run", action="store_true",
                       help="Preview migration without making changes")
    args = parser.parse_args()
    
    migration = SheetsMigration()
    
    # Override the run method for auto-confirm
    if args.auto_confirm:
        original_run = migration.run
        
        def auto_run():
            print("=" * 60)
            print("GOOGLE SHEETS SCHEMA MIGRATION")
            print("=" * 60)
            print("\nThis script will migrate your Google Sheets to include:")
            print("  • extraction_confidence field (confidence score 0.0-1.0)")
            print("  • failure_reason field (detailed error messages)")
            
            if args.dry_run:
                print("\n🔍 DRY RUN MODE - No changes will be made")
            
            print("\n🔌 Testing connection...")
            if not migration.sheets_manager.test_connection():
                print("✗ Failed to connect to Google Sheets")
                return False
            
            print("✓ Connected successfully")
            print(f"  Sheet URL: {migration.sheets_manager.spreadsheet.url}")
            
            if args.dry_run:
                print("\n📋 Would migrate Articles sheet:")
                worksheet = migration.sheets_manager.spreadsheet.worksheet("Articles")
                current_headers = worksheet.row_values(1)
                expected_headers = Article.sheet_headers()
                
                if current_headers == expected_headers:
                    print("  ✓ Sheet already has correct schema - no migration needed")
                else:
                    missing = set(expected_headers) - set(current_headers)
                    print(f"  Would add columns: {list(missing)}")
                    print(f"  Would preserve {len(worksheet.get_all_values()) - 1} existing rows")
                return True
            
            print("\n⚠️  Auto-confirm mode - proceeding with migration...")
            
            if migration.migrate_articles_sheet():
                if migration.verify_migration():
                    print("\n" + "=" * 60)
                    print("✓ MIGRATION COMPLETED SUCCESSFULLY")
                    print("=" * 60)
                    return True
                else:
                    print("\n⚠️  Migration verification failed")
                    return False
            else:
                print("\n✗ Migration failed")
                return False
        
        migration.run = auto_run
    
    success = migration.run()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()