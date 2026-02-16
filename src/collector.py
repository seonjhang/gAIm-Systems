#!/usr/bin/env python3
"""
Hockey Player Interview Collection Agent
Collects interview data from web sources (NHL, TSN, Sportsnet, ESPN) and YouTube
"""

import os
import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path
from dotenv import load_dotenv
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import specialized parsers
from nhl_article_parser import NHLArticleParser
try:
    from youtube_interview_finder import YouTubeInterviewFinder
    YOUTUBE_AVAILABLE = True
except ImportError:
    YOUTUBE_AVAILABLE = False
    logger.warning("YouTube interview finder not available")

try:
    from youtube_transcript_extractor import YouTubeTranscriptExtractor
    TRANSCRIPT_AVAILABLE = True
except ImportError:
    TRANSCRIPT_AVAILABLE = False
    logger.warning("YouTube transcript extractor not available")

try:
    from player_speech_extractor import PlayerSpeechExtractor
    SPEECH_EXTRACTOR_AVAILABLE = True
except ImportError:
    SPEECH_EXTRACTOR_AVAILABLE = False
    logger.warning("Player speech extractor not available")

class HockeyInterviewCollector:
    """Main agent for collecting hockey player interview data from web"""
    
    def __init__(self, use_youtube: bool = True, extract_transcripts: bool = True, 
                 extract_player_speech: bool = True, use_proxy: bool = True):
        """
        Initialize the Hockey Interview Collector
        
        Args:
            use_youtube: Whether to use YouTube as a source
            extract_transcripts: Whether to extract transcripts from YouTube videos
            extract_player_speech: Whether to extract only player speech from transcripts
            use_proxy: Whether to use Webshare proxy for transcript extraction
        """
        
        # Create data folders if they don't exist
        self.raw_data_dir = Path("data/raw")
        self.processed_data_dir = Path("data/processed")
        self.transcript_dir = self.raw_data_dir / "transcript"
        self.player_speech_dir = self.raw_data_dir / "player_speech"
        self.raw_data_dir.mkdir(parents=True, exist_ok=True)
        self.processed_data_dir.mkdir(parents=True, exist_ok=True)
        self.transcript_dir.mkdir(parents=True, exist_ok=True)
        self.player_speech_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize specialized parsers
        self.nhl_parser = NHLArticleParser()
        
        # Initialize YouTube finder if available
        self.youtube_finder = None
        if use_youtube and YOUTUBE_AVAILABLE:
            try:
                self.youtube_finder = YouTubeInterviewFinder(strict=False)
                logger.info("YouTube interview finder initialized")
            except Exception as e:
                logger.warning(f"YouTube finder not available: {e}")
                self.youtube_finder = None
        
        # Initialize transcript extractor if available
        self.transcript_extractor = None
        if extract_transcripts and TRANSCRIPT_AVAILABLE:
            try:
                self.transcript_extractor = YouTubeTranscriptExtractor(use_proxy=use_proxy)
                logger.info("YouTube transcript extractor initialized")
            except Exception as e:
                logger.warning(f"Transcript extractor not available: {e}")
                self.transcript_extractor = None
        
        # Initialize player speech extractor if available
        self.speech_extractor = None
        if extract_player_speech and SPEECH_EXTRACTOR_AVAILABLE:
            try:
                self.speech_extractor = PlayerSpeechExtractor()
                logger.info("Player speech extractor initialized")
            except Exception as e:
                logger.warning(f"Player speech extractor not available: {e}")
                self.speech_extractor = None
        
        # Store flags
        self.extract_transcripts = extract_transcripts
        self.extract_player_speech = extract_player_speech
    
    def collect_interviews(self, player_name: str, include_youtube: bool = True, youtube_top_n: int = 5) -> Dict[str, Any]:
        """
        Main collection method - collects interviews from multiple sources
        
        Args:
            player_name: Name of the hockey player
            include_youtube: Whether to include YouTube interviews
            youtube_top_n: Number of YouTube interviews to collect
            
        Returns:
            Collection results with interview data
        """
        logger.info(f"Starting interview collection for: {player_name}")
        
        results = {
            "player_name": player_name,
            "collection_date": datetime.now().isoformat(),
            "interviews": [],
            "sources": {
                "nhl_articles": 0,
                "youtube_videos": 0,
                "other_web": 0
            }
        }
        
        # 1. Collect from NHL.com (priority source)
        logger.info("Collecting from NHL.com...")
        nhl_interviews = self._collect_from_nhl(player_name)
        if nhl_interviews:
            results["interviews"].extend(nhl_interviews)
            results["sources"]["nhl_articles"] = len(nhl_interviews)
            logger.info(f"✅ Found {len(nhl_interviews)} NHL.com interviews")
        
        # 2. Collect from YouTube (if available)
        if include_youtube and self.youtube_finder:
            logger.info("Collecting from YouTube...")
            try:
                youtube_interviews = self._collect_from_youtube(player_name, youtube_top_n)
                if youtube_interviews:
                    results["interviews"].extend(youtube_interviews)
                    results["sources"]["youtube_videos"] = len(youtube_interviews)
                    logger.info(f"✅ Found {len(youtube_interviews)} YouTube interviews")
            except Exception as e:
                logger.warning(f"YouTube collection failed: {e}")
        
        # 3. Collect from other web sources (fallback)
        if len(results["interviews"]) < 5:
            logger.info("Collecting from other web sources...")
            other_interviews = self._scrape_interviews_from_web(player_name)
            if other_interviews:
                results["interviews"].extend(other_interviews)
                results["sources"]["other_web"] = len(other_interviews)
                logger.info(f"✅ Found {len(other_interviews)} other web interviews")
        
        logger.info(f"Collection complete: {len(results.get('interviews', []))} total interviews found")
        return results
    
    def _collect_from_nhl(self, player_name: str, max_articles: int = 10) -> List[Dict[str, Any]]:
        """
        Collect interview content from NHL.com articles
        
        Args:
            player_name: Name of the player
            max_articles: Maximum number of articles to process
            
        Returns:
            List of interview data from NHL.com
        """
        interviews = []
        
        # Search for NHL.com draft articles
        article_urls = self.nhl_parser.search_nhl_draft_articles(player_name, max_results=max_articles)
        
        logger.info(f"Found {len(article_urls)} NHL.com articles for {player_name}")
        
        for url in article_urls:
            try:
                logger.info(f"  → Parsing: {url}")
                parsed = self.nhl_parser.parse_article(url, player_name)
                
                if parsed and parsed.get("interview_content"):
                    interviews.append({
                        "source": "NHL.com",
                        "source_url": url,
                        "title": parsed.get("title", "No title"),
                        "published_date": parsed.get("published_date"),
                        "content": parsed.get("interview_content"),
                        "quotes": parsed.get("quotes", []),
                        "quote_count": parsed.get("quote_count", 0),
                        "word_count": parsed.get("word_count", 0),
                        "type": "nhl_article_interview",
                        "interview_segments": parsed.get("interview_segments", []),
                        "player_statements": parsed.get("player_statements", [])
                    })
                    logger.info(f"  ✅ Extracted {parsed.get('quote_count', 0)} quotes, {parsed.get('word_count', 0)} words")
                
            except Exception as e:
                logger.error(f"Error parsing NHL article {url}: {e}")
                continue
        
        return interviews
    
    def _collect_from_youtube(self, player_name: str, top_n: int = 5) -> List[Dict[str, Any]]:
        """
        Collect interview videos from YouTube and extract transcripts
        
        Args:
            player_name: Name of the player
            top_n: Number of videos to collect
            
        Returns:
            List of YouTube interview data with transcripts if extracted
        """
        interviews = []
        
        try:
            youtube_results = self.youtube_finder.find_top_interviews(player_name, top_n=top_n)
            
            for result in youtube_results:
                video_id = result.get("videoId")
                video_url = result.get("url")
                video_title = result.get("title", "No title")
                
                interview_data = {
                    "source": "YouTube",
                    "source_url": video_url,
                    "title": video_title,
                    "published_date": result.get("publishedAt"),
                    "channel": result.get("channel"),
                    "video_id": video_id,
                    "score": result.get("score", 0),
                    "type": "youtube_video_interview",
                    "content": f"YouTube video: {video_title}",
                    "word_count": 0,
                    "transcript_extracted": False,
                    "player_speech_extracted": False
                }
                
                # Extract transcript if enabled
                transcript_data = None
                if self.extract_transcripts and self.transcript_extractor and video_id:
                    try:
                        logger.info(f"  → Extracting transcript for: {video_title[:50]}...")
                        transcript_data = self.transcript_extractor.extract_transcript(
                            video_id,
                            video_title=video_title,
                            video_url=video_url,
                            output_dir=self.transcript_dir
                        )
                        
                        if transcript_data:
                            interview_data["transcript_extracted"] = True
                            interview_data["transcript"] = transcript_data.get("full_text", "")
                            interview_data["transcript_word_count"] = transcript_data.get("word_count", 0)
                            interview_data["word_count"] = transcript_data.get("word_count", 0)
                            interview_data["transcript_segments"] = transcript_data.get("transcript", [])
                            logger.info(f"  ✅ Extracted transcript: {transcript_data.get('word_count', 0)} words")
                    except Exception as e:
                        logger.warning(f"  ❌ Failed to extract transcript for {video_id}: {e}")
                
                # Extract player speech if transcript was extracted and enabled
                if (self.extract_player_speech and self.speech_extractor and 
                    transcript_data and interview_data.get("transcript_extracted")):
                    try:
                        logger.info(f"  → Extracting player speech from transcript...")
                        player_speech_data = self.speech_extractor.extract_player_speech(
                            transcript_data,
                            player_name,
                            video_id=video_id,
                            video_title=video_title,
                            video_url=video_url,
                            output_dir=self.player_speech_dir
                        )
                        
                        if player_speech_data:
                            interview_data["player_speech_extracted"] = True
                            interview_data["player_speech"] = player_speech_data.get("player_speech_text", "")
                            interview_data["player_speech_word_count"] = player_speech_data.get("word_count", 0)
                            interview_data["player_speech_segments"] = player_speech_data.get("player_speech", [])
                            interview_data["word_count"] = player_speech_data.get("word_count", 0)  # Update to player speech count
                            interview_data["reduction_ratio"] = player_speech_data.get("extraction_metadata", {}).get("reduction_ratio", 0)
                            logger.info(f"  ✅ Extracted player speech: {player_speech_data.get('word_count', 0)} words "
                                      f"(reduced from {player_speech_data.get('original_word_count', 0)})")
                    except Exception as e:
                        logger.warning(f"  ❌ Failed to extract player speech: {e}")
                
                interviews.append(interview_data)
            
        except Exception as e:
            logger.error(f"Error collecting from YouTube: {e}")
        
        return interviews
    
    def _scrape_interviews_from_web(self, player_name: str) -> List[Dict[str, Any]]:
        """
        Scrape interview content from various web sources
        
        Args:
            player_name: Name of the hockey player
            
        Returns:
            List of scraped interview data
        """
        scraped_data = []
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        
        # List of sources to scrape from
        sources = [
            {
                "name": "NHL",
                "search_url": f"https://www.nhl.com/news/search-results?searchText={player_name.replace(' ', '%20')}",
                "base_url": "https://www.nhl.com"
            },
            {
                "name": "TSN",
                "search_url": f"https://www.tsn.ca/search?query={player_name.replace(' ', '+')}+interview",
                "base_url": "https://www.tsn.ca"
            },
            {
                "name": "Sportsnet",
                "search_url": f"https://www.sportsnet.ca/search?query={player_name.replace(' ', '+')}+interview",
                "base_url": "https://www.sportsnet.ca"
            },
            {
                "name": "ESPN",
                "search_url": f"https://www.espn.com/search/results?q={player_name.replace(' ', '+')}+interview",
                "base_url": "https://www.espn.com"
            }
        ]
        
        for source in sources:
            try:
                logger.info(f"Scraping from {source['name']}...")
                response = requests.get(source['search_url'], headers=headers, timeout=15)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Find article links
                links = soup.find_all('a', href=True)
                article_urls = []
                
                for link in links:
                    href = link.get('href', '')
                    link_text = link.get_text().lower()
                    
                    # Look for interview-related content
                    if any(keyword in link_text for keyword in ['interview', 'talks', 'discusses', 'exclusive']):
                        if any(word in link_text for word in player_name.lower().split()):
                            if href.startswith('http'):
                                article_urls.append(href)
                            elif href.startswith('/'):
                                article_urls.append(f"{source['base_url']}{href}")
                
                # Remove duplicates
                article_urls = list(dict.fromkeys(article_urls))
                
                # Scrape content from found URLs
                for url in article_urls[:3]:  # Limit to 3 per source
                    try:
                        logger.info(f"  → Scraping: {url}")
                        content_response = requests.get(url, headers=headers, timeout=10)
                        content_response.raise_for_status()
                        
                        content_soup = BeautifulSoup(content_response.text, 'html.parser')
                        
                        # Extract text content
                        article_content = None
                        
                        # Try common article selectors
                        for selector in ['article', '.article-body', '.story-body', '.content', 'main']:
                            elements = content_soup.select(selector)
                            if elements:
                                article_content = elements[0].get_text(separator=' ', strip=True)
                                break
                        
                        # Fallback to all text
                        if not article_content:
                            article_content = content_soup.get_text(separator=' ', strip=True)
                        
                        # Filter meaningful content
                        if len(article_content) > 200 and player_name.lower() in article_content.lower():
                            # Clean up the content
                            article_content = ' '.join(article_content.split())
                            
                            scraped_data.append({
                                "source": source['name'],
                                "source_url": url,
                                "title": content_soup.title.string if content_soup.title else "No title",
                                "content": article_content[:10000],  # Limit to 10000 chars
                                "type": "web_interview",
                                "word_count": len(article_content.split())
                            })
                            logger.info(f"  ✅ Scraped {len(article_content.split())} words from {source['name']}")
                            
                            # Stop after finding a good article from this source
                            break
                            
                    except Exception as e:
                        logger.debug(f"Failed to scrape {url}: {e}")
                        continue
                        
            except Exception as e:
                logger.warning(f"Failed to scrape from {source['name']}: {e}")
                continue
        
        logger.info(f"Total interviews scraped: {len(scraped_data)}")
        return scraped_data
    
    def save_results(self, results: Dict[str, Any]):
        """
        Save collection results
        
        Args:
            results: Collection results dictionary
        """
        player_slug = results['player_name'].replace(' ', '_')
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save raw data
        filename = f"{player_slug}_{timestamp}.json"
        raw_filepath = self.raw_data_dir / filename
        
        with open(raw_filepath, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Raw data saved to: {raw_filepath}")
        
        # Save processed data (interviews.jsonl)
        processed_file = self.processed_data_dir / "interviews.jsonl"
        
        with open(processed_file, 'a', encoding='utf-8') as f:
            for interview in results.get('interviews', []):
                processed_interview = {
                    "player_name": results['player_name'],
                    "collection_date": results['collection_date'],
                    "source": interview.get('source', ''),
                    "source_url": interview.get('source_url', ''),
                    "title": interview.get('title', ''),
                    "content": interview.get('content', ''),
                    "word_count": interview.get('word_count', 0)
                }
                f.write(json.dumps(processed_interview, ensure_ascii=False) + '\n')
        
        logger.info(f"Processed data saved to: {processed_file}")
        return raw_filepath
    
    def export_to_structured_file(self, player_name: Optional[str] = None, 
                                 use_player_speech: bool = True,
                                 output_file: Optional[Path] = None) -> Path:
        """
        Export all transcripts/player speech to a structured text file (TSV format)
        with player_name and text columns
        
        Args:
            player_name: Optional player name to filter (if None, exports all players)
            use_player_speech: If True, use player_speech; otherwise use transcript
            output_file: Optional output file path (defaults to processed_data_dir/interviews_structured.txt)
            
        Returns:
            Path to the exported file
        """
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            if player_name:
                player_slug = player_name.replace(' ', '_')
                output_file = self.processed_data_dir / f"{player_slug}_interviews_{timestamp}.txt"
            else:
                output_file = self.processed_data_dir / f"all_interviews_{timestamp}.txt"
        
        output_file = Path(output_file)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Collect all data
        all_data = []
        
        # Process player_speech files if available and requested
        if use_player_speech and self.player_speech_dir.exists():
            for speech_file in self.player_speech_dir.glob("*_player_speech.json"):
                if player_name:
                    # Check if file matches player name
                    file_stem = speech_file.stem
                    player_slug = player_name.replace(' ', '_')
                    if not file_stem.startswith(player_slug):
                        continue
                
                try:
                    with open(speech_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    player_name_from_file = data.get('player_name', '')
                    text = data.get('player_speech_text', '')
                    
                    if text:
                        all_data.append({
                            'player_name': player_name_from_file,
                            'text': text,
                            'source': 'player_speech',
                            'video_id': data.get('video_id', ''),
                            'word_count': data.get('word_count', 0)
                        })
                except Exception as e:
                    logger.warning(f"Error reading {speech_file}: {e}")
                    continue
        
        # Process transcript files if player_speech not available or not requested
        if (not use_player_speech or not all_data) and self.transcript_dir.exists():
            for transcript_file in self.transcript_dir.glob("*_transcript.json"):
                if player_name:
                    # Check if file matches player name
                    file_stem = transcript_file.stem
                    player_slug = player_name.replace(' ', '_')
                    if not file_stem.startswith(player_slug):
                        continue
                
                try:
                    with open(transcript_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    player_name_from_file = data.get('player_name', '')
                    text = data.get('full_text', '')
                    
                    if text:
                        all_data.append({
                            'player_name': player_name_from_file,
                            'text': text,
                            'source': 'transcript',
                            'video_id': data.get('video_id', ''),
                            'word_count': data.get('word_count', 0)
                        })
                except Exception as e:
                    logger.warning(f"Error reading {transcript_file}: {e}")
                    continue
        
        # Write to structured file
        with open(output_file, 'w', encoding='utf-8') as f:
            # Write header
            f.write("player_name\ttext\n")
            
            # Write each entry
            for entry in all_data:
                player_name_str = entry['player_name']
                text = entry['text']
                
                # Clean text: remove newlines and tabs, replace with spaces
                text = ' '.join(text.split())
                
                # Skip if no text
                if not text:
                    continue
                
                # Escape tabs and newlines in text
                text = text.replace('\t', ' ').replace('\n', ' ').replace('\r', ' ')
                player_name_str = player_name_str.replace('\t', ' ').replace('\n', ' ').replace('\r', ' ')
                
                # Write row
                f.write(f"{player_name_str}\t{text}\n")
        
        logger.info(f"Structured text file saved to: {output_file} ({len(all_data)} entries)")
        return output_file

def main():
    """Main CLI function"""
    import sys
    
    print("🏒 Hockey Player Interview Collection Agent")
    print("=" * 60)
    
    # Get player name from command line argument
    if len(sys.argv) < 2:
        print("Usage: python hockey_interview_collector.py <player_name>")
        print("Example: python hockey_interview_collector.py 'Connor McDavid'")
        return
    
    player_name = sys.argv[1]
    
    # Initialize collector
    collector = HockeyInterviewCollector()
    
    # Collect interviews
    print(f"\n🔍 Collecting interviews for: {player_name}")
    results = collector.collect_interviews(player_name)
    
    # Display results
    print(f"\n📊 COLLECTION RESULTS")
    print("=" * 60)
    print(f"Player: {results['player_name']}")
    print(f"Total Interviews Found: {len(results.get('interviews', []))}")
    
    # Show source breakdown
    if 'sources' in results:
        print(f"\n📈 Source Breakdown:")
        print(f"   NHL.com Articles: {results['sources'].get('nhl_articles', 0)}")
        print(f"   YouTube Videos: {results['sources'].get('youtube_videos', 0)}")
        print(f"   Other Web Sources: {results['sources'].get('other_web', 0)}")
    
    if results.get('interviews'):
        print(f"\n✅ Interviews Collected:")
        for i, interview in enumerate(results['interviews'], 1):
            print(f"\n{i}. {interview.get('title', 'No title')}")
            print(f"   Source: {interview.get('source', 'N/A')}")
            print(f"   Type: {interview.get('type', 'N/A')}")
            
            # Show quote count for NHL articles
            if interview.get('type') == 'nhl_article_interview':
                print(f"   Quotes: {interview.get('quote_count', 0)}")
            
            # Show score for YouTube videos
            if interview.get('type') == 'youtube_video_interview':
                print(f"   Score: {interview.get('score', 0)}")
                print(f"   Channel: {interview.get('channel', 'N/A')}")
            
            print(f"   Words: {interview.get('word_count', 0)}")
            print(f"   URL: {interview.get('source_url', 'N/A')}")
            
            # Show sample quotes for NHL articles
            if interview.get('type') == 'nhl_article_interview' and interview.get('quotes'):
                print(f"   Sample Quote: \"{interview['quotes'][0][:100]}...\"")
    
    # Save results
    filename = collector.save_results(results)
    print(f"\n💾 Results saved to: {filename}")
    print(f"📝 Processed data appended to: data/processed/interviews.jsonl")
    
    # Export to structured text file
    structured_file = collector.export_to_structured_file(player_name=player_name, use_player_speech=True)
    print(f"📄 Structured text file saved to: {structured_file}")

if __name__ == "__main__":
    main()