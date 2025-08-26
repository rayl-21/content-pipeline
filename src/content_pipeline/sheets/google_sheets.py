"""Google Sheets integration for saving content pipeline results with standardized schema."""

import json
import logging
import time
from datetime import datetime
from typing import List, Optional, Dict, Any

import gspread
from google.oauth2.service_account import Credentials

from ..core.models import Article, ContentIdea, SummaryReport
from .formatting import SheetFormatter

logger = logging.getLogger(__name__)


class GoogleSheetsManager:
    """Manages Google Sheets operations for the content pipeline with standardized data models."""
    
    # Maximum content length to display in sheets (for readability)
    MAX_CONTENT_DISPLAY_LENGTH = 2000
    
    def __init__(self, credentials_path: str, spreadsheet_id: str):
        """Initialize Google Sheets manager.
        
        Args:
            credentials_path: Path to service account credentials JSON file
            spreadsheet_id: ID of the target Google Spreadsheet
        """
        self.credentials_path = credentials_path
        self.spreadsheet_id = spreadsheet_id
        self.client = None
        self.spreadsheet = None
        
        # Define the required scope
        self.scope = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize the Google Sheets client."""
        try:
            credentials = Credentials.from_service_account_file(
                self.credentials_path, 
                scopes=self.scope
            )
            self.client = gspread.authorize(credentials)
            self.spreadsheet = self.client.open_by_key(self.spreadsheet_id)
        except Exception as e:
            print(f"Error initializing Google Sheets client: {e}")
            self.client = None
            self.spreadsheet = None
    
    def test_connection(self) -> bool:
        """Test connection to Google Sheets.
        
        Returns:
            True if connection is successful, False otherwise
        """
        try:
            if not self.spreadsheet:
                return False
            
            # Try to access spreadsheet title
            _ = self.spreadsheet.title
            return True
            
        except Exception as e:
            print(f"Google Sheets connection test failed: {e}")
            return False
    
    def _ensure_headers(self, worksheet, headers: List[str]) -> bool:
        """Ensure worksheet has the correct headers.
        
        Args:
            worksheet: The worksheet object
            headers: List of header strings
            
        Returns:
            True if headers were set or already correct, False on error
        """
        try:
            # Check if sheet is empty or has different headers
            try:
                existing_headers = worksheet.row_values(1)
            except:
                existing_headers = []
            
            if not existing_headers or existing_headers != headers:
                if existing_headers:
                    # Sheet has data but wrong headers - this is a problem
                    print(f"Warning: Sheet has incompatible headers. Consider running purge script.")
                    return False
                else:
                    # Empty sheet - add headers
                    worksheet.append_row(headers)
            
            return True
            
        except Exception as e:
            print(f"Error ensuring headers: {e}")
            return False
    
    def _sanitize_for_sheets(self, value: Any) -> Any:
        """Sanitize a value for Google Sheets.
        
        Args:
            value: The value to sanitize
            
        Returns:
            Sanitized value safe for Google Sheets
        """
        if value is None:
            return ""
        
        # Handle different types
        if isinstance(value, bool):
            return "Yes" if value else "No"
        elif isinstance(value, (list, tuple)):
            return ", ".join(str(v) for v in value)
        elif isinstance(value, dict):
            return json.dumps(value)
        elif isinstance(value, datetime):
            return value.strftime("%Y-%m-%d %H:%M:%S")
        else:
            # Convert to string and handle length
            str_value = str(value)
            if len(str_value) > self.MAX_CONTENT_DISPLAY_LENGTH:
                return str_value[:self.MAX_CONTENT_DISPLAY_LENGTH] + "..."
            return str_value
    
    def save_articles(self, articles: List[Article], upsert: bool = True) -> bool:
        """Save articles to Google Sheets with UPSERT logic using standardized schema.
        
        Args:
            articles: List of articles to save
            upsert: If True, updates existing articles or adds new ones. If False, overwrites all.
            
        Returns:
            True if successful, False otherwise
        """
        if not articles or not self.spreadsheet:
            return False
        
        try:
            # Get or create Articles worksheet
            worksheet = self._get_or_create_worksheet("Articles")
            
            # Ensure correct headers
            headers = Article.sheet_headers()
            if not self._ensure_headers(worksheet, headers):
                print("Warning: Headers mismatch. Consider running purge script first.")
            
            if upsert:
                # Get existing data for UPSERT logic
                try:
                    existing_data = worksheet.get_all_values()
                    if existing_data and len(existing_data) > 1:
                        existing_rows = existing_data[1:]  # Skip header
                    else:
                        existing_rows = []
                except:
                    existing_rows = []
                
                # Create lookup by URL (column index 1)
                existing_articles = {}
                row_numbers = {}
                for idx, row in enumerate(existing_rows, start=2):
                    if len(row) > 1:  # Has URL column
                        url = row[1]
                        existing_articles[url] = row
                        row_numbers[url] = idx
                
                # Process articles
                updates = []  # Batch updates
                new_rows = []  # New articles
                
                for article in articles:
                    # Update the updated_at timestamp
                    article.updated_at = datetime.now()
                    
                    # Convert to sheet row
                    row = article.to_sheet_row()
                    
                    # Sanitize values for display
                    row = [self._sanitize_for_sheets(v) for v in row]
                    
                    if article.url in existing_articles:
                        # Update existing article
                        row_num = row_numbers[article.url]
                        updates.append((row_num, row))
                    else:
                        # Add new article
                        new_rows.append(row)
                
                # Perform batch updates
                for row_num, row_data in updates:
                    try:
                        cell_range = f'A{row_num}:{chr(65 + len(headers) - 1)}{row_num}'
                        worksheet.update(cell_range, [row_data], value_input_option='USER_ENTERED')
                        time.sleep(0.1)  # Rate limiting
                    except Exception as e:
                        print(f"Warning: Failed to update row {row_num}: {e}")
                
                # Append new articles
                if new_rows:
                    # Get the starting row for new data
                    start_row = len(existing_rows) + 2  # +1 for header, +1 for next row
                    worksheet.append_rows(new_rows, value_input_option='USER_ENTERED')
                    
                    # Apply formatting to new rows
                    end_row = start_row + len(new_rows) - 1
                    SheetFormatter.format_new_rows(worksheet, start_row, end_row, 'articles')
                    
                    # Update filter to include new data
                    total_rows = len(existing_rows) + len(new_rows) + 1  # +1 for header
                    SheetFormatter.ensure_filter_includes_new_data(worksheet, total_rows)
                    
            else:
                # Clear and rewrite all data
                worksheet.clear()
                
                # Add headers
                rows = [headers]
                
                # Add article data
                for article in articles:
                    row = article.to_sheet_row()
                    row = [self._sanitize_for_sheets(v) for v in row]
                    rows.append(row)
                
                # Update worksheet
                worksheet.update(rows, value_input_option='USER_ENTERED')
                
                # Apply formatting to all data rows
                if len(rows) > 1:
                    SheetFormatter.format_new_rows(worksheet, 2, len(rows), 'articles')
                    SheetFormatter.ensure_filter_includes_new_data(worksheet, len(rows))
            
            # Format headers
            worksheet.format('1:1', {
                'backgroundColor': {'red': 0.2, 'green': 0.5, 'blue': 0.8},
                'textFormat': {'bold': True, 'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}}
            })
            
            # Apply column widths
            SheetFormatter.auto_resize_columns(worksheet, 'articles')
            
            print(f"Successfully saved {len(articles)} articles to Google Sheets")
            return True
            
        except Exception as e:
            print(f"Error saving articles: {e}")
            return False
    
    def save_content_ideas(self, ideas: List[ContentIdea], upsert: bool = False) -> bool:
        """Save content ideas to Google Sheets using standardized schema.
        
        Args:
            ideas: List of content ideas to save
            upsert: If True, updates existing ideas or adds new ones. If False, overwrites all.
            
        Returns:
            True if successful, False otherwise
        """
        if not ideas or not self.spreadsheet:
            return False
        
        try:
            # Get or create Content Ideas worksheet
            worksheet = self._get_or_create_worksheet("Content Ideas")
            
            # Ensure correct headers
            headers = ContentIdea.sheet_headers()
            if not self._ensure_headers(worksheet, headers):
                print("Warning: Headers mismatch. Consider running purge script first.")
            
            if upsert:
                # Similar UPSERT logic as articles, but using idea ID
                try:
                    existing_data = worksheet.get_all_values()
                    if existing_data and len(existing_data) > 1:
                        existing_rows = existing_data[1:]
                    else:
                        existing_rows = []
                except:
                    existing_rows = []
                
                # Create lookup by ID (column index 0)
                existing_ideas = {}
                row_numbers = {}
                for idx, row in enumerate(existing_rows, start=2):
                    if len(row) > 0:
                        idea_id = row[0]
                        existing_ideas[idea_id] = row
                        row_numbers[idea_id] = idx
                
                # Process ideas
                updates = []
                new_rows = []
                
                for idea in ideas:
                    row = idea.to_sheet_row()
                    row = [self._sanitize_for_sheets(v) for v in row]
                    
                    if idea.id in existing_ideas:
                        row_num = row_numbers[idea.id]
                        updates.append((row_num, row))
                    else:
                        new_rows.append(row)
                
                # Perform updates
                for row_num, row_data in updates:
                    try:
                        cell_range = f'A{row_num}:{chr(65 + len(headers) - 1)}{row_num}'
                        worksheet.update(cell_range, [row_data], value_input_option='USER_ENTERED')
                        time.sleep(0.1)
                    except Exception as e:
                        print(f"Warning: Failed to update row {row_num}: {e}")
                
                if new_rows:
                    worksheet.append_rows(new_rows, value_input_option='USER_ENTERED')
                    
            else:
                # Clear and rewrite all
                worksheet.clear()
                
                rows = [headers]
                for idea in ideas:
                    row = idea.to_sheet_row()
                    row = [self._sanitize_for_sheets(v) for v in row]
                    rows.append(row)
                
                worksheet.update(rows, value_input_option='USER_ENTERED')
            
            # Get total rows for filter update
            total_rows = len(worksheet.get_all_values())
            
            # Apply formatting to new data if appending
            if total_rows > 1:
                SheetFormatter.format_new_rows(worksheet, 2, total_rows, 'ideas')
                SheetFormatter.ensure_filter_includes_new_data(worksheet, total_rows)
            
            # Format headers
            worksheet.format('1:1', {
                'backgroundColor': {'red': 0.2, 'green': 0.5, 'blue': 0.8},
                'textFormat': {'bold': True, 'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}}
            })
            
            # Apply column widths
            SheetFormatter.auto_resize_columns(worksheet, 'ideas')
            
            print(f"Successfully saved {len(ideas)} content ideas to Google Sheets")
            return True
            
        except Exception as e:
            print(f"Error saving content ideas: {e}")
            return False
    
    def save_summary_report(
        self, 
        articles: List[Article], 
        ideas: List[ContentIdea],
        processing_time: float = 0.0,
        errors: Optional[List[Dict[str, Any]]] = None
    ) -> bool:
        """Save structured summary report to Google Sheets.
        
        Args:
            articles: List of articles processed
            ideas: List of content ideas generated
            processing_time: Time taken to process in seconds
            errors: List of errors encountered during processing
            
        Returns:
            True if successful, False otherwise
        """
        if not self.spreadsheet:
            return False
        
        try:
            # Calculate statistics
            total_articles = len(articles)
            scraped_successfully = sum(1 for a in articles if a.scraping_success)
            
            # Calculate per-feed statistics
            feed_stats = {}
            for article in articles:
                feed_name = article.source_feed.value if hasattr(article.source_feed, 'value') else str(article.source_feed)
                if feed_name not in feed_stats:
                    feed_stats[feed_name] = {
                        "total": 0,
                        "scraped": 0,
                        "failed": 0
                    }
                feed_stats[feed_name]["total"] += 1
                if article.scraping_success:
                    feed_stats[feed_name]["scraped"] += 1
                else:
                    feed_stats[feed_name]["failed"] += 1
            
            # Create summary report object
            report = SummaryReport(
                run_date=datetime.now(),
                total_articles_fetched=total_articles,
                articles_scraped_successfully=scraped_successfully,
                ideas_generated=len(ideas),
                processing_time_seconds=processing_time,
                errors=errors or [],
                feed_statistics=feed_stats
            )
            
            # Get or create Summary Report worksheet
            worksheet = self._get_or_create_worksheet("Summary Report")
            
            # Ensure correct headers
            headers = SummaryReport.sheet_headers()
            
            # Check if sheet is empty
            try:
                existing_data = worksheet.get_all_values()
                if not existing_data:
                    worksheet.append_row(headers)
                    # Format headers
                    worksheet.format('1:1', {
                        'backgroundColor': {'red': 0.2, 'green': 0.6, 'blue': 0.9},
                        'textFormat': {'bold': True, 'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}}
                    })
            except:
                worksheet.append_row(headers)
            
            # Add the report row
            row = report.to_sheet_row()
            row = [self._sanitize_for_sheets(v) for v in row]
            worksheet.append_row(row, value_input_option='USER_ENTERED')
            
            print(f"Successfully saved summary report to Google Sheets")
            
            # Also create a human-readable summary in the old "Summary" sheet for backward compatibility
            self._save_legacy_summary(articles, ideas, report)
            
            return True
            
        except Exception as e:
            print(f"Error saving summary report: {e}")
            return False
    
    def _save_legacy_summary(self, articles: List[Article], ideas: List[ContentIdea], report: SummaryReport):
        """Save a human-readable summary for backward compatibility.
        
        Args:
            articles: List of articles processed
            ideas: List of content ideas generated
            report: The summary report object
        """
        try:
            worksheet = self._get_or_create_worksheet("Summary")
            worksheet.clear()
            
            # Prepare human-readable summary
            summary_data = [
                ["Content Pipeline Summary Report"],
                [""],
                ["Run Date:", report.run_date.strftime("%Y-%m-%d %H:%M:%S")],
                ["Run ID:", report.run_id],
                [""],
                ["=== STATISTICS ==="],
                ["Articles Processed:", report.total_articles_fetched],
                ["Successfully Scraped:", report.articles_scraped_successfully],
                ["Success Rate:", f"{report.scraping_success_rate:.1f}%"],
                ["Content Ideas Generated:", report.ideas_generated],
                ["Processing Time:", f"{report.processing_time_seconds:.2f} seconds"],
                [""],
                ["=== FEED BREAKDOWN ==="]
            ]
            
            # Add feed statistics
            for feed, stats in report.feed_statistics.items():
                summary_data.append([f"{feed}:", f"Total: {stats['total']}, Scraped: {stats['scraped']}, Failed: {stats['failed']}"])
            
            summary_data.append([""])
            summary_data.append(["=== TOP ARTICLES ==="])
            
            # Add top 10 articles
            for i, article in enumerate(articles[:10], 1):
                summary_data.append([f"{i}. {article.title[:100]}", article.url])
            
            if ideas:
                summary_data.append([""])
                summary_data.append(["=== CONTENT IDEAS GENERATED ==="])
                
                # Add all content ideas
                for i, idea in enumerate(ideas, 1):
                    summary_data.append([f"{i}. {idea.idea_title}", idea.content_type.value if hasattr(idea.content_type, 'value') else str(idea.content_type)])
            
            # Update worksheet
            worksheet.update(summary_data, value_input_option='USER_ENTERED')
            
            # Format title
            worksheet.format('1:1', {
                'backgroundColor': {'red': 0.2, 'green': 0.6, 'blue': 0.9},
                'textFormat': {'bold': True, 'fontSize': 16, 'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}}
            })
            
            # Format section headers
            for row_num in [6, 13]:  # Adjust based on actual row numbers
                try:
                    worksheet.format(f'{row_num}:{row_num}', {'textFormat': {'bold': True}})
                except:
                    pass
                    
        except Exception as e:
            print(f"Warning: Could not save legacy summary: {e}")
    
    def _get_or_create_worksheet(self, title: str):
        """Get existing worksheet or create new one.
        
        Args:
            title: Worksheet title
            
        Returns:
            Worksheet object
        """
        try:
            # Try to get existing worksheet
            return self.spreadsheet.worksheet(title)
        except gspread.WorksheetNotFound:
            # Create new worksheet
            return self.spreadsheet.add_worksheet(title=title, rows=1000, cols=20)
    
    def get_spreadsheet_info(self) -> Dict[str, Any]:
        """Get information about the spreadsheet.
        
        Returns:
            Dictionary with spreadsheet information
        """
        if not self.spreadsheet:
            return {"error": "Spreadsheet not initialized"}
        
        try:
            info = {
                "title": self.spreadsheet.title,
                "id": self.spreadsheet.id,
                "url": self.spreadsheet.url,
                "worksheets": []
            }
            
            for worksheet in self.spreadsheet.worksheets():
                try:
                    row_count = worksheet.row_count
                    col_count = worksheet.col_count
                    
                    # Try to get actual data dimensions
                    try:
                        all_values = worksheet.get_all_values()
                        actual_rows = len(all_values)
                        actual_cols = max(len(row) for row in all_values) if all_values else 0
                    except:
                        actual_rows = 0
                        actual_cols = 0
                    
                    info["worksheets"].append({
                        "title": worksheet.title,
                        "id": worksheet.id,
                        "row_count": row_count,
                        "col_count": col_count,
                        "actual_rows": actual_rows,
                        "actual_cols": actual_cols
                    })
                except Exception as e:
                    info["worksheets"].append({
                        "title": worksheet.title,
                        "error": str(e)
                    })
            
            return info
            
        except Exception as e:
            return {"error": str(e)}
    
    def get_articles(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Retrieve articles from Google Sheets.
        
        Args:
            limit: Maximum number of articles to retrieve
            
        Returns:
            List of article dictionaries
        """
        if not self.spreadsheet:
            return []
        
        try:
            worksheet = self.spreadsheet.worksheet("Articles")
            data = worksheet.get_all_values()
            
            if not data or len(data) < 2:
                return []
            
            headers = data[0]
            articles = []
            
            for row in data[1:limit+1] if limit else data[1:]:
                if row:  # Skip empty rows
                    article_dict = {}
                    for i, header in enumerate(headers):
                        if i < len(row):
                            article_dict[header.lower().replace(" ", "_")] = row[i]
                    articles.append(article_dict)
            
            return articles
            
        except Exception as e:
            print(f"Error retrieving articles: {e}")
            return []
    
    def update_article_status(self, url: str, **kwargs) -> bool:
        """Update specific fields of an article by URL.
        
        Args:
            url: The URL of the article to update
            **kwargs: Fields to update (e.g., scraping_success=True, content="...")
            
        Returns:
            True if successful, False otherwise
        """
        if not self.spreadsheet:
            return False
        
        try:
            worksheet = self.spreadsheet.worksheet("Articles")
            
            # Find the article by URL
            data = worksheet.get_all_values()
            if not data or len(data) < 2:
                return False
            
            headers = data[0]
            url_col = headers.index("URL") if "URL" in headers else 1
            
            for row_num, row in enumerate(data[1:], start=2):
                if len(row) > url_col and row[url_col] == url:
                    # Update specific fields
                    for field, value in kwargs.items():
                        # Map field name to column
                        field_name = field.replace("_", " ").title()
                        if field_name in headers:
                            col_idx = headers.index(field_name)
                            cell = f"{chr(65 + col_idx)}{row_num}"
                            worksheet.update(cell, self._sanitize_for_sheets(value), value_input_option='USER_ENTERED')
                    
                    # Update the "Updated At" timestamp
                    if "Updated At" in headers:
                        col_idx = headers.index("Updated At")
                        cell = f"{chr(65 + col_idx)}{row_num}"
                        worksheet.update(cell, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), value_input_option='USER_ENTERED')
                    
                    return True
            
            return False
            
        except Exception as e:
            print(f"Error updating article status: {e}")
            return False