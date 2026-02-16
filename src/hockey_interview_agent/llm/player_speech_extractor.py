#!/usr/bin/env python3
"""
Player Speech Extractor
Uses GPT-4o-mini to extract only the player's speech from interview transcripts
Filters out interviewer questions and other people's speech
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
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.error("openai library not installed. Install with: pip install openai")


class PlayerSpeechExtractor:
    """Extracts only player's speech from interview transcripts using GPT-4o-mini"""
    
    def __init__(self, model: str = "gpt-4o-mini", api_key: Optional[str] = None):
        """
        Initialize player speech extractor
        
        Args:
            model: OpenAI model to use (default: gpt-4o-mini)
            api_key: Optional OpenAI API key (defaults to OPENAI_API_KEY env var)
        """
        if not OPENAI_AVAILABLE:
            raise ImportError("openai library is required. Install with: pip install openai")
        
        self.model = model
        api_key = api_key or os.getenv("OPENAI_API_KEY")
        
        if not api_key:
            raise ValueError("OPENAI_API_KEY is required. Set it in your environment or .env file.")
        
        self.client = OpenAI(api_key=api_key)
        logger.info(f"Initialized PlayerSpeechExtractor with model: {model}")
    
    def extract_player_speech(self, transcript_data: Dict[str, Any], player_name: str,
                              video_id: Optional[str] = None, video_title: Optional[str] = None,
                              video_url: Optional[str] = None, output_dir: Optional[Path] = None) -> Optional[Dict[str, Any]]:
        """
        Extract only player's speech from transcript data
        
        Args:
            transcript_data: Dictionary with transcript data (from YouTubeTranscriptExtractor)
            player_name: Name of the player
            video_id: Optional video ID for metadata
            video_title: Optional video title for metadata
            video_url: Optional video URL for metadata
            output_dir: Optional directory to save extracted speech JSON
            
        Returns:
            Dictionary with extracted player speech or None if extraction failed
        """
        full_text = transcript_data.get("full_text", "")
        transcript_segments = transcript_data.get("transcript", [])
        
        if not full_text:
            logger.warning("No transcript text found")
            return {
                "player_name": player_name,
                "player_speech": [],
                "player_speech_text": "",
                "word_count": 0,
                "original_word_count": transcript_data.get("word_count", 0),
                "extraction_metadata": {
                    "model": self.model,
                    "extracted_at": datetime.now().isoformat()
                }
            }
        
        logger.info(f"Extracting player speech for {player_name} from {len(transcript_segments)} segments")
        
        # Use GPT to identify player speech
        player_segments = self._identify_player_segments(
            transcript_segments, 
            player_name,
            full_text
        )
        
        # Post-process: refine and connect adjacent segments
        player_segments = self._post_process_segments(
            player_segments,
            transcript_segments,
            player_name
        )
        
        # Combine player speech
        player_speech_text = ' '.join([seg['text'] for seg in player_segments])
        
        result = {
            "player_name": player_name,
            "player_speech": player_segments,
            "player_speech_text": player_speech_text,
            "word_count": len(player_speech_text.split()),
            "original_word_count": transcript_data.get("word_count", 0),
            "segment_count": len(player_segments),
            "video_id": video_id or transcript_data.get("video_id"),
            "video_title": video_title or transcript_data.get("video_title"),
            "video_url": video_url or transcript_data.get("video_url"),
            "extraction_metadata": {
                "model": self.model,
                "extracted_at": datetime.now().isoformat(),
                "reduction_ratio": len(player_segments) / len(transcript_segments) if transcript_segments else 0
            }
        }
        
        # Save to file if output_dir is provided
        if output_dir:
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
            
            player_slug = player_name.replace(' ', '_')
            video_id_str = video_id or transcript_data.get("video_id", "unknown")
            filename = f"{player_slug}_{video_id_str}_player_speech.json"
            filepath = output_dir / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Player speech saved to: {filepath}")
        
        return result
    
    def _identify_player_segments(self, transcript_segments: List[Dict[str, Any]], 
                                  player_name: str, full_text: str) -> List[Dict[str, Any]]:
        """
        Use GPT-4o-mini to identify which segments are player speech
        
        Args:
            transcript_segments: List of transcript segments with text, start, duration
            player_name: Name of the player
            full_text: Full transcript text
            
        Returns:
            List of segments that are player speech
        """
        # Try full transcript first if not too long (better context)
        # Increased limit for better context
        if len(transcript_segments) <= 200:
            try:
                return self._process_full_transcript(transcript_segments, player_name)
            except Exception as e:
                logger.warning(f"Full transcript processing failed, using chunks: {e}")
        
        # Process in chunks for longer transcripts with overlap for better context
        chunk_size = 80  # Increased chunk size for more context
        overlap = 10  # Overlap between chunks to avoid missing segments at boundaries
        all_player_segments = []
        
        for i in range(0, len(transcript_segments), chunk_size - overlap):
            # Create chunk with overlap
            chunk_start = max(0, i - overlap) if i > 0 else 0
            chunk_end = min(len(transcript_segments), i + chunk_size)
            chunk = transcript_segments[chunk_start:chunk_end]
            chunk_offset = chunk_start  # Offset for index calculation
            
            # Format segments for GPT with local and global indices
            segments_text = "\n".join([
                f"[Local:{j} Global:{chunk_offset+j}] {seg.get('text', '')}" 
                for j, seg in enumerate(chunk)
            ])
            
            # Add context from previous chunk if available
            context_text = ""
            if chunk_start > 0 and len(all_player_segments) > 0:
                # Show last few segments from previous chunk for context
                prev_segments = transcript_segments[max(0, chunk_start-5):chunk_start]
                context_text = "\nPrevious context:\n" + "\n".join([
                    f"[{k}] {seg.get('text', '')}" 
                    for k, seg in enumerate(prev_segments, start=chunk_start-5)
                ]) + "\n\n"
            
            system_prompt = f"""You are an expert at analyzing interview transcripts to identify when a specific person is speaking.

Your task: Identify which transcript segments are spoken by {player_name} (the hockey player being interviewed).

CRITICAL RULES - Be INCLUSIVE of player speech:
1. EXCLUDE only clear questions:
   - Questions ending with "?"
   - Questions starting with "Did you", "What do you", "How do you", "Why", "When", "Where"
   - Questions like "Are you...", "Have you...", "Will you..."
   - Interviewer statements like "Tell us about...", "Walk us through..."

2. INCLUDE all player speech (be generous):
   - First-person statements ("I", "we", "my", "me", "I'm", "I've", "I'll")
   - ALL answers to questions (even short ones like "Yeah", "No", "I think so", "Right")
   - Personal experiences, thoughts, feelings
   - Statements about game, team, career
   - Continuation phrases ("you know", "um", "uh" - part of player's natural speech)
   - Short responses and confirmations
   - Any statement that sounds like a response

3. When in doubt, INCLUDE the segment (better to include too much than miss player speech)

4. Player speech often starts with: "Yeah", "I mean", "Um", "Well", "So", "No", "Right"

Return JSON with LOCAL indices (0-based within this chunk):
{{"indices": [0, 1, 2, 4, 5, ...]}}

Include ALL segments where {player_name} is speaking."""

            user_prompt = f"""{context_text}Analyze these transcript segments from an interview with {player_name}:

{segments_text}

Identify ALL segments where {player_name} is speaking. Be INCLUSIVE - include all answers and statements, only exclude clear questions.

Return JSON with LOCAL indices (0-based within this chunk):
{{"indices": [0, 1, 2, ...]}}"""

            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.2,  # Slightly higher for better pattern recognition
                    response_format={"type": "json_object"}
                )
                
                content = response.choices[0].message.content
                
                # Parse JSON response
                indices = []
                try:
                    # Try to parse as JSON
                    result = json.loads(content)
                    if isinstance(result, dict):
                        indices = result.get("indices", result.get("segments", result.get("player_segments", [])))
                    elif isinstance(result, list):
                        indices = result
                except json.JSONDecodeError:
                    # Try to extract JSON object or array from text
                    import re
                    # Look for JSON object with indices
                    json_match = re.search(r'\{"indices"\s*:\s*\[[\d,\s]+\]\}', content)
                    if json_match:
                        try:
                            result = json.loads(json_match.group())
                            indices = result.get("indices", [])
                        except:
                            pass
                    
                    # Fallback: look for array
                    if not indices:
                        array_match = re.search(r'\[[\d,\s]+\]', content)
                        if array_match:
                            try:
                                indices = json.loads(array_match.group())
                            except:
                                pass
                    
                    if not indices:
                        logger.warning(f"Could not parse indices from response: {content[:200]}")
                        # Fallback to heuristics for this chunk
                        indices = []
                
                # Extract player segments using LOCAL indices
                for idx in indices:
                    if isinstance(idx, int) and 0 <= idx < len(chunk):
                        segment = chunk[idx].copy()
                        segment['original_index'] = chunk_offset + idx
                        # Avoid duplicates (from overlap)
                        if segment['original_index'] not in [s.get('original_index') for s in all_player_segments]:
                            all_player_segments.append(segment)
                
                logger.debug(f"Chunk {i//(chunk_size-overlap) + 1}: Identified {len(indices)} player segments from {len(chunk)} total")
                
            except Exception as e:
                logger.error(f"Error processing chunk {i//(chunk_size-overlap) + 1}: {e}")
                # Fallback: use heuristics for this chunk
                heuristic_segments = self._heuristic_player_segments(chunk, player_name)
                for seg in heuristic_segments:
                    seg['original_index'] = chunk_offset + chunk.index(seg)
                    if seg['original_index'] not in [s.get('original_index') for s in all_player_segments]:
                        all_player_segments.append(seg)
        
        return all_player_segments
    
    def _process_full_transcript(self, transcript_segments: List[Dict[str, Any]], 
                                player_name: str) -> List[Dict[str, Any]]:
        """
        Process full transcript at once for better context
        
        Args:
            transcript_segments: All transcript segments
            player_name: Name of the player
            
        Returns:
            List of player speech segments
        """
        # Format segments with indices and context
        segments_text = "\n".join([
            f"[{i}] {seg.get('text', '')}" 
            for i, seg in enumerate(transcript_segments)
        ])
        
        # Create example for few-shot learning
        example = """Example analysis:
[0] "Yeah, it's been exciting. Of course, um" → PLAYER (first-person, statement)
[1] "you always kind of uh had this uh this" → PLAYER (continuation of previous)
[2] "date mark on my calendar for a while." → PLAYER (personal experience)
[3] "Did you have many interviews?" → INTERVIEWER (question)
[4] "Uh no, I didn't have too many." → PLAYER (answer, first-person)
[5] "Yeah, I mean this is probably the biggest" → PLAYER (statement, first-person)
[6] "What is your impression?" → INTERVIEWER (question)
[7] "I think it's been great." → PLAYER (answer, first-person)"""
        
        system_prompt = f"""You are an expert at analyzing interview transcripts to identify when a specific person is speaking.

Your task: Identify which transcript segments are spoken by {player_name} (the hockey player being interviewed).

CRITICAL RULES - Be INCLUSIVE of player speech:
1. EXCLUDE only clear questions:
   - Questions ending with "?"
   - Questions starting with "Did you", "What do you", "How do you", "Why do you", "When did you", "Where did you"
   - Questions like "Are you...", "Have you...", "Will you..."
   - Interviewer statements like "Tell us about...", "Walk us through..."

2. INCLUDE all player speech:
   - First-person statements ("I", "we", "my", "me", "I'm", "I've", "I'll")
   - Answers to questions (even short ones like "Yeah", "No", "I think so", "Right")
   - Personal experiences, thoughts, feelings
   - Statements about their game, team, career, life
   - Continuation phrases ("you know", "um", "uh" - these are often part of player's speech)
   - Short responses ("Yeah", "No", "Right", "Exactly")
   - Any statement that sounds like a response to a question

3. When in doubt, INCLUDE the segment (better to include too much than miss player speech)

4. Player speech patterns:
   - Often starts with "Yeah", "I mean", "Um", "Well", "So"
   - Contains personal pronouns
   - Describes personal experiences
   - Answers questions (even if short)

{example}

Return a JSON object with this exact format:
{{"indices": [0, 1, 2, 4, 5, 7, ...]}}

Include ALL segment indices where {player_name} is speaking, even if the segment is short or contains filler words."""

        user_prompt = f"""Analyze this interview transcript with {player_name}. Be INCLUSIVE - include all player speech, only exclude clear questions.

{segments_text}

Identify ALL segments where {player_name} is speaking. Include:
- All answers to questions
- All statements
- Short responses ("Yeah", "No", etc.)
- Continuation phrases
- Only exclude clear interviewer questions

Return JSON:
{{"indices": [0, 1, 2, ...]}}"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.2,
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            result = json.loads(content)
            indices = result.get("indices", [])
            
            # Extract player segments
            player_segments = []
            for idx in indices:
                if isinstance(idx, int) and 0 <= idx < len(transcript_segments):
                    segment = transcript_segments[idx].copy()
                    segment['original_index'] = idx
                    player_segments.append(segment)
            
            return player_segments
            
        except Exception as e:
            logger.error(f"Error processing full transcript: {e}")
            # Fallback to heuristics
            return self._heuristic_player_segments(transcript_segments, player_name)
    
    def _post_process_segments(self, player_segments: List[Dict[str, Any]],
                               all_segments: List[Dict[str, Any]],
                               player_name: str) -> List[Dict[str, Any]]:
        """
        Post-process extracted segments to:
        1. Remove any remaining questions that slipped through
        2. Connect adjacent segments that are close in time
        3. Include nearby segments that might be part of the same response
        
        Args:
            player_segments: Segments identified as player speech
            all_segments: All transcript segments for context
            player_name: Name of the player
            
        Returns:
            Refined list of player speech segments
        """
        if not player_segments:
            return player_segments
        
        # Sort by original_index
        player_segments = sorted(player_segments, key=lambda s: s.get('original_index', 0))
        
        # Create a set of original indices for quick lookup
        player_indices = {seg.get('original_index') for seg in player_segments if 'original_index' in seg}
        
        refined_segments = []
        i = 0
        
        while i < len(player_segments):
            current_seg = player_segments[i]
            current_idx = current_seg.get('original_index', i)
            current_text = current_seg.get('text', '').strip().lower()
            
            # Skip if it's clearly a question (more comprehensive check)
            is_question = (
                current_text.endswith('?') or
                any(current_text.startswith(q) for q in [
                    'did you', 'what do you', 'how do you', 'why', 'when', 'where',
                    'are you', 'have you', 'will you', 'tell us', 'walk us',
                    'does this', 'does the', 'can you', 'could you', 'would you',
                    'do you feel', 'do you think', 'do you believe'
                ]) or
                'do you feel like' in current_text or
                'do you think' in current_text or
                'what is your' in current_text or
                'how do you feel' in current_text
            )
            
            if is_question:
                i += 1
                continue
            
            # Start a group with current segment
            group = [current_seg]
            group_start_idx = current_idx
            
            # Look ahead for adjacent segments (within 3 seconds or 3 segments)
            j = i + 1
            while j < len(player_segments):
                next_seg = player_segments[j]
                next_idx = next_seg.get('original_index', j)
                gap = next_idx - current_idx
                
                # If gap is small (adjacent or within 3 segments), include it
                if gap <= 3:
                    # Check if it's not a question
                    next_text = next_seg.get('text', '').strip().lower()
                    if not (next_text.endswith('?') or any(
                        next_text.startswith(q) for q in [
                            'did you', 'what do you', 'how do you', 'why', 'when', 'where',
                            'are you', 'have you', 'will you', 'tell us', 'walk us'
                        ]
                    )):
                        group.append(next_seg)
                        current_idx = next_idx
                        j += 1
                    else:
                        break
                else:
                    break
            
            # Also check for nearby segments in all_segments that might be part of response
            # Look at segments between group_start_idx and current_idx + 5 (expanded range)
            for check_idx in range(max(0, group_start_idx - 2), min(current_idx + 6, len(all_segments))):
                if check_idx not in player_indices:
                    check_seg = all_segments[check_idx]
                    check_text = check_seg.get('text', '').strip().lower()
                    
                    # Skip if it's clearly a question
                    is_question = (
                        check_text.endswith('?') or
                        any(check_text.startswith(q) for q in [
                            'did you', 'what do you', 'how do you', 'why', 'when', 'where',
                            'are you', 'have you', 'will you', 'tell us', 'walk us',
                            'does this', 'does the', 'can you', 'could you', 'would you',
                            'do you feel', 'do you think', 'do you believe'
                        ])
                    )
                    
                    if is_question:
                        continue
                    
                    # Include if it's a short response, continuation, or has player indicators
                    is_short_response = check_text in ['yeah', 'yes', 'no', 'right', 'exactly', 'sure', 'okay', 'ok', 'um', 'uh', 'well', 'so']
                    has_first_person = any(word in check_text for word in [
                        'i ', "i'", 'i\'m', 'i\'ve', 'i\'ll', 'i\'d', 'my ', 'we ', 'we\'re', 'me ',
                        'i think', 'i feel', 'i mean', 'i was', 'i am'
                    ])
                    is_continuation = any(phrase in check_text for phrase in ['you know', 'um', 'uh', 'well', 'so'])
                    has_personal = any(word in check_text for word in [
                        'think', 'feel', 'believe', 'experience', 'remember', 'my team', 'my game', 'my career'
                    ])
                    
                    # Include if any indicator matches (be generous)
                    if is_short_response or has_first_person or (is_continuation and len(check_text.split()) > 1) or has_personal:
                        check_seg['original_index'] = check_idx
                        group.append(check_seg)
                        player_indices.add(check_idx)
            
            # Add all segments in group
            refined_segments.extend(group)
            i = j if j > i + 1 else i + 1
        
        # Sort again by original_index
        refined_segments = sorted(refined_segments, key=lambda s: s.get('original_index', 0))
        
        logger.info(f"Post-processing: {len(player_segments)} -> {len(refined_segments)} segments")
        
        return refined_segments
    
    def _heuristic_player_segments(self, segments: List[Dict[str, Any]], 
                                   player_name: str) -> List[Dict[str, Any]]:
        """
        Fallback heuristic method to identify player segments
        Used when GPT fails - More inclusive approach
        """
        player_segments = []
        
        for seg in segments:
            text = seg.get('text', '').strip().lower()
            
            # Skip empty segments
            if not text:
                continue
            
            # EXCLUDE: Clear questions
            is_question = (
                text.endswith('?') or
                text.startswith('did you') or
                text.startswith('what do you') or
                text.startswith('how do you') or
                text.startswith('why do you') or
                text.startswith('when did you') or
                text.startswith('where did you') or
                text.startswith('are you') or
                text.startswith('have you') or
                text.startswith('will you') or
                'tell us about' in text or
                'walk us through' in text
            )
            
            if is_question:
                continue
            
            # INCLUDE: Player speech indicators (be generous)
            first_person = any(word in text for word in [
                'i ', "i'", 'i\'m', 'i\'ve', 'i\'ll', 'i\'d', 'my ', 'we ', 'we\'re', 'me ', 
                'myself', 'i think', 'i feel', 'i believe', 'i mean'
            ])
            
            # Short responses that are likely player
            short_response = text in ['yeah', 'yes', 'no', 'right', 'exactly', 'sure', 'okay', 'ok']
            
            # Continuation phrases (often part of player speech)
            continuation = any(phrase in text for phrase in ['you know', 'um', 'uh', 'well', 'so'])
            
            # Personal experience indicators
            personal = any(word in text for word in [
                'think', 'feel', 'believe', 'experience', 'remember', 'think about',
                'my team', 'my game', 'my career', 'i was', 'i am'
            ])
            
            # Include if any indicator matches (be inclusive)
            if first_person or short_response or (continuation and len(text.split()) > 2) or personal:
                player_segments.append(seg)
        
        return player_segments

