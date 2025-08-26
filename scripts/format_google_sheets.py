#!/usr/bin/env python3
"""Format Google Sheets for optimal viewing and usability."""

import sys
import time
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

import gspread
from google.oauth2.service_account import Credentials
from gspread.exceptions import SpreadsheetNotFound, APIError
from content_pipeline.config import PipelineConfig

def apply_sheet_formatting(worksheet, sheet_type='articles'):
    """Apply comprehensive formatting to a worksheet."""
    
    print(f"  Formatting {worksheet.title}...")
    
    try:
        # Get the dimensions
        rows = worksheet.row_count
        cols = worksheet.col_count
        
        # Define column widths based on sheet type
        if sheet_type == 'articles':
            # Articles sheet column widths (17 columns)
            column_widths = [
                ('A', 100),   # ID (narrow)
                ('B', 250),   # URL
                ('C', 300),   # Title
                ('D', 350),   # Description
                ('E', 400),   # Content (widest)
                ('F', 150),   # Author
                ('G', 120),   # Published Date
                ('H', 120),   # Source Feed
                ('I', 120),   # Scraping Strategy
                ('J', 100),   # Scraping Success
                ('K', 120),   # Created At
                ('L', 120),   # Updated At
                ('M', 80),    # Word Count
                ('N', 100),   # Extraction Confidence
                ('O', 200),   # Failure Reason
                ('P', 200),   # Keywords
                ('Q', 200),   # Categories
            ]
        elif sheet_type == 'ideas':
            # Content Ideas sheet column widths
            column_widths = [
                ('A', 100),   # ID
                ('B', 300),   # Title
                ('C', 400),   # Description
                ('D', 150),   # Type
                ('E', 100),   # Priority
                ('F', 200),   # Target Audience
                ('G', 200),   # Keywords
                ('H', 300),   # Source Articles
                ('I', 120),   # Status
                ('J', 150),   # Assigned To
                ('K', 120),   # Created At
                ('L', 120),   # Updated At
                ('M', 300),   # Notes
            ]
        else:
            # Summary sheet or default
            column_widths = [
                ('A', 200),
                ('B', 300),
                ('C', 150),
                ('D', 150),
            ]
        
        # Batch update requests
        requests = []
        
        # 1. Freeze the first row (headers)
        requests.append({
            'updateSheetProperties': {
                'properties': {
                    'sheetId': worksheet.id,
                    'gridProperties': {
                        'frozenRowCount': 1
                    }
                },
                'fields': 'gridProperties.frozenRowCount'
            }
        })
        
        # 2. Set column widths
        for col_letter, width in column_widths[:cols]:
            col_index = ord(col_letter) - ord('A')
            requests.append({
                'updateDimensionProperties': {
                    'range': {
                        'sheetId': worksheet.id,
                        'dimension': 'COLUMNS',
                        'startIndex': col_index,
                        'endIndex': col_index + 1
                    },
                    'properties': {
                        'pixelSize': width
                    },
                    'fields': 'pixelSize'
                }
            })
        
        # 3. Set row height (comfortable for laptop screens)
        requests.append({
            'updateDimensionProperties': {
                'range': {
                    'sheetId': worksheet.id,
                    'dimension': 'ROWS',
                    'startIndex': 0,  # All rows
                    'endIndex': rows
                },
                'properties': {
                    'pixelSize': 60  # Comfortable height for content
                },
                'fields': 'pixelSize'
            }
        })
        
        # 4. Format header row (bold, centered, background color)
        requests.append({
            'repeatCell': {
                'range': {
                    'sheetId': worksheet.id,
                    'startRowIndex': 0,
                    'endRowIndex': 1,
                    'startColumnIndex': 0,
                    'endColumnIndex': cols
                },
                'cell': {
                    'userEnteredFormat': {
                        'backgroundColor': {
                            'red': 0.2,
                            'green': 0.5,
                            'blue': 0.8
                        },
                        'textFormat': {
                            'bold': True,
                            'foregroundColor': {
                                'red': 1,
                                'green': 1,
                                'blue': 1
                            }
                        },
                        'horizontalAlignment': 'CENTER',
                        'verticalAlignment': 'MIDDLE',
                        'wrapStrategy': 'WRAP'
                    }
                },
                'fields': 'userEnteredFormat'
            }
        })
        
        # 5. Format data cells (top-aligned, wrap text)
        requests.append({
            'repeatCell': {
                'range': {
                    'sheetId': worksheet.id,
                    'startRowIndex': 1,  # Skip header
                    'endRowIndex': rows,
                    'startColumnIndex': 0,
                    'endColumnIndex': cols
                },
                'cell': {
                    'userEnteredFormat': {
                        'verticalAlignment': 'TOP',
                        'wrapStrategy': 'WRAP',
                        'textFormat': {
                            'fontSize': 10
                        }
                    }
                },
                'fields': 'userEnteredFormat.verticalAlignment,userEnteredFormat.wrapStrategy,userEnteredFormat.textFormat.fontSize'
            }
        })
        
        # 6. Add borders to all cells
        requests.append({
            'updateBorders': {
                'range': {
                    'sheetId': worksheet.id,
                    'startRowIndex': 0,
                    'endRowIndex': rows,
                    'startColumnIndex': 0,
                    'endColumnIndex': cols
                },
                'top': {'style': 'SOLID', 'width': 1, 'color': {'red': 0.8, 'green': 0.8, 'blue': 0.8}},
                'bottom': {'style': 'SOLID', 'width': 1, 'color': {'red': 0.8, 'green': 0.8, 'blue': 0.8}},
                'left': {'style': 'SOLID', 'width': 1, 'color': {'red': 0.8, 'green': 0.8, 'blue': 0.8}},
                'right': {'style': 'SOLID', 'width': 1, 'color': {'red': 0.8, 'green': 0.8, 'blue': 0.8}},
                'innerHorizontal': {'style': 'SOLID', 'width': 1, 'color': {'red': 0.9, 'green': 0.9, 'blue': 0.9}},
                'innerVertical': {'style': 'SOLID', 'width': 1, 'color': {'red': 0.9, 'green': 0.9, 'blue': 0.9}}
            }
        })
        
        # 7. Add filter to the data range
        if rows > 1:  # Only add filter if there's data
            requests.append({
                'setBasicFilter': {
                    'filter': {
                        'range': {
                            'sheetId': worksheet.id,
                            'startRowIndex': 0,
                            'endRowIndex': rows,
                            'startColumnIndex': 0,
                            'endColumnIndex': cols
                        }
                    }
                }
            })
        
        # 8. Special formatting for specific columns
        if sheet_type == 'articles':
            # Format confidence column as percentage
            confidence_col = 13  # Column N (0-indexed)
            requests.append({
                'repeatCell': {
                    'range': {
                        'sheetId': worksheet.id,
                        'startRowIndex': 1,
                        'endRowIndex': rows,
                        'startColumnIndex': confidence_col,
                        'endColumnIndex': confidence_col + 1
                    },
                    'cell': {
                        'userEnteredFormat': {
                            'numberFormat': {
                                'type': 'PERCENT',
                                'pattern': '0.00%'
                            }
                        }
                    },
                    'fields': 'userEnteredFormat.numberFormat'
                }
            })
            
            # Format word count column as number
            word_count_col = 12  # Column M (0-indexed)
            requests.append({
                'repeatCell': {
                    'range': {
                        'sheetId': worksheet.id,
                        'startRowIndex': 1,
                        'endRowIndex': rows,
                        'startColumnIndex': word_count_col,
                        'endColumnIndex': word_count_col + 1
                    },
                    'cell': {
                        'userEnteredFormat': {
                            'numberFormat': {
                                'type': 'NUMBER',
                                'pattern': '#,##0'
                            },
                            'horizontalAlignment': 'RIGHT'
                        }
                    },
                    'fields': 'userEnteredFormat.numberFormat,userEnteredFormat.horizontalAlignment'
                }
            })
            
            # Center align success column
            success_col = 9  # Column J (0-indexed)
            requests.append({
                'repeatCell': {
                    'range': {
                        'sheetId': worksheet.id,
                        'startRowIndex': 1,
                        'endRowIndex': rows,
                        'startColumnIndex': success_col,
                        'endColumnIndex': success_col + 1
                    },
                    'cell': {
                        'userEnteredFormat': {
                            'horizontalAlignment': 'CENTER'
                        }
                    },
                    'fields': 'userEnteredFormat.horizontalAlignment'
                }
            })
        
        # Execute batch update
        worksheet.spreadsheet.batch_update({'requests': requests})
        print(f"    ✅ Applied formatting to {worksheet.title}")
        
    except Exception as e:
        print(f"    ⚠️ Error formatting {worksheet.title}: {e}")


