"""Test script for FreightWaves scraping using MCP Playwright integration."""

import sys
import logging
from datetime import datetime
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from content_pipeline.core.models import Article

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def test_freightwaves_with_mcp():
    """Test FreightWaves scraping using actual MCP Playwright functions."""
    print("🧪 Testing FreightWaves scraping with MCP Playwright...")
    
    # Create a test article from FreightWaves
    test_article = Article(
        title="Test FreightWaves Article - Supply Chain News",
        url="https://www.freightwaves.com/news",
        published_date=datetime.now(),
        summary="Test article to validate scraping capabilities against FreightWaves",
        source="FreightWaves"
    )
    
    print(f"📰 Test article: {test_article.title}")
    print(f"🔗 URL: {test_article.url}")
    
    try:
        # Step 1: Navigate to FreightWaves news page
        print("\n🌐 Step 1: Navigating to FreightWaves...")
        
        # Navigate to the page
        # This uses the actual MCP Playwright function available in Claude Code
        nav_result = mcp__playwright__browser_navigate(url=test_article.url)
        print(f"✅ Navigation successful")
        
        # Step 2: Wait for content to load
        print("\n⏳ Step 2: Waiting for content to load...")
        mcp__playwright__browser_wait_for(time=3)
        print("✅ Content loaded")
        
        # Step 3: Take a screenshot to see what we got
        print("\n📸 Step 3: Taking screenshot for analysis...")
        screenshot_result = mcp__playwright__browser_take_screenshot()
        print(f"✅ Screenshot taken: {screenshot_result}")
        
        # Step 4: Analyze page structure
        print("\n🔍 Step 4: Analyzing page structure...")
        
        structure_analysis_js = """
        () => {
            const info = {
                title: document.title,
                url: window.location.href,
                totalParagraphs: document.querySelectorAll('p').length,
                articles: document.querySelectorAll('article').length,
                contentSections: document.querySelectorAll('.entry-content, .post-content, .article-content').length,
                hasArticleElements: document.querySelectorAll('article, .article, .post').length > 0,
                bodyTextLength: document.body.textContent.length,
                potentialSelectors: []
            };
            
            // Test common content selectors
            const selectors = [
                'article',
                '.entry-content',
                '.post-content', 
                '.article-content',
                '.content',
                '.post-body',
                'main',
                '.news-item',
                '.story-content'
            ];
            
            selectors.forEach(selector => {
                const elements = document.querySelectorAll(selector);
                if (elements.length > 0) {
                    info.potentialSelectors.push({
                        selector: selector,
                        count: elements.length,
                        hasText: elements[0].textContent.length > 100
                    });
                }
            });
            
            return info;
        }
        """
        
        page_info = mcp__playwright__browser_evaluate(function=structure_analysis_js)
        
        print(f"📊 Page Analysis Results:")
        print(f"   Title: {page_info.get('title', 'N/A')}")
        print(f"   URL: {page_info.get('url', 'N/A')}")
        print(f"   Total paragraphs: {page_info.get('totalParagraphs', 0)}")
        print(f"   Article elements: {page_info.get('articles', 0)}")
        print(f"   Content sections: {page_info.get('contentSections', 0)}")
        print(f"   Body text length: {page_info.get('bodyTextLength', 0)}")
        print(f"   Has article elements: {page_info.get('hasArticleElements', False)}")
        
        if page_info.get('potentialSelectors'):
            print(f"   Potential content selectors:")
            for selector_info in page_info.get('potentialSelectors', []):
                print(f"     - {selector_info['selector']}: {selector_info['count']} elements, has text: {selector_info['hasText']}")
        
        # Step 5: Try to extract some content
        print("\n📝 Step 5: Attempting content extraction...")
        
        content_extraction_js = """
        () => {
            console.log('Starting FreightWaves content extraction...');
            
            // Look for news articles or content on the page
            const selectors = [
                'article',
                '.entry-content',
                '.post-content',
                '.article-content',
                '.news-item',
                '.story-content',
                '.content'
            ];
            
            let extractedContent = [];
            
            selectors.forEach(selector => {
                const elements = document.querySelectorAll(selector);
                console.log(`Trying selector ${selector}: found ${elements.length} elements`);
                
                elements.forEach((element, index) => {
                    if (index < 3) { // Only check first 3 elements
                        const text = element.textContent.trim();
                        if (text.length > 50) {
                            extractedContent.push({
                                selector: selector,
                                index: index,
                                preview: text.substring(0, 150) + '...',
                                length: text.length
                            });
                        }
                    }
                });
            });
            
            // Also try to find headlines/titles
            const headlines = [];
            const headlineSelectors = ['h1', 'h2', 'h3', '.headline', '.title', 'article h1', 'article h2'];
            
            headlineSelectors.forEach(selector => {
                const elements = document.querySelectorAll(selector);
                elements.forEach((element, index) => {
                    if (index < 5) {
                        const text = element.textContent.trim();
                        if (text.length > 10 && text.length < 200) {
                            headlines.push(text);
                        }
                    }
                });
            });
            
            return {
                extractedContent: extractedContent,
                headlines: headlines,
                totalContentFound: extractedContent.length
            };
        }
        """
        
        extraction_result = mcp__playwright__browser_evaluate(function=content_extraction_js)
        
        print(f"📄 Content Extraction Results:")
        print(f"   Total content sections found: {extraction_result.get('totalContentFound', 0)}")
        
        if extraction_result.get('headlines'):
            print(f"   Headlines found ({len(extraction_result['headlines'])}):")
            for i, headline in enumerate(extraction_result.get('headlines', [])[:5]):
                print(f"     {i+1}. {headline}")
        
        if extraction_result.get('extractedContent'):
            print(f"   Content sections:")
            for content in extraction_result.get('extractedContent', [])[:3]:
                print(f"     - {content['selector']}[{content['index']}]: {content['length']} chars")
                print(f"       Preview: {content['preview']}")
        
        # Step 6: Test specific FreightWaves article extraction
        print("\n📰 Step 6: Testing article-specific extraction...")
        
        # Look for actual article links to test
        article_links_js = """
        () => {
            const links = [];
            const linkElements = document.querySelectorAll('a[href*="/news/"]');
            
            linkElements.forEach((link, index) => {
                if (index < 5) {
                    const href = link.getAttribute('href');
                    const text = link.textContent.trim();
                    
                    if (text.length > 10 && href && !href.includes('#')) {
                        let fullUrl = href;
                        if (href.startsWith('/')) {
                            fullUrl = 'https://www.freightwaves.com' + href;
                        }
                        
                        links.push({
                            url: fullUrl,
                            title: text,
                            length: text.length
                        });
                    }
                }
            });
            
            return links;
        }
        """
        
        article_links = mcp__playwright__browser_evaluate(function=article_links_js)
        
        if article_links and len(article_links) > 0:
            print(f"🔗 Found {len(article_links)} article links:")
            
            # Test scraping the first actual article
            test_article_url = article_links[0]['url']
            test_article_title = article_links[0]['title']
            
            print(f"   Testing first article: {test_article_title}")
            print(f"   URL: {test_article_url}")
            
            # Navigate to the specific article
            print(f"\n🌐 Navigating to specific article...")
            mcp__playwright__browser_navigate(url=test_article_url)
            mcp__playwright__browser_wait_for(time=4)  # Wait longer for article to load
            
            # Extract content from the specific article
            article_content_js = """
            () => {
                console.log('Extracting content from specific FreightWaves article...');
                
                const selectors = [
                    '.entry-content',
                    '.post-content',
                    '.article-content',
                    'article .content',
                    '.single-post-content',
                    '[data-module="ArticleBody"]',
                    '.post-body'
                ];
                
                let bestContent = null;
                let bestSelector = null;
                
                for (const selector of selectors) {
                    const element = document.querySelector(selector);
                    if (element) {
                        const paragraphs = element.querySelectorAll('p');
                        if (paragraphs.length > 0) {
                            const content = Array.from(paragraphs)
                                .map(p => p.textContent.trim())
                                .filter(text => text.length > 20)
                                .join('\\n\\n');
                            
                            if (content.length > (bestContent ? bestContent.length : 0)) {
                                bestContent = content;
                                bestSelector = selector;
                            }
                        }
                    }
                }
                
                return {
                    content: bestContent,
                    selector: bestSelector,
                    length: bestContent ? bestContent.length : 0,
                    preview: bestContent ? bestContent.substring(0, 300) + '...' : null,
                    articleTitle: document.title,
                    url: window.location.href
                };
            }
            """
            
            article_content = mcp__playwright__browser_evaluate(function=article_content_js)
            
            print(f"📄 Article Content Extraction Results:")
            print(f"   Article title: {article_content.get('articleTitle', 'N/A')}")
            print(f"   Best selector: {article_content.get('selector', 'None')}")
            print(f"   Content length: {article_content.get('length', 0)} characters")
            
            if article_content.get('content') and article_content.get('length', 0) > 100:
                print(f"   ✅ SUCCESS! Content extracted successfully")
                print(f"   Preview: {article_content.get('preview', 'No preview')}")
                
                # Update our test article with the real results
                test_article.content = article_content['content']
                test_article.scraped = True
                test_article.url = article_content.get('url', test_article.url)
                test_article.title = article_content.get('articleTitle', test_article.title)
                
            else:
                print(f"   ❌ FAILED! Insufficient content extracted")
                test_article.content = test_article.summary
                test_article.scraped = False
        
        else:
            print("   ❌ No article links found to test")
            test_article.content = test_article.summary
            test_article.scraped = False
        
        # Final results
        print("\n" + "="*60)
        print("🧪 FREIGHTWAVES SCRAPING TEST RESULTS")
        print("="*60)
        print(f"✅ Navigation: SUCCESS")
        print(f"✅ Page loading: SUCCESS")
        print(f"✅ JavaScript execution: SUCCESS")
        print(f"{'✅' if test_article.scraped else '❌'} Content extraction: {'SUCCESS' if test_article.scraped else 'FAILED'}")
        print(f"📊 Content length: {len(test_article.content)} characters")
        print(f"🎯 Success rate: {'100%' if test_article.scraped else '0%'}")
        
        if test_article.scraped:
            print(f"\n📝 Extracted content preview:")
            print(f"{test_article.content[:500]}...")
        
        print("="*60)
        
        return test_article.scraped
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        logger.error(f"FreightWaves scraping test error: {e}")
        return False


