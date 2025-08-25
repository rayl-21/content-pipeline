# Content Pipeline

A high-performance Python application for monitoring logistics and supply chain news from multiple RSS feeds, extracting article content with anti-bot strategies, generating content ideas, and persisting results to Google Sheets.

## Features

- 📡 **Multi-Feed RSS Monitoring**: Concurrent monitoring of FreightWaves and FreightCaviar feeds with configurable limits
- 🕷️ **Advanced Web Scraping**: Multiple scraping strategies from basic to MCP Playwright integration
- 💡 **Content Brainstorming**: Intelligent content idea generation based on trending topics
- 📊 **Google Sheets Integration**: UPSERT logic for efficient data persistence
- 🤖 **GitHub Actions**: Automated execution every 6 hours
- ⚙️ **Flexible Configuration**: Command-line control over strategies, feeds, and logging

## Quick Start

### Prerequisites

- Python 3.8+
- Google Service Account with Sheets API access
- Target Sheet ID: `1t01HICK7cCGFK2XDebagMjjfSnN0t04t_c8o0IJh7lQ`

### Installation

```bash
# Clone repository
git clone https://github.com/rayl-21/content-pipeline.git
cd content-pipeline

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure Google credentials (see Deployment section)
```

## Usage

### Basic Usage
```bash
# Run with defaults (5 articles from each feed, enhanced scraping)
python src/content_pipeline/main.py
```

### Feed Configuration
```bash
# Custom article limits
python src/content_pipeline/main.py --freightwaves-limit 10 --freightcaviar-limit 3

# Disable specific feeds
python src/content_pipeline/main.py --disable-freightcaviar
python src/content_pipeline/main.py --disable-freightwaves

# Process all available articles
python src/content_pipeline/main.py --freightwaves-limit 0 --freightcaviar-limit 0
```

### Scraping Strategies
```bash
# Basic requests-based scraping (fastest)
python src/content_pipeline/main.py --strategy basic

# Enhanced with user-agent rotation (default)
python src/content_pipeline/main.py --strategy enhanced

# Cloudflare bypass for protected sites
python src/content_pipeline/main.py --strategy cloudscraper

# MCP Playwright for JavaScript-heavy sites (Claude Code only)
python src/content_pipeline/main.py --strategy mcp_playwright
```

### Logging Control
```bash
# Enable debug logging
python src/content_pipeline/main.py --log-level DEBUG

# Quiet mode (errors only)
python src/content_pipeline/main.py --log-level ERROR
```

### Complete Example
```bash
# Full control: 10 FreightWaves articles with Cloudflare bypass and debug logging
python src/content_pipeline/main.py \
    --freightwaves-limit 10 \
    --disable-freightcaviar \
    --strategy cloudscraper \
    --log-level DEBUG
```

## Project Structure

```
content-pipeline/
├── src/content_pipeline/
│   ├── main.py                 # Application orchestrator with CLI
│   ├── config.py               # Centralized configuration
│   ├── core/
│   │   └── models.py           # Data models (Article, ContentIdea)
│   ├── scrapers/
│   │   ├── scraper.py          # Unified scraper with strategy pattern
│   │   ├── web_scraper.py      # Legacy compatibility wrapper
│   │   └── rss_monitor.py      # RSS feed monitoring
│   ├── brainstorm/
│   │   └── idea_generator.py   # Content idea generation
│   └── sheets/
│       └── google_sheets.py    # Google Sheets integration with UPSERT
├── tests/                       # Test suite
├── .github/workflows/           # GitHub Actions automation
└── requirements.txt            # Python dependencies
```

## Development Workflow

### Local Development
```bash
# Install development dependencies
pip install -r requirements-dev.txt  # If available

# Run tests
pytest tests/

# Check code formatting
black --check src/
flake8 src/

# Format code
black src/
```

### Testing Scraping Strategies
```bash
# Test basic scraping
python tests/test_freightwaves_scraping.py

# Test MCP integration (Claude Code environment)
python tests/test_mcp_scraping.py
```

## Deployment

### Prerequisites for Deployment

- **Google Service Account**: Must have Google Sheets API access enabled
- **Service Account Email**: `content-pipeline-bot@gen-lang-client-0530198105.iam.gserviceaccount.com`
- **Target Sheet ID**: `1t01HICK7cCGFK2XDebagMjjfSnN0t04t_c8o0IJh7lQ`

