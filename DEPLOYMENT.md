# Deployment Guide

## 🚀 Quick Setup Instructions

### 1. ✅ Repository Created
✅ Repository: https://github.com/rayl-21/content-pipeline  
✅ Core files uploaded  
✅ GitHub Actions workflow configured

### 2. 🔐 Configure Google Sheets Credentials

**REQUIRED**: Add your Google service account credentials as a GitHub Secret:

1. Go to: https://github.com/rayl-21/content-pipeline/settings/secrets/actions
2. Click "New repository secret"
3. **Name**: `GOOGLE_CREDENTIALS`
4. **Value**: Copy the entire contents of your `content-pipeline-bot-key.json` file
5. Click "Add secret"

### 3. 🎯 Target Google Sheet
- **Spreadsheet ID**: `1t01HICK7cCGFK2XDebagMjjfSnN0t04t_c8o0IJh7lQ`
- **Service Account Email**: `content-pipeline-bot@gen-lang-client-0530198105.iam.gserviceaccount.com`

**Make sure this service account has edit access to your Google Sheet!**

### 4. 🚀 Trigger the Pipeline

#### Manual Trigger:
1. Go to: https://github.com/rayl-21/content-pipeline/actions
2. Click on "Content Pipeline" workflow
3. Click "Run workflow" → "Run workflow"

#### Automatic Schedule:
- Runs every 6 hours automatically
- Next scheduled run will be at the next 6-hour interval (00:00, 06:00, 12:00, 18:00 UTC)

### 5. ✅ Success Criteria Verification

The pipeline will:
✅ Pull 5 latest articles from https://www.freightwaves.com/feed  
✅ Scrape article content (with graceful fallback to descriptions)  
✅ Generate content ideas using keyword analysis  
✅ Save results to your Google Sheets in 3 tabs:
   - **Articles**: Raw article data  
   - **Content Ideas**: Generated content ideas  
   - **Summary Report**: High-level metrics  

### 6. 📊 Monitor Results

Check your Google Sheet: https://docs.google.com/spreadsheets/d/1t01HICK7cCGFK2XDebagMjjfSnN0t04t_c8o0IJh7lQ

## 🏗️ Architecture

```
Content Pipeline Architecture:
📡 RSS Monitor → 🕷️ Web Scraper → 💡 Idea Generator → 📊 Google Sheets
```

### Core Components:
- **RSS Monitor**: Fetches latest articles from FreightWaves
- **Web Scraper**: Extracts full content (with error handling)
- **Idea Generator**: Creates content ideas using keyword analysis
- **Sheets Manager**: Saves data to Google Sheets with proper formatting

## 🔧 Local Development

```bash
# Clone and setup
git clone https://github.com/rayl-21/content-pipeline.git
cd content-pipeline
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run demo (no credentials needed)
python demo.py

# Run full pipeline (requires Google credentials)
python src/content_pipeline/main.py
```

## 📈 Expected Output

Recent successful test:
- **5 articles** processed from FreightWaves RSS
- **8 content ideas** generated
- **Topics covered**: Tariffs, imports, postal services, trucking, container rates
- **Keywords identified**: logistics, trade, fuel, tariffs, regulations

## 🆘 Troubleshooting

### Common Issues:
1. **"No module named 'content_pipeline'"** → Check PYTHONPATH in workflow
2. **"Credentials file not found"** → Verify GOOGLE_CREDENTIALS secret
3. **"Permission denied on Google Sheet"** → Share sheet with service account email
4. **"HTTP 403 errors on scraping"** → Expected, pipeline falls back to RSS descriptions

### Debug Steps:
1. Check GitHub Actions logs
2. Verify Google Sheet permissions
3. Test RSS feed accessibility
4. Validate JSON credentials format

## 🎉 Success Indicators

When working correctly, you'll see:
- Green checkmarks in GitHub Actions
- New data in your Google Sheet tabs
- Recent timestamps in the "Summary Report" tab
- No error artifacts uploaded

---

**Repository**: https://github.com/rayl-21/content-pipeline  
**Sheet**: https://docs.google.com/spreadsheets/d/1t01HICK7cCGFK2XDebagMjjfSnN0t04t_c8o0IJh7lQ  
**Actions**: https://github.com/rayl-21/content-pipeline/actions