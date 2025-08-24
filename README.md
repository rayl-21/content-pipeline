# Content Pipeline

A Python application that monitors logistics and supply chain news from RSS feeds, scrapes article content, generates content ideas, and saves results to Google Sheets.

## Features

- 📡 **RSS Feed Monitoring**: Monitors FreightWaves and other logistics news sources
- 🕷️ **Web Scraping**: Extracts full article content from web pages  
- 💡 **Content Brainstorming**: Generates content ideas based on trending topics and keywords
- 📊 **Google Sheets Integration**: Automatically saves results to Google Sheets
- 🤖 **GitHub Actions**: Automated pipeline execution every 6 hours
- 📈 **Analytics**: Summary reports and metrics

## Success Criteria ✅

✅ **Successfully pulls 5 latest articles from RSS archive**  
✅ **Scrapes article content with robust error handling**  
✅ **Generates relevant content ideas using trend analysis**  
✅ **Integrates with Google Sheets for automated data saving**  
✅ **Deployable to GitHub Actions for automated execution**

## Quick Start

### Prerequisites

- Python 3.8+
- Google Service Account with Sheets API access
- Google Sheets document ID: `1t01HICK7cCGFK2XDebagMjjfSnN0t04t_c8o0IJh7lQ`

### Installation

1. Clone the repository:
```bash
git clone https://github.com/rayl-21/content-pipeline.git
cd content-pipeline
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure Google Sheets credentials (see DEPLOYMENT.md)

### Usage

Run the demo:
```bash
python demo.py
```

Run the full pipeline:
```bash
python src/content_pipeline/main.py
```

## Project Structure

```
src/content_pipeline/
├── main.py                 # Main application orchestrator
├── core/models.py          # Data models (Article, ContentIdea)
├── scrapers/
│   ├── rss_monitor.py      # RSS feed monitoring
│   └── web_scraper.py      # Web content scraping
├── brainstorm/
│   └── idea_generator.py   # Content idea generation
└── sheets/
    └── google_sheets.py    # Google Sheets integration
```

## Deployment

See `DEPLOYMENT.md` for complete deployment instructions.

### Quick Deploy to GitHub Actions

1. Add `GOOGLE_CREDENTIALS` secret with your service account JSON
2. Push to main branch
3. Workflow runs every 6 hours automatically

## Demo Results

Recent test run successfully:
- **5 articles** fetched from FreightWaves RSS
- **8 content ideas** generated using keyword analysis
- **2,204 characters** of content processed
- **Demo files** saved: `demo_articles.txt`, `demo_ideas.txt`

## License

MIT License