#!/usr/bin/env python3
"""
Hockey Interview URL Validator
Validates YouTube URLs to ensure they are actual hockey player interviews
"""

import re
from typing import Dict, Any, List

class HockeyInterviewValidator:
    """Validates that URLs are actual hockey player interviews"""
    
    def __init__(self):
        # Hockey-related keywords
        self.hockey_keywords = [
            'hockey', 'nhl', 'nhl interview', 'player interview',
            'draft', 'combine', 'media day', 'press conference',
            'nhl draft', 'rookie', 'oilers', 'penguins', 'blackhawks',
            'ice hockey', 'hockey player'
        ]
        
        # Interview-related keywords
        self.interview_keywords = [
            'interview', 'exclusive', 'chat', 'talk', 'conversation',
            'q&a', 'qa', 'press conference', 'media day'
        ]
        
        # Non-interview patterns (to exclude)
        self.exclude_patterns = [
            'music', 'song', 'lyrics', 'video', 'clip',
            'highlight', 'goal', 'save', 'game replay'
        ]
    
    def extract_video_info(self, url: str) -> Dict[str, Any]:
        """
        Extract video ID and basic info from URL
        
        Args:
            url: YouTube URL
            
        Returns:
            Dictionary with video information
        """
        video_id = self._extract_video_id(url)
        
        return {
            "url": url,
            "video_id": video_id,
            "is_valid_youtube": video_id is not None
        }
    
    def _extract_video_id(self, url: str) -> str:
        """Extract YouTube video ID from URL"""
        patterns = [
            r'(?:youtube\.com\/watch\?v=|youtu\.be\/)([^&\n?#]+)',
            r'youtube\.com\/embed\/([^&\n?#]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        return None
    
    def validate_url(self, url: str, player_name: str = None) -> Dict[str, Any]:
        """
        Validate if URL is likely a hockey interview
        
        Args:
            url: YouTube URL to validate
            player_name: Name of player to check for
            
        Returns:
            Validation result
        """
        result = self.extract_video_info(url)
        
        if not result['is_valid_youtube']:
            return {
                "valid": False,
                "reason": "Not a valid YouTube URL",
                **result
            }
        
        # Extract keywords from URL
        url_lower = url.lower()
        
        # Check for hockey keywords
        has_hockey = any(keyword in url_lower for keyword in self.hockey_keywords)
        
        # Check for interview keywords
        has_interview = any(keyword in url_lower for keyword in self.interview_keywords)
        
        # Check for player name
        has_player = player_name and player_name.lower() in url_lower
        
        # Check for exclude patterns
        has_exclude = any(pattern in url_lower for pattern in self.exclude_patterns)
        
        # Calculate validation score
        score = 0
        if has_hockey:
            score += 1
        if has_interview:
            score += 1
        if has_player:
            score += 1
        if not has_exclude:
            score += 1
        
        valid = score >= 2 and not has_exclude
        
        return {
            "valid": valid,
            "score": score,
            "has_hockey": has_hockey,
            "has_interview": has_interview,
            "has_player": has_player,
            "has_exclude": has_exclude,
            "reason": self._get_reason(valid, has_hockey, has_interview, has_player, has_exclude),
            **result
        }
    
    def _get_reason(self, valid: bool, has_hockey: bool, 
                    has_interview: bool, has_player: bool, has_exclude: bool) -> str:
        """Get validation reason"""
        if has_exclude:
            return "URL contains excluded patterns (music, highlights, etc.)"
        if not has_hockey and not has_interview:
            return "No hockey or interview keywords found in URL"
        if valid:
            return "Likely a hockey interview"
        return "Uncertain if this is a hockey interview"

def main():
    """Test the validator"""
    validator = HockeyInterviewValidator()
    
    print("🏒 Hockey Interview URL Validator")
    print("=" * 60)
    
    # Test URLs
    test_urls = [
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",  # Rick Roll (example)
        "https://www.youtube.com/watch?v=connor-mcdavid-nhl-interview",  # Hypothetical
        "https://www.youtube.com/watch?v=sidney-crosby-press-conference",
    ]
    
    for url in test_urls:
        result = validator.validate_url(url, "Connor McDavid")
        print(f"\n🔗 URL: {url}")
        print(f"   Valid: {'✅' if result['valid'] else '❌'}")
        print(f"   Score: {result['score']}/4")
        print(f"   Reason: {result['reason']}")

if __name__ == "__main__":
    main()
