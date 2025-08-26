"""Google Sheets formatting utilities."""

import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


class SheetFormatter:
    """Handles Google Sheets formatting operations."""
    
    # Column width definitions for different sheet types
    COLUMN_WIDTHS = {
        'articles': [
            100,   # ID
            250,   # URL
            300,   # Title
            350,   # Description
            400,   # Content
            150,   # Author
            120,   # Published Date
            120,   # Source Feed
            120,   # Scraping Strategy
            100,   # Scraping Success
            120,   # Created At
            120,   # Updated At
            80,    # Word Count
            100,   # Extraction Confidence
            200,   # Failure Reason
            200,   # Keywords
            200,   # Categories
        ],
        'ideas': [
            100,   # ID
            300,   # Title
            400,   # Description
            150,   # Type
            100,   # Priority
            200,   # Target Audience
            200,   # Keywords
            300,   # Source Articles
            120,   # Status
            150,   # Assigned To
            120,   # Created At
            120,   # Updated At
            300,   # Notes
        ],
        'summary': [
            200,   # Metric
            300,   # Value
            150,   # Count
            150,   # Percentage
        ]
    }
    
    @staticmethod
    def ensure_filter_includes_new_data(worksheet, last_row: int):
        """Update filter to include newly added rows."""
        try:
            cols = worksheet.col_count
            
            # Clear existing filter and create new one
            requests = [{
                'clearBasicFilter': {
                    'sheetId': worksheet.id
                }
            }, {
                'setBasicFilter': {
                    'filter': {
                        'range': {
                            'sheetId': worksheet.id,
                            'startRowIndex': 0,
                            'endRowIndex': last_row + 1,
                            'startColumnIndex': 0,
                            'endColumnIndex': cols
                        }
                    }
                }
            }]
            
            worksheet.spreadsheet.batch_update({'requests': requests})
            logger.debug(f"Updated filter to include row {last_row}")
            
        except Exception as e:
            logger.warning(f"Could not update filter: {e}")
    
    @staticmethod
    def format_new_rows(worksheet, start_row: int, end_row: int, sheet_type: str = 'articles'):
        """Apply formatting to newly added rows."""
        try:
            cols = worksheet.col_count
            requests = []
            
            # Format data cells (top-aligned, wrap text)
            requests.append({
                'repeatCell': {
                    'range': {
                        'sheetId': worksheet.id,
                        'startRowIndex': start_row - 1,  # 0-indexed
                        'endRowIndex': end_row,
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
            
            # Add borders to new cells
            requests.append({
                'updateBorders': {
                    'range': {
                        'sheetId': worksheet.id,
                        'startRowIndex': start_row - 1,
                        'endRowIndex': end_row,
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
            
            # Special formatting for articles sheet
            if sheet_type == 'articles':
                # Format confidence column as percentage (column N, index 13)
                requests.append({
                    'repeatCell': {
                        'range': {
                            'sheetId': worksheet.id,
                            'startRowIndex': start_row - 1,
                            'endRowIndex': end_row,
                            'startColumnIndex': 13,
                            'endColumnIndex': 14
                        },
                        'cell': {
                            'userEnteredFormat': {
                                'numberFormat': {
                                    'type': 'NUMBER',
                                    'pattern': '0.00'
                                }
                            }
                        },
                        'fields': 'userEnteredFormat.numberFormat'
                    }
                })
                
                # Format word count column as number (column M, index 12)
                requests.append({
                    'repeatCell': {
                        'range': {
                            'sheetId': worksheet.id,
                            'startRowIndex': start_row - 1,
                            'endRowIndex': end_row,
                            'startColumnIndex': 12,
                            'endColumnIndex': 13
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
                
                # Center align success column (column J, index 9)
                requests.append({
                    'repeatCell': {
                        'range': {
                            'sheetId': worksheet.id,
                            'startRowIndex': start_row - 1,
                            'endRowIndex': end_row,
                            'startColumnIndex': 9,
                            'endColumnIndex': 10
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
            if requests:
                worksheet.spreadsheet.batch_update({'requests': requests})
                logger.debug(f"Applied formatting to rows {start_row}-{end_row}")
            
        except Exception as e:
            logger.warning(f"Could not format new rows: {e}")
    
    @staticmethod
    def auto_resize_columns(worksheet, sheet_type: str = 'articles'):
        """Auto-resize columns based on content while respecting max widths."""
        try:
            widths = SheetFormatter.COLUMN_WIDTHS.get(sheet_type, SheetFormatter.COLUMN_WIDTHS['summary'])
            requests = []
            
            for i, width in enumerate(widths):
                if i >= worksheet.col_count:
                    break
                    
                requests.append({
                    'updateDimensionProperties': {
                        'range': {
                            'sheetId': worksheet.id,
                            'dimension': 'COLUMNS',
                            'startIndex': i,
                            'endIndex': i + 1
                        },
                        'properties': {
                            'pixelSize': width
                        },
                        'fields': 'pixelSize'
                    }
                })
            
            if requests:
                worksheet.spreadsheet.batch_update({'requests': requests})
                logger.debug("Auto-resized columns")
                
        except Exception as e:
            logger.warning(f"Could not auto-resize columns: {e}")