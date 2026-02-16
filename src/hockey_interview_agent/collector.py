"""
collector.py

HockeyInterviewCollector

Main orchestration engine of the project.

Responsibilities
---------------
1. Discover relevant YouTube interviews for a player.
2. Extract transcripts from selected videos.
3. Extract player-only speech using GPT.
4. Save raw collection results to disk.

Design Philosophy
-----------------
- This module handles data collection only.
- It does NOT handle dataset exporting or transformation.
- Export logic is intentionally separated for maintainability.

Outputs
-------
Raw JSON saved to:
    data/raw/{Player}_{Timestamp}.json

Transcript JSON saved to:
    data/raw/transcript/

Player speech JSON saved to:
    data/raw/player_speech/
"""

from pathlib import Path
from datetime import datetime
import json

from hockey_interview_agent.youtube.youtube_interview_finder import YouTubeInterviewFinder
from hockey_interview_agent.youtube.youtube_transcript_extractor import YouTubeTranscriptExtractor
from hockey_interview_agent.llm.player_speech_extractor import PlayerSpeechExtractor


class HockeyInterviewCollector:
    """
    Orchestrates interview collection pipeline for a single player.
    """

    def __init__(
        self,
        use_youtube: bool = True,
        extract_transcripts: bool = True,
        extract_player_speech: bool = True,
        use_proxy: bool = True,
    ):
        self.use_youtube = use_youtube
        self.extract_transcripts = extract_transcripts
        self.extract_player_speech = extract_player_speech
        self.use_proxy = use_proxy

        if self.use_youtube:
            self.youtube_finder = YouTubeInterviewFinder()

        if self.extract_transcripts:
            self.transcript_extractor = YouTubeTranscriptExtractor(use_proxy=use_proxy)

        if self.extract_player_speech:
            self.speech_extractor = PlayerSpeechExtractor()

        Path("data/raw").mkdir(parents=True, exist_ok=True)

    def collect_interviews(self, player_name: str, youtube_top_n: int = 5) -> dict:
        """
        Collect interviews for a given player.

        Parameters
        ----------
        player_name : str
            Full name of the player.
        youtube_top_n : int
            Number of top YouTube interviews to collect.

        Returns
        -------
        dict
            Structured raw collection result.
        """

        results = {
            "player_name": player_name,
            "collection_date": datetime.now().isoformat(),
            "interviews": [],
        }

        if self.use_youtube:
            videos = self.youtube_finder.find_top_interviews(
                player_name,
                top_n=youtube_top_n,
            )

            for video in videos:
                interview_data = {
                    "source": "YouTube",
                    "title": video["title"],
                    "video_id": video["videoId"],
                    "video_url": video["url"],
                }

                if self.extract_transcripts:
                    transcript = self.transcript_extractor.extract_transcript(
                        video_id=video["videoId"],
                        video_title=video["title"],
                        video_url=video["url"],
                        output_dir=Path("data/raw/transcript"),
                    )

                    if transcript:
                        interview_data["word_count"] = transcript["word_count"]

                        if self.extract_player_speech:
                            speech = self.speech_extractor.extract_player_speech(
                                transcript_json=transcript,
                                player_name=player_name,
                                output_dir=Path("data/raw/player_speech"),
                            )

                            if speech:
                                interview_data["player_speech_word_count"] = speech["word_count"]

                results["interviews"].append(interview_data)

        return results

    def save_results(self, results: dict) -> Path:
        """
        Save raw collection results to disk.

        Returns
        -------
        Path
            Location of saved JSON file.
        """

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{results['player_name'].replace(' ', '_')}_{timestamp}.json"
        path = Path("data/raw") / filename

        with open(path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        return path
