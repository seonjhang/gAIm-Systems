#!/usr/bin/env python3
"""
YouTube Transcript Extractor with Webshare Proxy Support
Extracts transcripts from YouTube videos using Webshare proxy rotation
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

try:
    from youtube_transcript_api import YouTubeTranscriptApi
    from youtube_transcript_api.proxies import WebshareProxyConfig
    from youtube_transcript_api._errors import (
        TranscriptsDisabled,
        NoTranscriptFound,
        YouTubeRequestFailed
    )
    TRANSCRIPT_API_AVAILABLE = True
except ImportError as e:
    TRANSCRIPT_API_AVAILABLE = False
    logger.warning(f"youtube-transcript-api not available: {e}")


class YouTubeTranscriptExtractor:
    """Extracts transcripts from YouTube videos with Webshare proxy support"""
    
    def __init__(self, use_proxy: bool = True):
        """
        Initialize transcript extractor
        
        Args:
            use_proxy: Whether to use Webshare proxy for IP rotation
        """
        if not TRANSCRIPT_API_AVAILABLE:
            raise ImportError("youtube-transcript-api is required")
        
        self.use_proxy = use_proxy
        self.transcript_api = None
        
        if use_proxy:
            proxy_username = os.getenv("PROXY_USERNAME")
            proxy_password = os.getenv("PROXY_PASSWORD")
            
            if proxy_username and proxy_password:
                try:
                    # Try new API format first (check if WebshareProxyConfig accepts username/password)
                    import inspect
                    sig = inspect.signature(WebshareProxyConfig.__init__)
                    params = list(sig.parameters.keys())
                    
                    if 'username' in params and 'password' in params:
                        proxy_config = WebshareProxyConfig(
                            username=proxy_username,
                            password=proxy_password
                        )
                    elif 'user' in params and 'pwd' in params:
                        proxy_config = WebshareProxyConfig(
                            user=proxy_username,
                            pwd=proxy_password
                        )
                    else:
                        # Try with positional arguments or different format
                        raise ValueError(f"Unknown WebshareProxyConfig parameters: {params}")
                    
                    self.transcript_api = YouTubeTranscriptApi(proxy_config=proxy_config)
                    logger.info("Initialized YouTube Transcript API with Webshare proxy")
                except Exception as e:
                    logger.warning(f"Could not initialize proxy ({type(e).__name__}: {e}), using direct connection")
                    self.transcript_api = YouTubeTranscriptApi()
            else:
                logger.warning("Proxy credentials not found, using direct connection")
                self.transcript_api = YouTubeTranscriptApi()
        else:
            self.transcript_api = YouTubeTranscriptApi()
            logger.info("Initialized YouTube Transcript API without proxy")
    
    def extract_transcript(self, video_id: str, video_title: Optional[str] = None,
                          video_url: Optional[str] = None, output_dir: Optional[Path] = None) -> Optional[Dict[str, Any]]:
        """
        Extract transcript from a YouTube video
        
        Args:
            video_id: YouTube video ID
            video_title: Optional video title for metadata
            video_url: Optional video URL for metadata
            output_dir: Optional directory to save transcript JSON
            
        Returns:
            Dictionary with transcript data or None if extraction failed
        """
        if not self.transcript_api:
            logger.error("Transcript API not initialized")
            return None
        
        try:
            # List available transcripts
            transcript_list = self.transcript_api.list(video_id)
            
            # Try to get English transcript first, then any available
            transcript = None
            try:
                transcript = transcript_list.find_transcript(['en'])
            except:
                # Try any available transcript
                try:
                    transcript = transcript_list.find_generated_transcript(['en'])
                except:
                    # Get first available transcript
                    available = list(transcript_list)
                    if available:
                        transcript = available[0]
            
            if not transcript:
                logger.warning(f"No transcript found for video {video_id}")
                return None
            
            # Fetch transcript data
            transcript_data = transcript.fetch()
            
            # Combine all text
            full_text = ' '.join([item.text for item in transcript_data])
            
            result = {
                "video_id": video_id,
                "video_title": video_title or "Unknown",
                "video_url": video_url or f"https://www.youtube.com/watch?v={video_id}",
                "transcript": [{"text": item.text, "start": item.start, "duration": item.duration} for item in transcript_data],
                "full_text": full_text,
                "word_count": len(full_text.split()),
                "language": transcript.language_code,
                "is_generated": transcript.is_generated,
                "item_count": len(transcript_data),
                "extracted_at": datetime.now().isoformat()
            }
            
            # Save to file if output_dir is provided
            if output_dir:
                output_dir = Path(output_dir)
                output_dir.mkdir(parents=True, exist_ok=True)
                
                player_slug = video_title.replace(' ', '_')[:50] if video_title else video_id
                filename = f"{player_slug}_{video_id}_transcript.json"
                filepath = output_dir / filename
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(result, f, indent=2, ensure_ascii=False)
                
                logger.info(f"Transcript saved to: {filepath}")
            
            return result
            
        except TranscriptsDisabled:
            logger.warning(f"Transcripts are disabled for video {video_id}")
            return None
        except NoTranscriptFound:
            logger.warning(f"No transcript found for video {video_id}")
            return None
        except YouTubeRequestFailed as e:
            logger.error(f"YouTube request failed for video {video_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error extracting transcript for video {video_id}: {type(e).__name__}: {e}")
            return None


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python youtube_transcript_extractor.py <video_id>")
        sys.exit(1)
    
    video_id = sys.argv[1]
    
    extractor = YouTubeTranscriptExtractor()
    result = extractor.extract_transcript(video_id)
    
    if result:
        print(f"✅ Extracted {result['word_count']} words")
        print(f"Language: {result['language']}")
        print(f"Generated: {result['is_generated']}")
        print(f"\nFirst 500 characters:")
        print(result['full_text'][:500])
    else:
        print("❌ Failed to extract transcript")