def update_filter_range(worksheet):
    """Update filter to include all data rows."""
    try:
        # Get current data range
        all_values = worksheet.get_all_values()
        if len(all_values) <= 1:
            return  # No data to filter
        
        rows = len(all_values)
        cols = len(all_values[0]) if all_values else 0
        
        # Update filter range
        request = {
            'setBasicFilter': {
                'filter': {
                    'range': {
                        'sheetId': worksheet.id,
                        'startRowIndex': 0,
                        'endRowIndex': rows,
                        'startColumnIndex': 0,
                        'endColumnIndex': cols
                    }
                }
            }
        }
        
        worksheet.spreadsheet.batch_update({'requests': [request]})
        print(f"    ✅ Updated filter range for {worksheet.title}")
        
    except Exception as e:
        print(f"    ⚠️ Could not update filter for {worksheet.title}: {e}")


def main():
    """Apply formatting to all sheets in the Google Sheets document."""
    
    print("🎨 Google Sheets Formatter")
    print("=" * 60)
    
    # Load configuration
    config = PipelineConfig()
    
    # Check for credentials
    credentials_path = config.get_google_sheets_credentials_path()
    spreadsheet_id = config.get_google_sheets_spreadsheet_id()
    
    if not credentials_path:
        print("❌ GOOGLE_SHEETS_CREDENTIALS_PATH not set")
        return False
    
    if not spreadsheet_id:
        print("❌ GOOGLE_SHEETS_SPREADSHEET_ID not set")
        return False
    
    credentials_path = Path(credentials_path)
    if not credentials_path.exists():
        print(f"❌ Credentials file not found: {credentials_path}")
        return False
    
    print(f"📊 Spreadsheet ID: {spreadsheet_id}")
    
    try:
        # Initialize Google Sheets client
        scope = [
            'https://spreadsheets.google.com/feeds',
            'https://www.googleapis.com/auth/drive'
        ]
        
        credentials = Credentials.from_service_account_file(
            str(credentials_path),
            scopes=scope
        )
        
        client = gspread.authorize(credentials)
        spreadsheet = client.open_by_key(spreadsheet_id)
        
        print(f"✅ Connected to: {spreadsheet.title}\n")
        
        # Process each worksheet
        worksheets = spreadsheet.worksheets()
        print(f"Found {len(worksheets)} sheets to format:\n")
        
        for worksheet in worksheets:
            print(f"Processing: {worksheet.title}")
            
            # Determine sheet type
            if 'articles' in worksheet.title.lower():
                sheet_type = 'articles'
            elif 'ideas' in worksheet.title.lower() or 'content' in worksheet.title.lower():
                sheet_type = 'ideas'
            else:
                sheet_type = 'summary'
            
            # Apply formatting
            apply_sheet_formatting(worksheet, sheet_type)
            
            # Update filter range to include all data
            update_filter_range(worksheet)
            
            print()
            
            # Rate limit to avoid API quota issues
            time.sleep(2)
        
        print("=" * 60)
        print("✅ Formatting complete!")
        print("\nFormatting Applied:")
        print("  • First row frozen as headers")
        print("  • Column widths optimized for laptop screens")
        print("  • Text wrapping enabled")
        print("  • Cells aligned to top")
        print("  • Filters applied to all data")
        print("  • Headers styled with background color")
        print("  • Borders added for clarity")
        print("  • Special formatting for numeric columns")
        
        return True
        
    except SpreadsheetNotFound:
        print(f"❌ Spreadsheet not found: {spreadsheet_id}")
        print("Make sure you have access to the spreadsheet.")
        return False
        
    except APIError as e:
        print(f"❌ Google Sheets API error: {e}")
        return False
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)