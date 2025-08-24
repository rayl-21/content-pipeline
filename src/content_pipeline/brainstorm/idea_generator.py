"""Content idea generation from articles."""

import re
from typing import List, Set, Dict
from collections import Counter

from content_pipeline.core.models import Article, ContentIdea


class IdeaGenerator:
    """Generates content ideas based on scraped articles."""
    
    def __init__(self):
        """Initialize the idea generator."""
        self.content_types = [
            "Blog Post",
            "Social Media Post",
            "Newsletter",
            "Video Script",
            "Infographic",
            "Whitepaper",
            "Case Study",
            "Tutorial",
            "Listicle",
            "Analysis"
        ]
        
        # Common stop words to filter out
        self.stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'this', 'that', 'these', 'those', 'is', 'are',
            'was', 'were', 'be', 'been', 'have', 'has', 'had', 'will', 'would',
            'could', 'should', 'may', 'might', 'can', 'do', 'does', 'did', 'get',
            'got', 'go', 'goes', 'went', 'come', 'came', 'take', 'took', 'make',
            'made', 'see', 'saw', 'know', 'knew', 'think', 'thought', 'say', 'said'
        }
    
    def generate_ideas(self, articles: List[Article]) -> List[ContentIdea]:
        """Generate content ideas from a list of articles.
        
        Args:
            articles: List of Article objects
            
        Returns:
            List of ContentIdea objects
        """
        if not articles:
            return []
        
        ideas = []
        
        # Extract themes and keywords
        all_keywords = self._extract_keywords(articles)
        themes = self._identify_themes(articles, all_keywords)
        
        # Generate ideas based on individual articles
        for article in articles:
            article_ideas = self._generate_article_ideas(article, themes)
            ideas.extend(article_ideas)
        
        # Generate cross-article ideas
        cross_ideas = self._generate_cross_article_ideas(articles, themes)
        ideas.extend(cross_ideas)
        
        # Remove duplicates and sort by relevance
        unique_ideas = self._deduplicate_ideas(ideas)
        
        return unique_ideas[:10]  # Return top 10 ideas
    
    def _extract_keywords(self, articles: List[Article]) -> List[str]:
        """Extract keywords from articles.
        
        Args:
            articles: List of articles
            
        Returns:
            List of keywords sorted by frequency
        """
        all_text = []
        
        for article in articles:
            # Combine title, summary, and content
            text_parts = [article.title, article.summary]
            if hasattr(article, 'content') and article.content:
                text_parts.append(article.content)
            
            all_text.extend(text_parts)
        
        # Extract words
        words = []
        for text in all_text:
            if text:
                # Clean and split text
                clean_text = re.sub(r'[^\w\s]', ' ', text.lower())
                text_words = clean_text.split()
                words.extend([w for w in text_words if len(w) > 3 and w not in self.stop_words])
        
        # Count word frequency
        word_counts = Counter(words)
        
        # Return top keywords
        return [word for word, _ in word_counts.most_common(50)]
    
    def _identify_themes(self, articles: List[Article], keywords: List[str]) -> Dict[str, List[str]]:
        """Identify common themes across articles.
        
        Args:
            articles: List of articles
            keywords: List of keywords
            
        Returns:
            Dictionary mapping theme names to related keywords
        """
        themes = {}
        
        # Predefined theme categories
        theme_categories = {
            'technology': ['tech', 'digital', 'software', 'data', 'ai', 'automation', 'platform', 'system'],
            'business': ['business', 'company', 'market', 'industry', 'revenue', 'growth', 'strategy'],
            'logistics': ['shipping', 'freight', 'supply', 'chain', 'transportation', 'delivery', 'warehouse'],
            'finance': ['financial', 'investment', 'cost', 'price', 'funding', 'capital', 'money'],
            'environment': ['sustainable', 'green', 'environment', 'carbon', 'emission', 'climate'],
            'regulation': ['regulation', 'compliance', 'policy', 'government', 'law', 'legal']
        }
        
        for theme_name, theme_words in theme_categories.items():
            matching_keywords = []
            for keyword in keywords:
                if any(theme_word in keyword for theme_word in theme_words):
                    matching_keywords.append(keyword)
            
            if matching_keywords:
                themes[theme_name] = matching_keywords[:10]  # Top 10 keywords per theme
        
        return themes
    
    def _generate_article_ideas(self, article: Article, themes: Dict[str, List[str]]) -> List[ContentIdea]:
        """Generate ideas based on a single article.
        
        Args:
            article: Single article
            themes: Identified themes
            
        Returns:
            List of content ideas
        """
        ideas = []
        
        # Find which themes this article relates to
        article_text = f"{article.title} {article.summary}".lower()
        related_themes = []
        
        for theme, keywords in themes.items():
            if any(keyword in article_text for keyword in keywords):
                related_themes.append(theme)
        
        # Generate different types of content ideas
        idea_templates = [
            "Understanding {title}: A Deep Dive",
            "5 Key Takeaways from {title}",
            "How {title} Impacts Your Business",
            "The Future Implications of {title}",
            "Breaking Down {title}: What You Need to Know"
        ]
        
        for template in idea_templates:
            main_topic = self._extract_main_topic(article.title)
            idea_title = template.format(title=main_topic)
            
            # Select keywords from related themes
            idea_keywords = []
            for theme in related_themes:
                idea_keywords.extend(themes[theme][:3])
            
            # Add article-specific keywords
            article_keywords = self._extract_keywords([article])
            idea_keywords.extend(article_keywords[:5])
            
            idea = ContentIdea(
                title=idea_title,
                content_type=self._select_content_type(template),
                keywords=list(set(idea_keywords)),
                source_articles=[article.url],
                themes=related_themes
            )
            ideas.append(idea)
        
        return ideas
    
    def _generate_cross_article_ideas(self, articles: List[Article], themes: Dict[str, List[str]]) -> List[ContentIdea]:
        """Generate ideas that combine multiple articles.
        
        Args:
            articles: List of articles
            themes: Identified themes
            
        Returns:
            List of cross-article content ideas
        """
        ideas = []
        
        # Generate theme-based ideas
        for theme, keywords in themes.items():
            if len(keywords) >= 3:
                theme_ideas = [
                    f"Top {theme.title()} Trends This Week",
                    f"{theme.title()} Industry Roundup",
                    f"What's Happening in {theme.title()}",
                    f"{theme.title()} News You Can't Miss"
                ]
                
                for idea_title in theme_ideas:
                    idea = ContentIdea(
                        title=idea_title,
                        content_type="Newsletter",
                        keywords=keywords[:10],
                        source_articles=[article.url for article in articles],
                        themes=[theme]
                    )
                    ideas.append(idea)
        
        return ideas
    
    def _extract_main_topic(self, title: str) -> str:
        """Extract the main topic from an article title.
        
        Args:
            title: Article title
            
        Returns:
            Main topic string
        """
        # Remove common prefixes and suffixes
        clean_title = re.sub(r'^(the|a|an)\s+', '', title.lower())
        clean_title = re.sub(r'\s+(news|report|update|analysis)$', '', clean_title)
        
        # Limit length
        if len(clean_title) > 50:
            clean_title = clean_title[:50] + "..."
        
        return clean_title.title()
    
    def _select_content_type(self, template: str) -> str:
        """Select appropriate content type based on template.
        
        Args:
            template: Idea template
            
        Returns:
            Content type
        """
        if "takeaways" in template.lower() or "key" in template.lower():
            return "Listicle"
        elif "deep dive" in template.lower() or "understanding" in template.lower():
            return "Blog Post"
        elif "breaking down" in template.lower():
            return "Tutorial"
        else:
            return "Blog Post"
    
    def _deduplicate_ideas(self, ideas: List[ContentIdea]) -> List[ContentIdea]:
        """Remove duplicate ideas and sort by relevance.
        
        Args:
            ideas: List of content ideas
            
        Returns:
            Deduplicated and sorted list of ideas
        """
        seen_titles = set()
        unique_ideas = []
        
        for idea in ideas:
            if idea.title not in seen_titles:
                seen_titles.add(idea.title)
                unique_ideas.append(idea)
        
        # Sort by number of keywords (more keywords = more relevant)
        unique_ideas.sort(key=lambda x: len(x.keywords), reverse=True)
        
        return unique_ideas