### Quick Deploy to GitHub Actions

1. **Configure Google Sheets Credentials**
   - Go to: `https://github.com/rayl-21/content-pipeline/settings/secrets/actions`
   - Click "New repository secret"
   - Name: `GOOGLE_CREDENTIALS`
   - Value: Paste entire contents of your `content-pipeline-bot-key.json` file
   - Click "Add secret"

2. **Grant Sheet Access**
   - Share your Google Sheet with service account email above
   - Grant Editor permissions

3. **Verify Deployment**
   - Push to main branch
   - Check Actions tab for execution status
   - Pipeline runs every 6 hours (00:00, 06:00, 12:00, 18:00 UTC)

### Manual Trigger

1. Go to: https://github.com/rayl-21/content-pipeline/actions
2. Click "Content Pipeline" workflow
3. Click "Run workflow" → "Run workflow"

### Local Development Setup

```bash
# Clone and setup
git clone https://github.com/rayl-21/content-pipeline.git
cd content-pipeline
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Run with Google credentials
export GOOGLE_APPLICATION_CREDENTIALS="path/to/content-pipeline-bot-key.json"
python src/content_pipeline/main.py

# Or run demo mode (no credentials needed)
python demo.py
```

### Troubleshooting

**Common Issues:**
- **"No module named 'content_pipeline'"** → Check PYTHONPATH in workflow
- **"Credentials file not found"** → Verify GOOGLE_CREDENTIALS secret is properly set
- **"Permission denied on Google Sheet"** → Share sheet with service account email
- **"HTTP 403 errors on scraping"** → Expected behavior, pipeline falls back to RSS descriptions

**Debug Steps:**
1. Check GitHub Actions logs for detailed error messages
2. Verify Google Sheet permissions (must be shared with service account)
3. Test RSS feed accessibility manually
4. Validate JSON credentials format (must be valid JSON)

## Data Models

### Standardized Schema

The content pipeline uses standardized data models with validation, type safety, and consistent formatting across Python and Google Sheets.

#### Articles Table

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `id` | UUID | Unique identifier | Auto-generated |
| `url` | URL | Article URL | Required, validated, unique |
| `title` | String | Article title | Required, max 500 chars |
| `description` | Text | Article summary | Optional |
| `content` | Text | Full article content | Optional, unlimited |
| `author` | String | Article author | Optional, max 200 chars |
| `published_date` | DateTime | Publication date | Required, ISO format |
| `source_feed` | Enum | Feed source | FreightWaves, FreightCaviar, Custom |
| `scraping_strategy` | Enum | Strategy used | basic, enhanced, cloudscraper, mcp_playwright, none |
| `scraping_success` | Boolean | Scraping result | True/False |
| `created_at` | DateTime | Added to system | Auto-generated |
| `updated_at` | DateTime | Last update | Auto-updated |
| `word_count` | Integer | Content word count | Auto-calculated |
| `keywords` | List | Keywords/tags | Optional, comma-separated |
| `categories` | List | Article categories | Optional, comma-separated |

#### Content Ideas Table

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `id` | UUID | Unique identifier | Auto-generated |
| `idea_title` | String | Idea title | Required, max 200 chars |
| `idea_description` | Text | Detailed description | Optional |
| `target_audience` | String | Target audience | Optional, max 100 chars |
| `content_type` | Enum | Content format | blog, video, infographic, podcast, social_media, newsletter, whitepaper |
| `priority` | Enum | Priority level | high, medium, low |
| `keywords` | List | SEO keywords | Optional, comma-separated |
| `source_articles` | List | Article IDs | References to articles |
| `created_at` | DateTime | Creation date | Auto-generated |
| `status` | Enum | Idea status | proposed, in_progress, completed, rejected, on_hold |
| `themes` | List | Content themes | Optional, comma-separated |