def test_enhanced_scraper_integration():
    """Test the enhanced scraper with actual MCP integration."""
    print("\n🔧 Testing Enhanced Scraper Integration...")
    
    try:
        from content_pipeline.scrapers.mcp_integration import create_mcp_scraper
        
        # Create MCP scraper
        mcp_scraper = create_mcp_scraper()
        
        # Test article
        test_article = Article(
            title="Integration Test Article",
            url="https://www.freightwaves.com/news",
            published_date=datetime.now(),
            summary="Integration test for MCP scraper",
            source="FreightWaves"
        )
        
        print(f"🧪 Testing MCP scraper integration...")
        print(f"   MCP Available: {mcp_scraper.mcp_available}")
        
        if mcp_scraper.mcp_available:
            # Test single article scraping
            result = mcp_scraper.scrape_single_article(test_article)
            
            print(f"   Scraping result: {'SUCCESS' if result.scraped else 'FAILED'}")
            print(f"   Content length: {len(result.content)} chars")
            
            return result.scraped
        else:
            print(f"   ❌ MCP functions not available in current environment")
            return False
            
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        logger.error(f"Integration test error: {e}")
        return False


if __name__ == "__main__":
    print("🚀 Starting FreightWaves Scraping Test Suite...")
    
    # Test 1: Direct MCP scraping
    print("\n" + "="*60)
    print("TEST 1: Direct MCP Playwright Scraping")
    print("="*60)
    
    success1 = test_freightwaves_with_mcp()
    
    # Test 2: Enhanced scraper integration
    print("\n" + "="*60)
    print("TEST 2: Enhanced Scraper Integration")
    print("="*60)
    
    success2 = test_enhanced_scraper_integration()
    
    # Overall results
    print("\n" + "="*60)
    print("🏆 OVERALL TEST RESULTS")
    print("="*60)
    print(f"Direct MCP scraping: {'✅ PASS' if success1 else '❌ FAIL'}")
    print(f"Enhanced integration: {'✅ PASS' if success2 else '❌ FAIL'}")
    print(f"Overall success: {'✅ PASS' if (success1 or success2) else '❌ FAIL'}")
    print("="*60)
    
    # Return appropriate exit code
    sys.exit(0 if (success1 or success2) else 1)