#!/usr/bin/env python3
"""
NHL.com Article Parser
Specialized parser for extracting interview content from NHL.com articles
"""

import re
import logging
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
import requests

logger = logging.getLogger(__name__)


class NHLArticleParser:
    """Parses NHL.com articles to extract interview content"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
    
    def parse_article(self, url: str, player_name: str) -> Optional[Dict[str, Any]]:
        """
        Parse an NHL.com article and extract interview content
        
        Args:
            url: NHL.com article URL
            player_name: Name of the player
            
        Returns:
            Dictionary with parsed interview data or None if parsing fails
        """
        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract article metadata
            title = self._extract_title(soup)
            published_date = self._extract_published_date(soup)
            
            # Extract main article content
            article_body = self._extract_article_body(soup)
            
            # Extract interview quotes
            quotes = self._extract_quotes(article_body, player_name)
            
            # Extract interview segments (Q&A style)
            interview_segments = self._extract_interview_segments(article_body, player_name)
            
            # Extract player statements
            player_statements = self._extract_player_statements(article_body, player_name)
            
            # Combine all interview content
            interview_content = self._combine_interview_content(
                quotes, interview_segments, player_statements
            )
            
            if not interview_content:
                logger.warning(f"No interview content found in {url}")
                return None
            
            return {
                "url": url,
                "title": title,
                "published_date": published_date,
                "article_body": article_body,
                "quotes": quotes,
                "interview_segments": interview_segments,
                "player_statements": player_statements,
                "interview_content": interview_content,
                "word_count": len(interview_content.split()),
                "quote_count": len(quotes),
                "source": "NHL.com"
            }
            
        except Exception as e:
            logger.error(f"Error parsing NHL article {url}: {e}")
            return None
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract article title"""
        # Try multiple selectors for title
        title_selectors = [
            'h1.article-headline',
            'h1',
            '.article-title',
            'title'
        ]
        
        for selector in title_selectors:
            element = soup.select_one(selector)
            if element:
                title = element.get_text(strip=True)
                if title and len(title) > 10:  # Valid title
                    return title
        
        return "No title found"
    
    def _extract_published_date(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract published date"""
        # Try multiple selectors for date
        date_selectors = [
            'time[datetime]',
            '.article-date',
            '.published-date',
            '[class*="date"]'
        ]
        
        for selector in date_selectors:
            element = soup.select_one(selector)
            if element:
                date_attr = element.get('datetime') or element.get_text(strip=True)
                if date_attr:
                    return date_attr
        
        return None
    
    def _extract_article_body(self, soup: BeautifulSoup) -> str:
        """Extract main article body content"""
        # Try multiple selectors for article body
        body_selectors = [
            'article .article-body',
            'article .story-body',
            '.article-content',
            '.story-content',
            'article',
            'main'
        ]
        
        for selector in body_selectors:
            element = soup.select_one(selector)
            if element:
                # Remove script and style elements
                for script in element(["script", "style", "nav", "header", "footer"]):
                    script.decompose()
                
                text = element.get_text(separator=' ', strip=True)
                if text and len(text) > 200:  # Valid article content
                    return text
        
        # Fallback: get all text
        return soup.get_text(separator=' ', strip=True)
    
    def _extract_quotes(self, text: str, player_name: str) -> List[str]:
        """Extract quoted statements from article"""
        quotes = []
        
        # Pattern 1: Text in double quotes
        double_quote_pattern = r'"([^"]{20,500})"'
        matches = re.findall(double_quote_pattern, text)
        
        for match in matches:
            # Check if quote mentions player or is likely from player
            if player_name.lower() in match.lower() or self._is_player_quote(match):
                quotes.append(match.strip())
        
        # Pattern 2: Text in single quotes (less common)
        single_quote_pattern = r"'([^']{20,500})'"
        matches = re.findall(single_quote_pattern, text)
        
        for match in matches:
            if player_name.lower() in match.lower() or self._is_player_quote(match):
                quotes.append(match.strip())
        
        # Remove duplicates while preserving order
        seen = set()
        unique_quotes = []
        for quote in quotes:
            quote_lower = quote.lower()
            if quote_lower not in seen:
                seen.add(quote_lower)
                unique_quotes.append(quote)
        
        return unique_quotes
    
    def _is_player_quote(self, text: str) -> bool:
        """Check if text is likely a player quote (first person, interview style)"""
        # First person indicators
        first_person_indicators = [
            r'\bI\s+(was|am|have|had|think|feel|said|told|went|got|did|want|need|hope)',
            r'\bwe\s+(were|are|have|had|think|feel|said|went|got|did)',
            r'\bmy\s+(team|coach|family|goal|dream|plan)',
            r'\bit\s+(was|is|felt|feels|seems)',
        ]
        
        text_lower = text.lower()
        for pattern in first_person_indicators:
            if re.search(pattern, text_lower):
                return True
        
        return False
    
    def _extract_interview_segments(self, text: str, player_name: str) -> List[Dict[str, str]]:
        """Extract Q&A style interview segments"""
        segments = []
        
        # Pattern: Look for "Player said:" or "Player told reporters:" followed by quote
        patterns = [
            # Match: <Player> said: "..."
            rf'{re.escape(player_name)}\s+(said|told|explained|noted|added|mentioned|stated|revealed)[:,\s]+"([^"]{{20,500}})"',
            # Match: <Player> said: '...'
            rf"{re.escape(player_name)}\s+(said|told|explained|noted|added|mentioned|stated|revealed)[:,\s]+'([^']{{20,500}})'",
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                segments.append({
                    "context": match.group(1),  # said, told, etc.
                    "quote": match.group(2)
                })
        
        return segments
    
    def _extract_player_statements(self, text: str, player_name: str) -> List[str]:
        """Extract statements attributed to the player"""
        statements = []
        
        # Look for paragraphs that mention player and contain quotes or first-person statements
        paragraphs = text.split('\n\n')
        
        for para in paragraphs:
            if player_name.lower() in para.lower():
                # Check if paragraph contains quotes or first-person statements
                if '"' in para or "'" in para or self._is_player_quote(para):
                    # Extract the relevant part
                    # Try to find the quote or statement
                    quote_match = re.search(r'"([^"]{20,500})"', para)
                    if quote_match:
                        statements.append(quote_match.group(1).strip())
                    elif self._is_player_quote(para):
                        # Extract first-person statement
                        statements.append(para.strip())
        
        return statements
    
    def _combine_interview_content(self, quotes: List[str], 
                                  segments: List[Dict[str, str]], 
                                  statements: List[str]) -> str:
        """Combine all interview content into a single text"""
        content_parts = []
        
        # Add quotes
        for quote in quotes:
            content_parts.append(f'"{quote}"')
        
        # Add interview segments
        for segment in segments:
            content_parts.append(f"{segment['context']}: \"{segment['quote']}\"")
        
        # Add player statements
        for statement in statements:
            if statement not in quotes:  # Avoid duplicates
                content_parts.append(statement)
        
        return '\n\n'.join(content_parts)
    
    def search_nhl_draft_articles(self, player_name: str, max_results: int = 10) -> List[str]:
        """
        Search NHL.com for draft-related articles about a player
        
        Args:
            player_name: Name of the player
            max_results: Maximum number of URLs to return
            
        Returns:
            List of article URLs
        """
        urls = []
        
        # Search NHL.com draft section
        search_urls = [
            f"https://www.nhl.com/news/topic/nhl-draft/",
            f"https://www.nhl.com/news/search-results?searchText={player_name.replace(' ', '%20')}",
        ]
        
        for search_url in search_urls:
            try:
                response = self.session.get(search_url, timeout=15)
                if response.status_code != 200:
                    continue
                
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Find article links
                article_links = soup.find_all('a', href=True)
                
                for link in article_links:
                    href = link.get('href', '')
                    link_text = link.get_text().lower()
                    
                    # Check if it's a draft article about the player
                    if any(word in link_text for word in player_name.lower().split()):
                        if '/news/' in href or '/topic/nhl-draft/' in href:
                            if href.startswith('http'):
                                full_url = href
                            elif href.startswith('/'):
                                full_url = f"https://www.nhl.com{href}"
                            else:
                                continue
                            
                            if full_url not in urls:
                                urls.append(full_url)
                                
                            if len(urls) >= max_results:
                                break
                
                if len(urls) >= max_results:
                    break
                    
            except Exception as e:
                logger.error(f"Error searching NHL.com: {e}")
                continue
        
        return urls[:max_results]