#### Summary Report Table

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `run_id` | UUID | Pipeline run ID | Auto-generated |
| `run_date` | DateTime | Execution date | Required |
| `total_articles_fetched` | Integer | Articles processed | Required |
| `articles_scraped_successfully` | Integer | Successful scrapes | Required |
| `scraping_success_rate` | Percentage | Success rate | Auto-calculated |
| `ideas_generated` | Integer | Ideas created | Required |
| `processing_time_seconds` | Float | Execution time | Optional |
| `errors` | JSON | Error log | JSON array |
| `feed_statistics` | JSON | Per-feed metrics | JSON object |

### Data Validation

All data models include:
- **URL Validation**: Ensures valid URL format with scheme and netloc
- **Text Sanitization**: Removes control characters, normalizes whitespace
- **Length Constraints**: Enforces maximum lengths for fields
- **Enum Validation**: Ensures categorical values match allowed options
- **Automatic Calculations**: Word count, success rates, timestamps

### Backward Compatibility

Legacy field mappings are maintained for seamless migration:
- `summary` → `description` (Article)
- `scraped` → `scraping_success` (Article)
- `source` → `source_feed` (Article)
- `title` → `idea_title` (ContentIdea)
- `description` → `idea_description` (ContentIdea)

### Data Purge and Migration

A one-time purge script is available to standardize existing data:

```bash
# Backup only (safe exploration)
python scripts/purge_sheets_data.py --backup-only

# Full purge and setup (destructive)
python scripts/purge_sheets_data.py

# Purge and migrate old data to new format
python scripts/purge_sheets_data.py --migrate
```

The purge script will:
1. Create timestamped backups in `backups/` directory
2. Clear all existing sheets
3. Set up standardized headers
4. Optionally migrate old data to new format
5. Maintain data integrity throughout

## Architecture Overview

### Core Components

- **RSS Monitor** (`rss_monitor.py`): Fetches latest articles from FreightWaves and FreightCaviar feeds
- **Web Scraper** (`scraper.py`): Unified scraper with strategy pattern for content extraction
- **Idea Generator** (`idea_generator.py`): Creates content ideas using keyword analysis
- **Sheets Manager** (`google_sheets.py`): Handles UPSERT operations to Google Sheets

### Scraping Strategy Pattern

The unified scraper supports multiple strategies, automatically falling back when needed:

1. **BASIC**: Simple requests-based scraping
2. **ENHANCED**: User-agent rotation and improved headers (default)
3. **CLOUDSCRAPER**: Cloudflare bypass capabilities
4. **MCP_PLAYWRIGHT**: Full browser automation (Claude Code environment only)

### Data Flow

```
RSS Feeds → Article Extraction → Content Scraping → Idea Generation → Google Sheets
    ↓              ↓                    ↓                 ↓              ↓
[Monitor]    [Parse Metadata]    [Get Full Text]   [Analyze Topics]  [UPSERT]
```

## Command Reference

| Option | Description | Default |
|--------|-------------|---------|
| `--freightwaves-limit N` | Number of FreightWaves articles | 5 |
| `--freightcaviar-limit N` | Number of FreightCaviar articles | 5 |
| `--disable-freightwaves` | Skip FreightWaves feed | False |
| `--disable-freightcaviar` | Skip FreightCaviar feed | False |
| `--strategy STRATEGY` | Scraping strategy (basic/enhanced/cloudscraper/mcp_playwright) | enhanced |
| `--log-level LEVEL` | Logging verbosity (DEBUG/INFO/WARNING/ERROR) | INFO |
| `--help` | Show help message | - |

## Success Metrics

When operating correctly, the pipeline will:
- ✅ Fetch articles from configured RSS feeds
- ✅ Extract full article content with fallback to descriptions
- ✅ Generate 5-10 content ideas per batch
- ✅ Save to Google Sheets with proper deduplication (via UPSERT)
- ✅ Complete execution within 5 minutes
- ✅ Maintain 100% scraping success rate (content or fallback)

## Expected Output

Google Sheets Structure:
- **Articles Tab**: Raw article data with full content or descriptions
- **Content Ideas Tab**: Generated content ideas with topics and keywords
- **Summary Report Tab**: High-level metrics and execution timestamps

Recent Performance:
- Articles processed: 5-10 per feed per run
- Content ideas generated: 8-15 per batch
- Topics covered: Tariffs, imports, logistics, trucking, container rates
- Keywords identified: logistics, trade, fuel, regulations, supply chain

## License

MIT License