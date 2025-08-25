# Content Pipeline Project Overview

## Purpose
A Python application that monitors logistics and supply chain news from multiple RSS feeds (FreightWaves and FreightCaviar), scrapes article content, generates content ideas, and saves results to Google Sheets.

## Core Features
- Multi-Feed RSS Monitoring with configurable article limits
- Web Scraping for extracting full article content (currently blocked by FreightWaves)
- Content Brainstorming based on trending topics and keywords
- Google Sheets Integration for automated data saving
- GitHub Actions for automated pipeline execution every 6 hours
- Analytics and summary reports by feed source

## Technology Stack
- **Language**: Python 3.8+
- **Core Libraries**: 
  - feedparser (RSS parsing)
  - requests (HTTP requests) 
  - beautifulsoup4 (HTML parsing)
  - gspread + google-auth (Google Sheets API)
  - python-dotenv (environment variables)
- **Deployment**: GitHub Actions
- **Data Storage**: Google Sheets

## Project Structure
```
src/content_pipeline/
├── main.py                 # Main application orchestrator
├── config.py               # Configuration for feeds and settings
├── core/models.py          # Data models (Article, ContentIdea)
├── scrapers/
│   ├── rss_monitor.py      # RSS feed monitoring
│   └── web_scraper.py      # Web content scraping (NEEDS ENHANCEMENT)
├── brainstorm/
│   └── idea_generator.py   # Content idea generation
└── sheets/
    └── google_sheets.py    # Google Sheets integration
```

## Current Issues
- FreightWaves is blocking the simple requests-based scraper with 403 errors
- No advanced anti-bot detection strategies implemented
- No tests directory or testing framework setup