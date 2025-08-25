"""Google Sheets integration for saving content pipeline results."""

import json
from datetime import datetime
from typing import List, Optional, Dict, Any

import gspread
from google.oauth2.service_account import Credentials

from content_pipeline.core.models import Article, ContentIdea


class GoogleSheetsManager:
    """Manages Google Sheets operations for the content pipeline."""
    
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
    
    def save_articles(self, articles: List[Article], upsert: bool = True) -> bool:
        """Save articles to Google Sheets with UPSERT logic.
        
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
            
            # Prepare headers
            headers = [
                "Title", "URL", "Published Date", "Author", 
                "Summary", "Content", "Categories", "Scraped", "Source", "Last Updated"
            ]
            
            if upsert:
                # Get existing data
                try:
                    existing_data = worksheet.get_all_values()
                    if existing_data and len(existing_data) > 0:
                        # Skip header row
                        existing_rows = existing_data[1:] if len(existing_data) > 1 else []
                    else:
                        existing_rows = []
                        worksheet.clear()
                        worksheet.append_row(headers)
                except:
                    existing_rows = []
                    worksheet.clear()
                    worksheet.append_row(headers)
                
                # Create a dictionary of existing articles by URL for quick lookup
                existing_articles = {}
                row_numbers = {}
                for idx, row in enumerate(existing_rows, start=2):  # Start from row 2 (after header)
                    if len(row) > 1:  # Make sure row has URL column
                        url = row[1]
                        existing_articles[url] = row
                        row_numbers[url] = idx
                
                # Process new articles
                updates = []  # List of (row_number, row_data) for batch update
                new_rows = []  # New articles to append
                
                for article in articles:
                    row = [
                        article.title,
                        article.url,
                        article.published_date.strftime("%Y-%m-%d %H:%M:%S") if article.published_date else "",
                        article.author or "",
                        article.summary or "",
                        (article.content or "")[:1000] + "..." if hasattr(article, 'content') and article.content and len(article.content) > 1000 else (article.content or ""),
                        ", ".join(article.categories) if article.categories else "",
                        str(getattr(article, 'scraped', False)),
                        getattr(article, 'source', ''),
                        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    ]
                    
                    if article.url in existing_articles:
                        # Update existing article
                        row_num = row_numbers[article.url]
                        updates.append((row_num, row))
                    else:
                        # Add new article
                        new_rows.append(row)
                
                # Perform batch updates for existing articles
                for row_num, row_data in updates:
                    cell_range = f'A{row_num}:J{row_num}'
                    worksheet.update(cell_range, [row_data], value_input_option='USER_ENTERED')
                
                # Append new articles
                if new_rows:
                    worksheet.append_rows(new_rows, value_input_option='USER_ENTERED')
                    
            else:
                # Clear and rewrite all data (original behavior)
                worksheet.clear()
                
                # Prepare data rows
                rows = [headers]
                for article in articles:
                    row = [
                        article.title,
                        article.url,
                        article.published_date.strftime("%Y-%m-%d %H:%M:%S") if article.published_date else "",
                        article.author or "",
                        article.summary or "",
                        (article.content or "")[:1000] + "..." if hasattr(article, 'content') and article.content and len(article.content) > 1000 else (article.content or ""),
                        ", ".join(article.categories) if article.categories else "",
                        str(getattr(article, 'scraped', False)),
                        getattr(article, 'source', ''),
                        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    ]
                    rows.append(row)
                
                # Update the worksheet
                worksheet.update(rows, value_input_option='USER_ENTERED')
            
            # Format headers
            worksheet.format('1:1', {
                'backgroundColor': {'red': 0.8, 'green': 0.8, 'blue': 0.8},
                'textFormat': {'bold': True}
            })
            
            return True
            
        except Exception as e:
            print(f"Error saving articles: {e}")
            return False
    
    def save_content_ideas(self, ideas: List[ContentIdea]) -> bool:
        """Save content ideas to Google Sheets.
        
        Args:
            ideas: List of content ideas to save
            
        Returns:
            True if successful, False otherwise
        """
        if not ideas or not self.spreadsheet:
            return False
        
        try:
            # Get or create Content Ideas worksheet
            worksheet = self._get_or_create_worksheet("Content Ideas")
            
            # Clear existing data
            worksheet.clear()
            
            # Prepare headers
            headers = [
                "Title", "Content Type", "Keywords", "Themes", 
                "Source Articles", "Created Date"
            ]
            
            # Prepare data rows
            rows = [headers]
            for idea in ideas:
                row = [
                    idea.title,
                    idea.content_type,
                    ", ".join(idea.keywords) if idea.keywords else "",
                    ", ".join(idea.themes) if hasattr(idea, 'themes') and idea.themes else "",
                    "\n".join(idea.source_articles) if idea.source_articles else "",
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                ]
                rows.append(row)
            
            # Update the worksheet
            worksheet.update(rows, value_input_option='USER_ENTERED')
            
            # Format headers
            worksheet.format('1:1', {
                'backgroundColor': {'red': 0.8, 'green': 0.9, 'blue': 0.8},
                'textFormat': {'bold': True}
            })
            
            return True
            
        except Exception as e:
            print(f"Error saving content ideas: {e}")
            return False
    
    def save_summary_report(self, articles: List[Article], ideas: List[ContentIdea]) -> bool:
        """Save summary report to Google Sheets.
        
        Args:
            articles: List of articles processed
            ideas: List of content ideas generated
            
        Returns:
            True if successful, False otherwise
        """
        if not self.spreadsheet:
            return False
        
        try:
            # Get or create Summary worksheet
            worksheet = self._get_or_create_worksheet("Summary")
            
            # Clear existing data
            worksheet.clear()
            
            # Prepare summary data
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            summary_data = [
                ["Content Pipeline Summary Report"],
                [""],
                ["Run Date:", current_time],
                [""],
                ["Articles Processed:", len(articles)],
                ["Content Ideas Generated:", len(ideas)],
                [""],
                ["Article Sources:"]
            ]
            
            # Add article titles
            for i, article in enumerate(articles, 1):
                summary_data.append([f"{i}. {article.title}", article.url])
            
            summary_data.append([""])
            summary_data.append(["Content Ideas Generated:"])
            
            # Add content ideas
            for i, idea in enumerate(ideas, 1):
                summary_data.append([f"{i}. {idea.title}", idea.content_type])
            
            # Update the worksheet
            worksheet.update(summary_data, value_input_option='USER_ENTERED')
            
            # Format title
            worksheet.format('1:1', {
                'backgroundColor': {'red': 0.2, 'green': 0.6, 'blue': 0.9},
                'textFormat': {'bold': True, 'fontSize': 16, 'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}}
            })
            
            # Format headers
            worksheet.format('3:3', {'textFormat': {'bold': True}})
            worksheet.format('5:6', {'textFormat': {'bold': True}})
            worksheet.format('8:8', {'textFormat': {'bold': True}})
            
            return True
            
        except Exception as e:
            print(f"Error saving summary report: {e}")
            return False
    
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
                info["worksheets"].append({
                    "title": worksheet.title,
                    "id": worksheet.id,
                    "row_count": worksheet.row_count,
                    "col_count": worksheet.col_count
                })
            
            return info
            
        except Exception as e:
            return {"error": str(e)}